from typing import Optional, List

from app.models.self_analysis import COT, Reflection

async def cot_store(session_id: str, step: str, cot: str) -> str:
    """
    セッションIDとステップに対応するChain-of-Thoughtを保存します。
    """
    await COT.objects.create(session_id=session_id, step=step, cot=cot)
    return "ok"

async def reflection_store(session_id: str, step: str, level: str, reflection: str) -> str:
    """
    セッションIDとステップ、レベル(micro|macro)に対応するリフレクションを保存します。
    """
    await Reflection.objects.create(session_id=session_id, step=step, level=level, reflection=reflection)
    return "ok"

async def list_reflections(session_id: str, step: Optional[str] = None, level: Optional[str] = None) -> List[dict]:
    """
    セッションID、ステップ、レベルでフィルタリングしたリフレクション一覧を返します。
    """
    q = Reflection.objects.filter(session_id=session_id)
    if step:
        q = q.filter(step=step)
    if level:
        q = q.filter(level=level)
    return [{"step": r.step, "level": r.level, "reflection": r.reflection} for r in q] 