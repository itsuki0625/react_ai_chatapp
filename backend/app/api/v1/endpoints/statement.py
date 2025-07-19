from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
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
                
                # 空の場合のフォールバック（より自然な日本語メッセージ）
                if not step_improvement["suggestions"] and not step_improvement["changes"]:
                    fallback_messages = {
                        "analysis": "総合的な分析結果を確認中です",
                        "structure": "文章構成の改善案を検討中です", 
                        "content": "内容の充実度を分析中です",
                        "expression": "表現力の向上案を検討中です",
                        "coherence": "論理的一貫性を分析中です",
                        "polish": "最終的な仕上げを確認中です"
                    }
                    step_improvement["suggestions"] = [fallback_messages.get(step_name, f"{step_name}の分析を実行中です")]
                    step_improvement["changes"] = []
                    logger.warning(f"No suggestions or changes found for {step_name}")
                
                logger.info(f"Final {step_name} - suggestions: {len(step_improvement['suggestions'])}, changes: {len(step_improvement['changes'])}")
                
            except Exception as e:
                logger.error(f"Error processing {step_name}: {str(e)}")
                # エラーの場合のフォールバック（より自然な日本語メッセージ）
                error_messages = {
                    "analysis": "分析結果の処理中です",
                    "structure": "構成分析を再実行中です",
                    "content": "内容分析を処理中です", 
                    "expression": "表現分析を確認中です",
                    "coherence": "一貫性分析を処理中です",
                    "polish": "最終確認を実行中です"
                }
                step_improvement["content"] = error_messages.get(step_name, f"{step_name}の分析を処理中です")
                step_improvement["suggestions"] = ["分析結果を準備中です。しばらくお待ちください。"]
                step_improvement["changes"] = []
            
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