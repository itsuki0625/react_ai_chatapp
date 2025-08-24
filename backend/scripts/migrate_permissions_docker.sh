#!/bin/bash

# 本番環境用権限マイグレーションスクリプト (Docker対応)
# Usage: ./migrate_permissions_docker.sh [COMMAND] [OPTIONS]

set -e  # エラー時に停止

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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
本番環境用権限マイグレーションツール

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    check         環境チェック
    backup        現在の権限設定をバックアップ
    dry-run       ドライラン実行 (安全確認)
    migrate       実際のマイグレーション実行
    interactive   インタラクティブモード
    rollback      ロールバック (バックアップから復元)

Options:
    --version VERSION    適用するバージョン (例: v1.1.0)
    --environment ENV    環境指定 (stg|prod) デフォルト: stg
    --backup-file FILE   ロールバック時のバックアップファイル
    --verbose           詳細ログ
    --help              このヘルプを表示

Examples:
    # 環境チェック
    $0 check --environment stg

    # ドライラン実行
    $0 dry-run --version v1.1.0 --environment prod

    # 実際のマイグレーション (STG環境)
    $0 migrate --version v1.1.0 --environment stg

    # インタラクティブモード
    $0 interactive --environment prod

    # ロールバック
    $0 rollback --backup-file permission_backup_20240124_120000.json
EOF
}

# Docker Compose プロジェクト名取得
get_docker_compose_project() {
    local env=$1
    case $env in
        stg)
            echo "react-ai-chatapp-stg"
            ;;
        prod)
            echo "react-ai-chatapp-prod"
            ;;
        *)
            echo "react-ai-chatapp"
            ;;
    esac
}

# Docker コンテナが実行中か確認
check_docker_container() {
    local env=$1
    local project=$(get_docker_compose_project $env)
    
    log_info "Docker コンテナ状態確認中..."
    
    if ! docker-compose -p $project ps backend | grep -q "Up"; then
        log_error "バックエンドコンテナが実行されていません"
        log_info "以下のコマンドでコンテナを起動してください:"
        log_info "docker-compose -p $project up -d backend"
        return 1
    fi
    
    log_success "Docker コンテナ確認完了"
    return 0
}

# Docker内でPythonスクリプト実行
execute_in_docker() {
    local env=$1
    local command=$2
    local project=$(get_docker_compose_project $env)
    
    log_info "Docker内でコマンド実行: $command"
    docker-compose -p $project exec -T backend python $command
}

# 環境チェック実行
run_check() {
    local env=$1
    
    log_info "🔍 環境チェック実行中 ($env)..."
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    execute_in_docker $env "scripts/migrate_permissions.py --check-env"
}

# バックアップ実行
run_backup() {
    local env=$1
    
    log_info "💾 権限設定バックアップ実行中 ($env)..."
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    execute_in_docker $env "scripts/migrate_permissions.py --backup"
    
    # バックアップファイルをホストにコピー
    local project=$(get_docker_compose_project $env)
    local container_id=$(docker-compose -p $project ps -q backend)
    local backup_files=$(docker exec $container_id find /app -name "permission_backup_*.json" -type f -printf "%f\n" | sort -r | head -1)
    
    if [[ -n "$backup_files" ]]; then
        docker cp "$container_id:/app/$backup_files" "./backups/"
        log_success "バックアップファイルをホストにコピー: ./backups/$backup_files"
    fi
}

# ドライラン実行
run_dry_run() {
    local env=$1
    local version=$2
    local verbose=$3
    
    log_info "🧪 ドライラン実行中 ($env, version: ${version:-latest})..."
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    local cmd="scripts/migrate_permissions.py --dry-run"
    [[ -n "$version" ]] && cmd="$cmd --version $version"
    [[ "$verbose" == "true" ]] && cmd="$cmd --verbose"
    
    execute_in_docker $env "$cmd"
}

# 実際のマイグレーション実行
run_migrate() {
    local env=$1
    local version=$2
    local verbose=$3
    
    log_warning "⚠️  実際のマイグレーションを実行します ($env)"
    log_warning "この操作はデータベースを変更します"
    
    if [[ "$env" == "prod" ]]; then
        log_error "本番環境への適用は慎重に行ってください"
        echo -n "本番環境のマイグレーションを実行しますか? (yes/no): "
        read confirm
        [[ "$confirm" != "yes" ]] && { log_info "処理をキャンセルしました"; return 0; }
    fi
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    # 事前にバックアップを作成
    log_info "📦 事前バックアップ作成中..."
    run_backup $env
    
    local cmd="scripts/migrate_permissions.py"
    [[ -n "$version" ]] && cmd="$cmd --version $version"
    [[ "$verbose" == "true" ]] && cmd="$cmd --verbose"
    
    execute_in_docker $env "$cmd"
}

# インタラクティブモード実行
run_interactive() {
    local env=$1
    
    log_info "🎯 インタラクティブモード開始 ($env)..."
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    local project=$(get_docker_compose_project $env)
    docker-compose -p $project exec backend python scripts/migrate_permissions.py --interactive
}

# ロールバック実行
run_rollback() {
    local env=$1
    local backup_file=$2
    
    if [[ -z "$backup_file" ]]; then
        log_error "バックアップファイルが指定されていません"
        return 1
    fi
    
    if [[ ! -f "./backups/$backup_file" ]]; then
        log_error "バックアップファイルが見つかりません: ./backups/$backup_file"
        return 1
    fi
    
    log_warning "⚠️  ロールバックを実行します ($env)"
    log_warning "バックアップファイル: $backup_file"
    
    echo -n "ロールバックを実行しますか? (yes/no): "
    read confirm
    [[ "$confirm" != "yes" ]] && { log_info "処理をキャンセルしました"; return 0; }
    
    if ! check_docker_container $env; then
        return 1
    fi
    
    local project=$(get_docker_compose_project $env)
    local container_id=$(docker-compose -p $project ps -q backend)
    
    # バックアップファイルをコンテナにコピー
    docker cp "./backups/$backup_file" "$container_id:/app/$backup_file"
    
    # ロールバック実行 (別途実装が必要)
    execute_in_docker $env "scripts/rollback_permissions.py --backup-file $backup_file"
}

# メイン処理
main() {
    # デフォルト値
    local command=""
    local environment="stg"
    local version=""
    local backup_file=""
    local verbose="false"
    
    # コマンドライン引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            check|backup|dry-run|migrate|interactive|rollback)
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
            --backup-file)
                backup_file=$2
                shift 2
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
    
    # コマンド必須チェック
    if [[ -z "$command" ]]; then
        log_error "コマンドが指定されていません"
        usage
        exit 1
    fi
    
    # バックアップディレクトリ作成
    mkdir -p "./backups"
    
    # コマンド実行
    case $command in
        check)
            run_check $environment
            ;;
        backup)
            run_backup $environment
            ;;
        dry-run)
            run_dry_run $environment "$version" "$verbose"
            ;;
        migrate)
            run_migrate $environment "$version" "$verbose"
            ;;
        interactive)
            run_interactive $environment
            ;;
        rollback)
            run_rollback $environment "$backup_file"
            ;;
        *)
            log_error "サポートされていないコマンド: $command"
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"
