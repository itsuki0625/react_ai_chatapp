#!/bin/bash

# ECS Fargate環境用権限マイグレーションスクリプト
# AWS ECS RunTaskを使用してマイグレーションを実行

set -e  # エラー時に停止

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用方法表示
usage() {
    cat << EOF
ECS Fargate環境用権限マイグレーションツール

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    check         環境チェック（ECSタスクとして実行）
    backup        現在の権限設定をバックアップ
    dry-run       ドライラン実行
    migrate       実際のマイグレーション実行
    logs          マイグレーションログの確認

Options:
    --environment ENV    環境指定 (stg|prod) デフォルト: stg
    --version VERSION    適用するバージョン (例: v1.1.0)
    --aws-region REGION  AWSリージョン (デフォルト: ap-northeast-1)
    --cluster CLUSTER    ECSクラスター名 (自動検出)
    --subnet SUBNET      サブネットID (自動検出)
    --security-group SG  セキュリティグループID (自動検出)
    --timeout SECONDS    タスク実行タイムアウト (デフォルト: 1800)
    --wait               タスク完了まで待機
    --verbose            詳細ログ

Examples:
    # STG環境でドライラン実行
    $0 dry-run --environment stg --version v1.1.0 --wait

    # 本番環境でマイグレーション実行
    $0 migrate --environment prod --version v1.1.0 --wait

    # ログ確認
    $0 logs --environment stg
EOF
}

# AWS CLI設定確認
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI がインストールされていません"
        return 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません"
        return 1
    fi
    
    log_success "AWS CLI設定確認完了"
}

# ECS環境情報取得
get_ecs_config() {
    local env=$1
    local region=$2
    
    log_info "ECS環境情報を取得中..."
    
    # クラスター名取得
    CLUSTER_NAME=$(aws ecs list-clusters --region $region --query "clusterArns[?contains(@, '$env-api')]" --output text | head -1 | awk -F'/' '{print $2}')
    if [[ -z "$CLUSTER_NAME" ]]; then
        log_error "ECSクラスターが見つかりません: $env-api"
        return 1
    fi
    
    # タスク定義ARN取得
    TASK_DEFINITION=$(aws ecs describe-task-definition --region $region --task-definition "$env-migration-task" --query "taskDefinition.taskDefinitionArn" --output text 2>/dev/null)
    if [[ -z "$TASK_DEFINITION" || "$TASK_DEFINITION" == "None" ]]; then
        log_error "マイグレーション用タスク定義が見つかりません: $env-migration-task"
        log_info "Terraformでマイグレーション機能をデプロイしてください"
        return 1
    fi
    
    # VPC設定取得
    VPC_ID=$(aws ec2 describe-vpcs --region $region --filters "Name=tag:Name,Values=$env-vpc" --query "Vpcs[0].VpcId" --output text)
    if [[ -z "$VPC_ID" || "$VPC_ID" == "None" ]]; then
        log_error "VPCが見つかりません: $env-vpc"
        return 1
    fi
    
    # プライベートサブネット取得
    SUBNETS=$(aws ec2 describe-subnets --region $region --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*private*" --query "Subnets[].SubnetId" --output text)
    if [[ -z "$SUBNETS" ]]; then
        log_error "プライベートサブネットが見つかりません"
        return 1
    fi
    SUBNET_ID=$(echo $SUBNETS | awk '{print $1}')  # 最初のサブネットを使用
    
    # セキュリティグループ取得
    SECURITY_GROUP=$(aws ec2 describe-security-groups --region $region --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=$env-app-sg" --query "SecurityGroups[0].GroupId" --output text)
    if [[ -z "$SECURITY_GROUP" || "$SECURITY_GROUP" == "None" ]]; then
        log_error "セキュリティグループが見つかりません: $env-app-sg"
        return 1
    fi
    
    log_success "ECS環境情報取得完了"
    log_info "クラスター: $CLUSTER_NAME"
    log_info "タスク定義: $TASK_DEFINITION"
    log_info "サブネット: $SUBNET_ID"
    log_info "セキュリティグループ: $SECURITY_GROUP"
}

# ECSタスク実行
run_ecs_task() {
    local env=$1
    local region=$2
    local command=$3
    local wait_for_completion=$4
    local timeout=$5
    
    log_info "ECSタスクを実行中..."
    log_info "コマンド: $command"
    
    # タスク実行
    TASK_ARN=$(aws ecs run-task \
        --region $region \
        --cluster $CLUSTER_NAME \
        --task-definition $TASK_DEFINITION \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --overrides "{
            \"containerOverrides\": [{
                \"name\": \"migration\",
                \"command\": [\"sh\", \"-c\", \"$command\"]
            }]
        }" \
        --query "tasks[0].taskArn" \
        --output text)
    
    if [[ -z "$TASK_ARN" || "$TASK_ARN" == "None" ]]; then
        log_error "ECSタスクの起動に失敗しました"
        return 1
    fi
    
    log_success "ECSタスクが起動しました: $TASK_ARN"
    
    if [[ "$wait_for_completion" == "true" ]]; then
        log_info "タスクの完了を待機しています（タイムアウト: ${timeout}秒）..."
        
        if aws ecs wait tasks-stopped --region $region --cluster $CLUSTER_NAME --tasks $TASK_ARN --cli-read-timeout $timeout --cli-connect-timeout 60; then
            # タスクの最終状態確認
            EXIT_CODE=$(aws ecs describe-tasks --region $region --cluster $CLUSTER_NAME --tasks $TASK_ARN --query "tasks[0].containers[0].exitCode" --output text)
            
            if [[ "$EXIT_CODE" == "0" ]]; then
                log_success "マイグレーションタスクが正常に完了しました"
            else
                log_error "マイグレーションタスクがエラーで終了しました (終了コード: $EXIT_CODE)"
                return 1
            fi
        else
            log_error "タスクがタイムアウトしました"
            return 1
        fi
    else
        log_info "タスクをバックグラウンドで実行中です"
        log_info "ログを確認するには: $0 logs --environment $env"
    fi
    
    return 0
}

