import os
import json
import asyncio
import httpx
import logging
from fastapi import HTTPException
from datetime import datetime
from app.core.config import settings
from typing import List, Dict, AsyncGenerator, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def stream_openai_response(messages: List[Dict], session_id: str) -> AsyncGenerator[str, None]:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            temperature=0.7
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content is not None:
                try:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
                except Exception as e:
                    logger.error(f"Error while streaming chunk: {str(e)}")
                    continue
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error from OpenAI: {str(e)}")
        yield f"data: エラーが発生しました: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

async def generate_study_plan(subject: str, goal: str, duration: int, level: str) -> Dict[str, Any]:
    """
    AIを使用して学習計画を生成する
    
    Parameters:
    - subject: 学習科目 (例: "数学", "英語", "プログラミング")
    - goal: 学習目標 (例: "大学入試対策", "TOEIC 800点取得")
    - duration: 学習期間（日数）
    - level: 学習レベル (例: "初級", "中級", "上級")
    
    Returns:
    - 学習計画データ（目標リストを含む）
    """
    try:
        # AIに渡すプロンプトを作成
        prompt = f"""
あなたは教育専門家で、学生の学習計画を作成するエキスパートです。
以下の条件に基づいて、効果的な学習計画を作成してください。

科目: {subject}
目標: {goal}
期間: {duration}日間
レベル: {level}

学習計画には、複数の具体的な学習目標を含めてください。各目標には以下の情報を含めます：
1. タイトル（具体的な学習活動）
2. 詳細な説明（なぜこの活動が重要か、どう取り組むべきか）
3. 目標達成予定日（適切な期間配分）
4. 優先度（1～5、5が最も高い）

学習期間全体に渡って、バランスよく目標を配置してください。
基礎から応用へと進む段階的なアプローチを取り入れてください。

出力はJSON形式で、以下の構造に従ってください：
{{
  "goals": [
    {{
      "title": "目標1のタイトル",
      "description": "目標1の詳細説明",
      "target_date": "YYYY-MM-DD",
      "priority": 3
    }},
    {{
      "title": "目標2のタイトル",
      "description": "目標2の詳細説明",
      "target_date": "YYYY-MM-DD",
      "priority": 4
    }},
    // 他の目標...（合計5～8個程度の目標を設定）
  ]
}}

回答はJSON形式のみで返してください。JSON以外のテキストは含めないでください。
"""
        
        # OpenAI APIを呼び出し
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "あなたは学習計画を生成するAIアシスタントです。JSONフォーマットで回答してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # レスポンスからJSONデータを抽出
        response_text = response.choices[0].message.content.strip()
        
        # JSONではない部分（マークダウンコードブロックなど）を削除
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # JSON形式のレスポンスを解析
        plan_data = json.loads(response_text)
        
        # 目標の日付を整形（現在の日付から相対的に設定）
        current_date = datetime.now().date()
        for i, goal in enumerate(plan_data["goals"]):
            if "target_date" not in goal or not goal["target_date"]:
                # 期間を均等に分割して目標日を設定
                days_per_goal = duration // len(plan_data["goals"])
                goal_day = current_date.replace(day=current_date.day + (i+1) * days_per_goal)
                goal["target_date"] = goal_day.isoformat()
        
        return plan_data
        
    except Exception as e:
        logger.error(f"Error generating study plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"学習計画の生成に失敗しました: {str(e)}"
        ) 