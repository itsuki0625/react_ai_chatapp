from typing import List, Dict
from sqlalchemy import select, or_

from app.database.database import AsyncSessionLocal
from app.models.university import University, Department

async def uni_search(session_id: str, keyword: str) -> List[Dict]:
    """
    キーワードで大学名・コードを検索し、ID・名前・コードを返します。
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(University).where(
                University.is_active == True,
                or_(
                    University.name.ilike(f"%{keyword}%"),
                    University.university_code.ilike(f"%{keyword}%")
                )
            )
        )
        universities = result.scalars().all()
        return [
            {"id": str(u.id), "name": u.name, "university_code": u.university_code}
            for u in universities
        ]

async def course_lookup(session_id: str, university_code: str) -> List[Dict]:
    """
    大学コードに基づいて所属学部・学科一覧を取得します。
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Department).join(University).where(
                University.university_code == university_code,
                Department.is_active == True
            )
        )
        departments = result.scalars().all()
        return [
            {"id": str(d.id), "name": d.name, "department_code": d.department_code}
            for d in departments
        ]

async def prof_lookup(session_id: str, department_code: str) -> List[Dict]:
    """
    学科コードに基づいて教授一覧を取得します。
    プロフェッサーモデルが未定義のため、空リストを返却します。
    """
    # TODO: Professorモデルを app.models.university に追加し、実装を行ってください
    return [] 