# ログ表示
show_logs() {
    local env=$1
    local region=$2
    
    log_info "マイグレーションログを表示中..."
    
    LOG_GROUP="/ecs/$env-migration"
    
    # 最新のログストリームを取得
    LOG_STREAM=$(aws logs describe-log-streams --region $region --log-group-name $LOG_GROUP --order-by LastEventTime --descending --max-items 1 --query "logStreams[0].logStreamName" --output text 2>/dev/null)
    
    if [[ -z "$LOG_STREAM" || "$LOG_STREAM" == "None" ]]; then
        log_warning "ログストリームが見つかりません"
        return 1
    fi
    
    log_info "ログストリーム: $LOG_STREAM"
    
    # ログ表示
    aws logs get-log-events --region $region --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM --query "events[].[timestamp,message]" --output text | sort -n | while IFS=$'\t' read -r timestamp message; do
        # タイムスタンプを人間が読める形式に変換
        readable_time=$(date -d @$((timestamp/1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $((timestamp/1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
        echo "[$readable_time] $message"
    done
}

# メイン処理
main() {
    # デフォルト値
    local command=""
    local environment="stg"
    local version=""
    local aws_region="ap-northeast-1"
    local wait_for_completion="false"
    local timeout="1800"
    local verbose="false"
    
    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            check|backup|dry-run|migrate|logs)
                command=$1
                shift
                ;;
            --environment)
                environment=$2
                shift 2
                ;;
            --version)
                version=$2
                shift 2
                ;;
            --aws-region)
                aws_region=$2
                shift 2
                ;;
            --timeout)
                timeout=$2
                shift 2
                ;;
            --wait)
                wait_for_completion="true"
                shift
                ;;
            --verbose)
                verbose="true"
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "未知のオプション: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # 必須チェック
    if [[ -z "$command" ]]; then
        log_error "コマンドが指定されていません"
        usage
        exit 1
    fi
    
    # AWS CLI確認
    if ! check_aws_cli; then
        exit 1
    fi
    
    # ログ表示の場合は特別処理
    if [[ "$command" == "logs" ]]; then
        show_logs $environment $aws_region
        exit $?
    fi
    
    # ECS設定取得
    if ! get_ecs_config $environment $aws_region; then
        exit 1
    fi
    
    # コマンド別実行
    case $command in
        check)
            migration_command="python scripts/migrate_permissions.py --check-env"
            [[ "$verbose" == "true" ]] && migration_command="$migration_command --verbose"
            ;;
        backup)
            migration_command="python scripts/migrate_permissions.py --backup"
            [[ "$verbose" == "true" ]] && migration_command="$migration_command --verbose"
            ;;
        dry-run)
            migration_command="python scripts/migrate_permissions.py --dry-run"
            [[ -n "$version" ]] && migration_command="$migration_command --version $version"
            [[ "$verbose" == "true" ]] && migration_command="$migration_command --verbose"
            ;;
        migrate)
            if [[ "$environment" == "prod" ]]; then
                log_warning "⚠️  本番環境でのマイグレーションを実行します"
                echo -n "続行しますか? (yes/no): "
                read confirm
                [[ "$confirm" != "yes" ]] && { log_info "処理をキャンセルしました"; exit 0; }
            fi
            
            migration_command="python scripts/migrate_permissions.py"
            [[ -n "$version" ]] && migration_command="$migration_command --version $version"
            [[ "$verbose" == "true" ]] && migration_command="$migration_command --verbose"
            ;;
        *)
            log_error "サポートされていないコマンド: $command"
            exit 1
            ;;
    esac
    
    # ECSタスク実行
    if run_ecs_task $environment $aws_region "$migration_command" $wait_for_completion $timeout; then
        log_success "処理が完了しました"
        
        if [[ "$wait_for_completion" == "false" ]]; then
            log_info "タスクの進行状況を確認するには:"
            log_info "$0 logs --environment $environment"
        fi
    else
        log_error "処理に失敗しました"
        exit 1
    fi
}

# スクリプト実行
main "$@"
