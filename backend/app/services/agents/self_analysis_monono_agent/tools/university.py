from typing import List, Dict, Optional
from sqlalchemy import select, or_

from app.database.database import AsyncSessionLocal
from app.models.university import University, Department
import requests
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

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

def course_search(keyword: str, field: Optional[str] = None, limit: int = 20) -> list[dict]:
    """学部・ゼミ検索。DuckDuckGoで検索し、結果ページからname/programを抽出して返す"""
    query = f"{keyword} {field or ''} university curriculum"
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=limit)
    universities = []
    for item in results or []:
        title = item.get('title')
        url = item.get('href')
        program = None
        try:
            resp = requests.get(url, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # ページタイトルをプログラム名称とみなす
            h1 = soup.find('h1')
            program = h1.get_text(strip=True) if h1 else title
        except Exception:
            program = title
        universities.append({
            'name': title,
            'program': program,
            'url': url
        })
    return universities

def admission_stats(univ: str) -> dict:
    """倍率・募集人数・出願要件などをDuckDuckGo検索結果ページから抽出して返す"""
    query = f"{univ} admission statistics"
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=1)
    if not results:
        return {}
    url = results[0].get('href')
    stats = {}
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        if table:
            for row in table.find_all('tr'):
                cols = row.find_all(['th', 'td'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True)
                    val = cols[1].get_text(strip=True)
                    stats[key] = val
    except Exception:
        return {}
    return stats

def fit_score(crit: dict, program_info: dict) -> float:
    """SequenceMatcherによる簡易フィットスコア計算（0–1）"""
    crit_text = ' '.join(str(v) for v in crit.values())
    prog_text = ' '.join(str(v) for v in program_info.values())
    if not crit_text or not prog_text:
        return 0.0
    score = SequenceMatcher(None, crit_text, prog_text).ratio()
    return float(score) 