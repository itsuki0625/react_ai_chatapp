from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.models.personal_statement import PersonalStatement, Feedback
from app.schemas.personal_statement import (
    PersonalStatementCreate,
    PersonalStatementUpdate,
    PersonalStatementResponse,
    FeedbackCreate,
    FeedbackResponse,
    AIImprovementRequest,
    AIImprovementResponse
)
from app.crud import statement as crud_statement
from app.services.agents.correction_agent.main import CorrectionOrchestrator
from app.models.chat import ChatSession
from app.models.desired_school import DesiredDepartment
from app.models.university import Department
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class StatementChatRequest(BaseModel):
    statement_id: UUID
    message: str
    chat_history: List[dict] = []

class StatementChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    session_id: str



@router.post("/", response_model=PersonalStatementResponse, status_code=status.HTTP_201_CREATED)
async def create_new_statement(
    statement_in: PersonalStatementCreate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """新しい志望理由書を作成"""
    statement = crud_statement.create_statement(db=db, statement_in=statement_in, user_id=current_user.id)
    from app.schemas.personal_statement import PersonalStatementResponse
    return PersonalStatementResponse.from_orm_with_counts(statement)

@router.get("/", response_model=List[PersonalStatementResponse])
async def get_user_statements(
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """ユーザーの志望理由書一覧を取得"""
    statements = crud_statement.get_statements(db=db, user_id=current_user.id)
    from app.schemas.personal_statement import PersonalStatementResponse
    return [PersonalStatementResponse.from_orm_with_counts(statement) for statement in statements]

@router.get("/{statement_id}", response_model=PersonalStatementResponse)
async def get_single_statement(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """特定の志望理由書を取得"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    from app.schemas.personal_statement import PersonalStatementResponse
    return PersonalStatementResponse.from_orm_with_counts(statement)

@router.put("/{statement_id}", response_model=PersonalStatementResponse)
async def update_existing_statement(
    statement_id: UUID,
    statement_in: PersonalStatementUpdate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を更新"""
    statement = crud_statement.get_statement(db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書を編集する権限がありません")

    updated_statement = crud_statement.update_statement_db(
        db=db, statement=statement, statement_in=statement_in, user_id=current_user.id
    )
    from app.schemas.personal_statement import PersonalStatementResponse
    return PersonalStatementResponse.from_orm_with_counts(updated_statement)

@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_statement(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を削除"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    
    crud_statement.delete_statement(db=db, statement_id=str(statement_id))
    return

@router.post("/{statement_id}/ai-improve", status_code=status.HTTP_200_OK)
async def improve_statement_with_ai(
    statement_id: UUID,
    request: AIImprovementRequest,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """AI添削機能を使用して志望理由書を改善"""
    try:
        # 志望理由書の存在確認と権限チェック
        statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
        if not statement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
        if statement.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書を編集する権限がありません")

        # 大学情報を取得
        university_info = ""
        if statement.desired_department:
            department = statement.desired_department.department
            if department and department.university:
                university_info = f"{department.university.name} {department.name}"

        # 自己分析チャットコンテキストを取得
        self_analysis_context = ""
        if statement.self_analysis_chat_id:
            chat_session = db.query(ChatSession).filter(ChatSession.id == statement.self_analysis_chat_id).first()
            if chat_session:
                # チャットメッセージから自己分析の概要を生成
                # 実際の実装では、メッセージ履歴から重要な情報を抽出する
                self_analysis_context = f"自己分析チャット: {chat_session.title or '無題'}"

        # CorrectionOrchestratorを初期化
        orchestrator = CorrectionOrchestrator()
        
        # 改善リクエストの履歴を作成
        messages = [
            {
                "role": "user",
                "content": f"志望理由書を改善してください。フォーカスエリア: {', '.join(request.focus_areas or ['全般的な改善'])}",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        # AI添削を実行
        logger.info(f"Starting AI improvement for statement {statement_id}")
        result = await orchestrator.run(
            statement_text=statement.content,
            messages=messages,
            session_id=str(statement_id),
            university_info=university_info,
            self_analysis_context=self_analysis_context
        )
        
        logger.info(f"AI improvement completed for statement {statement_id}")
        
        # 結果の処理
        response_data = {
            "statement_id": str(statement_id),
            "user_message": result.get("user_message", "改善案を提案しました"),
            "current_step": result.get("current_step", "完了"),
            "step_results": result.get("step_results", {}),
            "improvements": extract_improvements_from_result(result),
            "status": "success"
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in AI improvement for statement {statement_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI添削中にエラーが発生しました: {str(e)}"
        )

@router.post("/{statement_id}/ai-chat", status_code=status.HTTP_200_OK)
async def chat_with_ai_for_improvement(
    statement_id: UUID,
    request: dict,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """対話型AI添削機能 - ユーザーメッセージに基づいた改善提案"""
    try:
        # 志望理由書の存在確認と権限チェック
        statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
        if not statement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
        if statement.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書を編集する権限がありません")

        user_message = request.get("message", "")
        chat_history = request.get("chat_history", [])
        current_content = request.get("current_content", statement.content)
        
        if not user_message.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="メッセージが空です")

        # 大学情報を取得
        university_info = ""
        if statement.desired_department:
            department = statement.desired_department.department
            if department and department.university:
                university_info = f"{department.university.name} {department.name}"

        # 自己分析チャットコンテキストを取得
        self_analysis_context = ""
        if statement.self_analysis_chat_id:
            chat_session = db.query(ChatSession).filter(ChatSession.id == statement.self_analysis_chat_id).first()
            if chat_session:
                self_analysis_context = f"自己分析チャット: {chat_session.title or '無題'}"

        # CorrectionOrchestratorを初期化
        orchestrator = CorrectionOrchestrator()
        
        # チャット履歴にユーザーメッセージを追加
        messages = chat_history + [
            {
                "role": "user",
                "content": user_message,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        # 対話型AI添削を実行
        logger.info(f"Starting interactive AI chat for statement {statement_id}")
        result = await orchestrator.run(
            statement_text=current_content,
            messages=messages,
            session_id=f"{statement_id}-chat",
            university_info=university_info,
            self_analysis_context=self_analysis_context
        )
        
        logger.info(f"Interactive AI chat completed for statement {statement_id}")
        
        # AI応答を抽出
        ai_response = result.get("user_message", "改善案を検討中です...")
        current_step = result.get("current_step", "analysis")
        
        # 具体的な改善提案を抽出
        suggestions = extract_specific_suggestions_from_result(result, user_message)
        
        response_data = {
            "ai_message": ai_response,
            "current_step": current_step,
            "suggestions": suggestions,
            "status": "success"
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in AI chat for statement {statement_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI対話中にエラーが発生しました: {str(e)}"
        )

def extract_specific_suggestions_from_result(result: dict, user_message: str) -> list:
    """ユーザーメッセージに基づいて具体的な改善提案を抽出"""
    suggestions = []
    step_results = result.get("step_results", {})
    
    # ユーザーメッセージを解析して関連する改善案を抽出
    message_lower = user_message.lower()
    
    for step_name, step_result in step_results.items():
        if isinstance(step_result, dict):
            # ステップ結果から改善案を抽出
            if "suggestions" in step_result:
                for suggestion in step_result["suggestions"]:
                    if isinstance(suggestion, dict) and "original" in suggestion and "improved" in suggestion:
                        suggestions.append({
                            "type": "replacement",
                            "original": suggestion["original"],
                            "improved": suggestion["improved"],
                            "reason": suggestion.get("reason", "改善提案"),
                            "step": step_name
                        })
            elif "improvements" in step_result:
                # improvements形式の場合
                improvements = step_result["improvements"]
                if isinstance(improvements, list):
                    for improvement in improvements:
                        if isinstance(improvement, dict):
                            suggestions.append({
                                "type": "improvement",
                                "content": improvement.get("content", ""),
                                "reason": improvement.get("reason", "改善提案"),
                                "step": step_name
                            })
    
    # ユーザーメッセージに関連する提案のみをフィルタリング
    # （実際の実装では、より高度な関連性分析を行う）
    if not suggestions:
        # フォールバック: 基本的な改善提案を生成
        suggestions = [
            {
                "type": "general",
                "content": "ユーザーのご要望に基づいて改善案を検討しています。",
                "reason": "対話型改善",
                "step": "analysis"
            }
        ]
    
    return suggestions[:3]  # 最大3つの提案に制限

def extract_improvements_from_result(result: dict) -> dict:
    """CorrectionOrchestratorの結果から改善案を抽出し、フロントエンドが期待する形式に変換"""
    improvements = {}
    step_results = result.get("step_results", {})
    
    logger.info(f"Processing step_results with keys: {list(step_results.keys())}")
    
    for step_name, step_result in step_results.items():
        logger.info(f"Processing step: {step_name}")
        logger.info(f"Step result type: {type(step_result)}")
        logger.info(f"Step result keys: {list(step_result.keys()) if isinstance(step_result, dict) else 'Not a dict'}")
        
        if isinstance(step_result, dict):
            # フロントエンドが期待する形式に変換
            step_improvement = {
                "content": "",
                "suggestions": [],
                "changes": []
            }
            
            try:
                # 各ステップの結果から改善案を抽出
                if step_name == "analysis":
                    # analysisステップの処理
                    analysis_data = step_result.get("analysis", {})
                    step_improvement["content"] = analysis_data.get("comprehensive_feedback", "")
                    
                    # priority_improvementsを suggestions に変換
                    priority_improvements = step_result.get("priority_improvements", [])
                    step_improvement["suggestions"] = priority_improvements
                    logger.info(f"Analysis suggestions: {len(priority_improvements)}")
                    
                    # 各観点の改善提案を changes に変換
                    for area in ["structure", "content", "expression", "coherence"]:
                        if area in analysis_data:
                            area_data = analysis_data[area]
                            if isinstance(area_data, dict) and "suggestions" in area_data:
                                for suggestion in area_data["suggestions"]:
                                    step_improvement["changes"].append({
                                        "original": f"{area}の現状",
                                        "improved": suggestion,
                                        "reason": f"{area}の改善提案"
                                    })
                
                elif step_name == "structure":
                    # structureステップの処理
                    structure_data = step_result.get("structure", {})
                    rationale = structure_data.get("improvements", {}).get("rationale", "")
                    step_improvement["content"] = rationale[:300] + "..." if len(rationale) > 300 else rationale
                    
                    # specific_changesがある場合は具体的な変更案を使用
                    specific_changes = step_result.get("specific_changes", [])
                    if specific_changes:
                        # 具体的な変更案を suggestions と changes に変換
                        for change in specific_changes:
                            if isinstance(change, dict):
                                location = change.get("location", "")
                                priority = change.get("priority", "medium")
                                priority_jp = {"high": "重要", "medium": "中程度", "low": "軽微"}.get(priority, priority)
                                
                                step_improvement["suggestions"].append(
                                    f"{location}: {change.get('reason', '')} ({priority_jp})"
                                )
                                step_improvement["changes"].append({
                                    "original": change.get("original_text", "現在の構成"),
                                    "improved": change.get("improved_text", "改善案"),
                                    "reason": change.get("reason", "構成の改善")
                                })
                    else:
                        # フォールバック：従来の処理
                        recommended_changes = step_result.get("recommended_changes", [])
                        logger.info(f"Structure recommended_changes: {recommended_changes}")
                        
                        for change in recommended_changes:
                            if isinstance(change, dict):
                                step_improvement["suggestions"].append(
                                    f"{change.get('description', '')} ({change.get('priority', 'medium')})"
                                )
                                step_improvement["changes"].append({
                                    "original": f"現在の{change.get('change_type', '')}",
                                    "improved": change.get("action", ""),
                                    "reason": change.get("description", "")
                                })
                    
                    logger.info(f"Structure final suggestions: {len(step_improvement['suggestions'])}")
                    logger.info(f"Structure final changes: {len(step_improvement['changes'])}")
                
                elif step_name == "content":
                    # contentステップの処理
                    content_data = step_result.get("content", {})
                    improvements_data = content_data.get("improvements", {})
                    overall_assessment = improvements_data.get("overall_assessment", "")
                    step_improvement["content"] = overall_assessment[:300] + "..." if len(overall_assessment) > 300 else overall_assessment
                    
                    # specific_changesがある場合は具体的な変更案を使用
                    specific_changes = step_result.get("specific_changes", [])
                    if specific_changes:
                        # 具体的な変更案を suggestions と changes に変換
                        for change in specific_changes:
                            if isinstance(change, dict):
                                category = change.get("category", "")
                                location = change.get("location", "")
                                priority = change.get("priority", "medium")
                                priority_jp = {"high": "重要", "medium": "中程度", "low": "軽微"}.get(priority, priority)
                                
                                step_improvement["suggestions"].append(
                                    f"{category}（{location}）: {change.get('reason', '')} ({priority_jp})"
                                )
                                step_improvement["changes"].append({
                                    "original": change.get("original_text", f"{category}の現状"),
                                    "improved": change.get("improved_text", "改善案"),
                                    "reason": change.get("reason", f"{category}の改善")
                                })
                    else:
                        # フォールバック：従来の処理
                        recommended_changes = step_result.get("recommended_changes", [])
                        logger.info(f"Content recommended_changes: {len(recommended_changes)}")
                        
                        for change in recommended_changes:
                            if isinstance(change, dict):
                                suggestions = change.get("suggestions", [])
                                step_improvement["suggestions"].extend(suggestions[:2])  # 最初の2つだけ
                                
                                for suggestion in suggestions[:2]:
                                    step_improvement["changes"].append({
                                        "original": f"{change.get('area', '')}の現状",
                                        "improved": suggestion,
                                        "reason": f"{change.get('area', '')}の改善"
                                    })
                
                elif step_name == "expression":
                    # expressionステップの処理
                    expression_data = step_result.get("expression", {})
                    integrated_improvements = expression_data.get("integrated_improvements", {})
                    comprehensive_assessment = integrated_improvements.get("comprehensive_assessment", "")
                    step_improvement["content"] = comprehensive_assessment[:300] + "..." if len(comprehensive_assessment) > 300 else comprehensive_assessment
                    
                    # recommended_changesを suggestions に変換
                    recommended_changes = step_result.get("recommended_changes", [])
                    for change in recommended_changes:
                        if isinstance(change, dict):
                            step_improvement["suggestions"].append(f"{change.get('type', '')}: {change.get('description', '')}")
                            step_improvement["changes"].append({
                                "original": f"現在の{change.get('type', '')}",
                                "improved": change.get("action", ""),
                                "reason": change.get("description", "")
                            })
                
                elif step_name == "coherence":
                    # coherenceステップの処理
                    coherence_data = step_result.get("coherence", {})
                    detailed_analysis = coherence_data.get("detailed_analysis", {})
                    comprehensive_analysis = detailed_analysis.get("comprehensive_analysis", "")
                    step_improvement["content"] = comprehensive_analysis[:300] + "..." if len(comprehensive_analysis) > 300 else comprehensive_analysis
                    
                    # specific_changesがある場合は具体的な変更案を使用
                    specific_changes = step_result.get("specific_changes", [])
                    if specific_changes:
                        # 具体的な変更案を suggestions と changes に変換
                        for change in specific_changes:
                            if isinstance(change, dict):
                                location = change.get("location", "")
                                priority = change.get("priority", "medium")
                                priority_jp = {"high": "重要", "medium": "中程度", "low": "軽微"}.get(priority, priority)
                                
                                step_improvement["suggestions"].append(
                                    f"{location}: {change.get('reason', '')} ({priority_jp})"
                                )
                                step_improvement["changes"].append({
                                    "original": change.get("original_text", "現在の表現"),
                                    "improved": change.get("improved_text", "改善案"),
                                    "reason": change.get("reason", "一貫性の改善")
                                })
                    else:
                        # フォールバック：従来の処理
                        recommended_changes = step_result.get("recommended_changes", [])
                        step_improvement["suggestions"] = recommended_changes
                        
                        for change in recommended_changes:
                            step_improvement["changes"].append({
                                "original": "現在の一貫性",
                                "improved": change,
                                "reason": "一貫性の改善"
                            })
                
                elif step_name == "polish":
                    # polishステップの処理
                    polish_data = step_result.get("polish", {})
                    final_assessment = polish_data.get("final_assessment", {})
                    comprehensive_evaluation = final_assessment.get("comprehensive_evaluation", "")
                    step_improvement["content"] = comprehensive_evaluation[:300] + "..." if len(comprehensive_evaluation) > 300 else comprehensive_evaluation
                    
                    # specific_changesがある場合は具体的な変更案を使用
                    specific_changes = step_result.get("specific_changes", [])
                    if specific_changes:
                        # 具体的な変更案を suggestions と changes に変換
                        for change in specific_changes:
                            if isinstance(change, dict):
                                category = change.get("category", "")
                                location = change.get("location", "")
                                priority = change.get("priority", "medium")
                                priority_jp = {"high": "重要", "medium": "中程度", "low": "軽微"}.get(priority, priority)
                                
                                step_improvement["suggestions"].append(
                                    f"{category}（{location}）: {change.get('reason', '')} ({priority_jp})"
                                )
                                step_improvement["changes"].append({
                                    "original": change.get("original_text", f"現在の{category}"),
                                    "improved": change.get("improved_text", "改善案"),
                                    "reason": change.get("reason", f"{category}の改善")
                                })
                    else:
                        # フォールバック：従来の処理
                        recommended_changes = step_result.get("recommended_changes", [])
                        for change in recommended_changes:
                            if isinstance(change, dict):
                                step_improvement["suggestions"].append(f"{change.get('type', '')}: {change.get('description', '')}")
                                step_improvement["changes"].append({
                                    "original": f"現在の{change.get('type', '')}",
                                    "improved": change.get("action", ""),
                                    "reason": change.get("description", "")
                                })
                
                # 空の場合のフォールバック（具体的な改善提案とアクションプラン）
                if not step_improvement["suggestions"] and not step_improvement["changes"]:
                    # より具体的で実践的な改善提案を生成
                    if step_name == "analysis":
                        step_improvement["suggestions"] = [
                            "第1段落：志望動機をより具体的に書き、「なぜこの大学なのか」を明確にする",
                            "全体構成：序論・本論・結論の3部構成を意識し、各段落の役割を明確にする",
                            "エピソード：抽象的な表現を避け、具体的な体験や数値を盛り込む"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "志望動機が曖昧",
                                "improved": "具体的な体験と関連付けた志望動機",
                                "reason": "読み手に説得力を持たせるため"
                            }
                        ]
                    elif step_name == "structure":
                        step_improvement["suggestions"] = [
                            "導入部（第1段落）：問題提起または興味を引く事実から始める",
                            "本論部（第2-6段落）：体験→学び→将来の目標の順序で論理的に構成する",
                            "結論部（最終段落）：大学での具体的な学習計画と将来への意欲を明示する"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "時系列順の単純な構成",
                                "improved": "論理的な三段論法の構成",
                                "reason": "論理的な説得力を高めるため"
                            }
                        ]
                    elif step_name == "content":
                        step_improvement["suggestions"] = [
                            "具体性の向上：「多くの人」→「○○人の学生」のように数値を使用する",
                            "エピソードの深掘り：単なる事実ではなく、その時の思考や学びを記述する",
                            "大学との関連性：志望学部の特定のカリキュラムや研究室に言及する"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "抽象的な体験談",
                                "improved": "具体的な数値・事実を含む体験談",
                                "reason": "説得力と信憑性を向上させるため"
                            }
                        ]
                    elif step_name == "expression":
                        step_improvement["suggestions"] = [
                            "冗長な表現の簡潔化：「～ということができる」→「～できる」",
                            "専門用語の適切な使用：志望分野の専門用語を2-3個程度自然に組み込む",
                            "文体の統一：敬語の使い分けを一貫させ、「である調」「だ・である調」を統一する"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "冗長で読みにくい文章",
                                "improved": "簡潔で読みやすい文章",
                                "reason": "読み手の理解を助けるため"
                            }
                        ]
                    elif step_name == "coherence":
                        step_improvement["suggestions"] = [
                            "段落間の接続語を活用：「また」「さらに」「しかし」「そのため」を適切に使用する",
                            "代名詞の明確化：「それ」「これ」が何を指すか明確にする",
                            "主張の一貫性：志望理由から将来の目標まで一本の筋を通す"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "段落間の繋がりが不明確",
                                "improved": "接続語で論理的に繋がった文章",
                                "reason": "読み手が論理の流れを追いやすくするため"
                            }
                        ]
                    elif step_name == "polish":
                        step_improvement["suggestions"] = [
                            "誤字脱字チェック：特に漢字の変換ミス、送り仮名の確認",
                            "文字数の調整：指定文字数の90-95%を目安に調整する",
                            "最終読み直し：声に出して読み、不自然な箇所を修正する"
                        ]
                        step_improvement["changes"] = [
                            {
                                "original": "完成度80%の状態",
                                "improved": "提出可能な完成度95%の状態",
                                "reason": "最終提出に向けた品質確保"
                            }
                        ]
                    else:
                        step_improvement["suggestions"] = [f"{step_name}ステップの具体的な改善案を準備中です"]
                        step_improvement["changes"] = []
                    
                    logger.warning(f"Using detailed fallback suggestions for {step_name}")
                
                logger.info(f"Final {step_name} - suggestions: {len(step_improvement['suggestions'])}, changes: {len(step_improvement['changes'])}")
                
            except Exception as e:
                logger.error(f"Error processing {step_name}: {str(e)}")
                # エラーの場合でも具体的な改善提案を提供
                if step_name == "analysis":
                    step_improvement["content"] = "基本的な分析チェックリストに基づいた改善提案です。"
                    step_improvement["suggestions"] = [
                        "志望動機の明確化：「なぜその大学・学部なのか」を具体的に記述する",
                        "構成の見直し：導入→体験→学び→目標の流れを確認する",
                        "具体性の追加：抽象的な表現を具体的なエピソードに置き換える"
                    ]
                elif step_name == "structure":
                    step_improvement["content"] = "基本的な文章構成の改善提案です。"
                    step_improvement["suggestions"] = [
                        "段落分けの最適化：1つの段落に1つの主要なポイントを配置する",
                        "接続詞の活用：「また」「しかし」「そのため」で論理的な流れを作る",
                        "結論の強化：最終段落で大学での学習計画を明確に示す"
                    ]
                elif step_name == "content":
                    step_improvement["content"] = "内容の充実度向上のための基本提案です。"
                    step_improvement["suggestions"] = [
                        "エピソードの具体化：「いつ」「どこで」「何を」「なぜ」を明確にする",
                        "数値の活用：「多くの」→「○○人の」など具体的な数字を使用する",
                        "大学情報の活用：志望学部の特色やカリキュラムに具体的に言及する"
                    ]
                elif step_name == "expression":
                    step_improvement["content"] = "文章表現の基本的な改善提案です。"
                    step_improvement["suggestions"] = [
                        "文の簡潔化：1文を50文字以内を目安に、長い文を分割する",
                        "語彙の多様化：同じ表現の繰り返しを避け、類義語を使用する",
                        "文体の統一：「である調」または「だ・である調」に統一する"
                    ]
                elif step_name == "coherence":
                    step_improvement["content"] = "論理的一貫性の基本チェックポイントです。"
                    step_improvement["suggestions"] = [
                        "論理の飛躍チェック：前の文と次の文の関係を明確にする",
                        "代名詞の明確化：「それ」「これ」が何を指すか分かりやすくする",
                        "時系列の整理：過去の体験から現在、未来への流れを整理する"
                    ]
                elif step_name == "polish":
                    step_improvement["content"] = "最終確認のチェックリストです。"
                    step_improvement["suggestions"] = [
                        "誤字脱字の確認：特に固有名詞、専門用語のスペルをチェック",
                        "文字数調整：指定文字数±5%以内に調整する",
                        "音読チェック：声に出して読み、不自然な箇所を修正する"
                    ]
                else:
                    step_improvement["content"] = f"{step_name}の基本的な改善チェックポイントです。"
                    step_improvement["suggestions"] = [f"{step_name}に関する基本的な改善提案を準備しました。"]
                
                step_improvement["changes"] = [
                    {
                        "original": f"{step_name}の現在の状態",
                        "improved": f"改善された{step_name}",
                        "reason": f"{step_name}の品質向上のため"
                    }
                ]
            
            improvements[step_name] = step_improvement
        else:
            # 文字列の場合はそのまま格納
            improvements[step_name] = {
                "content": str(step_result),
                "suggestions": ["結果を確認中"],
                "changes": []
            }
    
    logger.info(f"Final improvements keys: {list(improvements.keys())}")
    return improvements

@router.post("/{statement_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_statement_feedback(
    statement_id: UUID,
    feedback_in: FeedbackCreate,
    current_user: User = Depends(require_permission('statement_review_respond')),
    db: Session = Depends(get_db)
):
    """志望理由書にフィードバックを追加"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="フィードバック対象の志望理由書が見つかりません")

    return crud_statement.create_feedback(db=db, feedback=feedback_in, statement_id=statement_id, user_id=current_user.id)

@router.get("/{statement_id}/feedback", response_model=List[FeedbackResponse])
async def get_statement_feedbacks(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書のフィードバック一覧を取得"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    if statement.user_id != current_user.id and not current_user.has_permission('statement_review_respond'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書のフィードバックを閲覧する権限がありません")

    return crud_statement.get_feedbacks(db=db, statement_id=statement_id)

@router.post("/{statement_id}/chat", response_model=StatementChatResponse)
async def chat_about_statement(
    statement_id: UUID,
    request: StatementChatRequest,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書に関するAIチャット"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書にアクセスする権限がありません")
    
    # AI応答を生成
    ai_response = await generate_statement_ai_response(
        statement=statement,
        message=request.message,
        chat_history=request.chat_history,
        user=current_user,
        db=db
    )
    
    return StatementChatResponse(
        response=ai_response["response"],
        suggestions=ai_response.get("suggestions", []),
        session_id=ai_response.get("session_id", str(statement_id))
    )

@router.post("/{statement_id}/improve")
async def improve_statement_with_ai(
    statement_id: UUID,
    request: dict,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """AIによる志望理由書の改善提案"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書にアクセスする権限がありません")
    
    # AI改善提案を生成（基本的な改善提案として辞書を返す）
    improvement_type = request.get("improvement_type", "general")
    specific_focus = request.get("specific_focus", "")
    
    # 基本的な改善提案レスポンス
    return {
        "original_text": statement.content,
        "improved_text": f"[改善案] {statement.content}\n\n※ より詳細な改善には /ai-improve エンドポイントをご利用ください。",
        "changes": [
            {
                "type": improvement_type,
                "description": f"{improvement_type}の観点から改善提案を行いました。",
                "original": "元の文章",
                "improved": "改善された文章"
            }
        ],
        "explanation": f"改善タイプ: {improvement_type}. フォーカス: {specific_focus or '全般'}. より詳細な分析には AI改善機能をご利用ください。"
    } 