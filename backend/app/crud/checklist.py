from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update, delete as sql_delete
from app.models.checklist import ChecklistEvaluation
from app.schemas.checklist import ChecklistEvaluationCreate, ChecklistEvaluationUpdate
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from uuid import UUID
from fastapi import HTTPException
import logging
from app.core.config import settings
import json
from datetime import datetime

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class ChecklistEvaluator:
    def __init__(self):
        self.evaluation_prompt = """
あなたは生徒の進路設計を行うプロフェッショナルです。
以下の会話履歴から、生徒の進路設計に関する以下の要素を評価してください：

チェックリスト:
1. 将来やりたいこと・実現したい夢・解決したい課題
   - 明確な目標や解決したい社会的・経済的・環境的問題が示されているか
   - 目標・課題の解決手段やアプローチ（ビジネス、技術、政策など）が言及されているか
2. 上記の目標や夢に至ったきっかけ
   - 幼少期や過去の経験、人物、書籍、出来事など、動機を形成した具体的な背景が示されているか
   - 当時の経験が現在の目標とどのようにつながっているかが明確になっているか
3. 目標実現・課題解決に向けて、これまで行ってきたこと
   - 具体的な取り組みや実践事例（起業、研究、ボランティア、プロジェクト参加など）が示されているか
   - その行動を通じて得た成果や気づき、学びが示されているか
4. 現状と目標とのギャップ
   - 自分が理想としている姿や解決策と、現実の状況との間にある差異が明確になっているか
   - なぜそのギャップが重要で、解消の必要があるのかが示されているか
5. ギャップが存在する理由の分析
   - 問題や課題が解決されていない背景要因（市場構造、大手企業の慣行、社会的通念、技術的制約など）が特定されているか
   - 当初の想定を妨げているブランド価値、コスト構造、利害関係者の思惑などの要因が挙げられているか
6. 目標実現・課題解決に必要な要素とその理由
   - 必要とされる資源（知識、スキル、ネットワーク、資金、組織体制など）が明確化されているか
   - なぜそれらが必要なのか、論理的な根拠（市場調査、アンケート結果、環境分析など）が示されているか
   - 課題発見から達成までを支援する新たな仕組みや専門家（コンサルタント、研究者、メンターなど）の価値が示されているか
7. 必要な要素が実現したときの良い影響
   - 社会的課題解決への貢献（環境保護、資源の有効活用、社会的インパクト）が提示されているか
   - 経済面（コスト削減、利益創出、持続可能な成長）や環境面（排出ガス削減、土壌汚染防止）へのポジティブな効果が列挙されているか
   - 個人・組織・社会の発展やイメージ向上に資する好循環の可能性が示されているか
8. 志望する進学先で学びたいこと
   - 指定した教育機関（大学、研究所など）の強み（教授陣の専門性、学際的研究、実践的プログラムなど）が示されているか
   - 具体的な講義名、研究会、ゼミ、研究分野が挙げられているか
   - 学びを通じて目標達成や課題解決へどのようにつなげるかの展望が示されているか

評価結果は以下のJSON形式で返してください：

{
    "checklist": [
        {
            "item": "将来やりたいこと・実現したい夢・解決したい課題",
            "status": "完了" | "未完了" | "一部完了",
            "summary": "生徒の回答の要約",
            "next_question": "この項目を深めるための次の質問"
        },
        {
            "item": "上記の目標や夢に至ったきっかけ",
            "status": "完了" | "未完了" | "一部完了",
            "summary": "生徒の回答の要約",
            "next_question": "この項目を深めるための次の質問"
        },
        // 他の項目も同様
    ],
    "overall_status": "完了" | "未完了" | "一部完了",
    "general_feedback": "全体的なフィードバック",
}

応答は必ず上記のJSON形式で返してください。
特に未完了や一部完了の項目がある場合は、その項目を深めるための具体的な質問を提案してください。
"""


    async def evaluate_chat(self, chat_history: List[Dict]) -> Optional[Dict]:
        formatted_history = "\n".join([
            f"{'User' if msg['role'].lower() == 'user' else 'Assistant'}: {msg['content']}"
            for msg in chat_history
        ])

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.evaluation_prompt},
                    {"role": "user", "content": formatted_history}
                ],
                response_format={ "type": "json_object" }
            )

            evaluation_result_str = response.choices[0].message.content
            logger.debug(f"Raw evaluation response from OpenAI: {evaluation_result_str}")
            try:
                evaluation_result = json.loads(evaluation_result_str)
                if "checklist" in evaluation_result and isinstance(evaluation_result["checklist"], list) and \
                   "overall_status" in evaluation_result and "general_feedback" in evaluation_result:
                    for item in evaluation_result["checklist"]:
                        if not all(k in item for k in ["item", "status", "summary", "next_question"]):
                            logger.error(f"Parsed JSON checklist item lacks expected keys: {item}")
                            return None
                    return evaluation_result
                else:
                    logger.error(f"Parsed JSON lacks expected top-level keys (checklist, overall_status, general_feedback). Got: {evaluation_result.keys() if isinstance(evaluation_result, dict) else 'Not a dict'}")
                    return None
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse OpenAI response as JSON: {json_err}")
                logger.error(f"Invalid JSON string: {evaluation_result_str}")
                return None
        except Exception as e:
            logger.error(f"Error interacting with OpenAI during evaluation: {e}", exc_info=True)
            return None

async def create_evaluation_records(
    db: AsyncSession,
    session_id: UUID,
    evaluation_data: Dict
) -> List[ChecklistEvaluation]:
    created_evaluations: List[ChecklistEvaluation] = []
    checklist_items_data = evaluation_data.get("checklist")

    if not checklist_items_data or not isinstance(checklist_items_data, list):
        logger.error(f"Invalid or missing checklist items in evaluation_data for session {session_id}.")
        return created_evaluations

    for item_data in checklist_items_data:
        try:
            db_item_evaluation = ChecklistEvaluation(
                session_id=session_id,
                checklist_item=item_data.get("item", "N/A"),
                is_completed=(item_data.get("status", "").lower() == "完了"),
                evaluated_at=datetime.utcnow()
            )
            db.add(db_item_evaluation)
            created_evaluations.append(db_item_evaluation)
        except Exception as e:
            logger.error(f"Error creating individual checklist item record for session {session_id}, item '{item_data.get('item')}': {e}", exc_info=True)
            pass

    return created_evaluations


async def get_evaluation_by_session_id(
    db: AsyncSession,
    session_id: UUID
) -> List[ChecklistEvaluation]:
    try:
        stmt = select(ChecklistEvaluation).filter(
            ChecklistEvaluation.session_id == session_id
        ).order_by(ChecklistEvaluation.created_at)
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting evaluations for session {session_id}: {e}", exc_info=True)
        return []

async def update_evaluation_for_session(
    db: AsyncSession,
    session_id: UUID,
    evaluation_data: Dict
) -> List[ChecklistEvaluation]:
    try:
        stmt_delete = sql_delete(ChecklistEvaluation).where(ChecklistEvaluation.session_id == session_id)
        await db.execute(stmt_delete)
        logger.info(f"Deleted existing evaluations for session {session_id}")

        new_evaluations = await create_evaluation_records(db, session_id, evaluation_data)
        
        logger.info(f"Successfully updated evaluations for session {session_id}. Created {len(new_evaluations)} new records.")
        return new_evaluations
    except Exception as e:
        logger.error(f"Error updating evaluations for session {session_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update evaluation data for session.") 