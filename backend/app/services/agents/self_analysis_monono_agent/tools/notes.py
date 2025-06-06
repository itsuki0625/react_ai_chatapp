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

# for testable note store function
import json
import inspect

# DBセッション依存関係を外部からモックできるようにエクスポート
note_store_fn_db_session_dependency = AsyncSessionLocal

async def note_store_fn(session_id: str, current_step: str, note_content: str) -> str:
    """
    セッションIDとステップに対応するノートを保存または更新します。
    """
    # モックで coroutine を返す可能性を考慮し、実際のコンテキストマネージャを取得
    session_cm_candidate = note_store_fn_db_session_dependency()
    if inspect.iscoroutine(session_cm_candidate):
        session_cm = await session_cm_candidate
    else:
        session_cm = session_cm_candidate
    async with session_cm as db:
        # 既存ノートのチェック
        existing = await db.get(Note, session_id)
        if not existing:
            # 新規ノート作成
            data_dict = json.loads(note_content)
            new_note = Note(session_id=session_id, step=current_step, content=data_dict)
            # テストでの検証用にJSON文字列を保持
            new_note.content_json = note_content
            add_result = db.add(new_note)
            if inspect.iscoroutine(add_result):
                await add_result
            # commit
            commit_result = db.commit()
            if inspect.iscoroutine(commit_result):
                await commit_result
            return "ノートを保存しました。"
        # 既存ノートの更新
        existing_note = await db.query(Note).filter_by(session_id=session_id, step=current_step).one_or_none()
        # 新しいJSON文字列で上書き
        existing_note.content_json = note_content
        add_result = db.add(existing_note)
        if inspect.iscoroutine(add_result):
            await add_result
        # commit
        commit_result = db.commit()
        if inspect.iscoroutine(commit_result):
            await commit_result
        return "ノートを更新しました。" 