from typing import Optional, List
from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.models.self_analysis import SelfAnalysisNote as Note, Summary

async def note_store(session_id: str, step: str, content: dict) -> str:
    """
    セッションIDとステップに対応するノートを保存します。
    """
    async with AsyncSessionLocal() as db:
        note = Note(session_id=session_id, step=step, content=content)
        db.add(note)
        await db.commit()
    return "ok"

async def list_notes(session_id: str, step: Optional[str] = None) -> List[dict]:
    """
    指定のセッションIDおよびステップに紐づくノート一覧を取得します。
    """
    async with AsyncSessionLocal() as db:
        stmt = select(Note).where(Note.session_id == session_id)
        if step:
            stmt = stmt.where(Note.step == step)
        result = await db.execute(stmt)
        notes = result.scalars().all()
        return [n.content for n in notes]

async def get_summary(session_id: str) -> dict:
    """
    指定のセッションIDのサマリーを取得します。
    """
    async with AsyncSessionLocal() as db:
        summary = await db.get(Summary, session_id)
        if not summary:
            return {}
        return {
            "q1": summary.q1,
            "q2": summary.q2,
            "q3": summary.q3,
            "q4": summary.q4,
            "q5": summary.q5,
            "q6": summary.q6,
            "q7": summary.q7,
            "q8": summary.q8,
            "q9": summary.q9,
        } 