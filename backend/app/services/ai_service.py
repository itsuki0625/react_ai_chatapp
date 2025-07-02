# from typing import List, Dict, Optional, Any
# from agents import Runner # OpenAI Agents SDK をインポート
# # from app.core.config import settings # APIキーは環境変数から直接読み込む想定
# from app.services.agents import self_analysis_agent, admission_agent, study_support_agent # エージェント定義をインポート
# import logging


# logger = logging.getLogger(__name__)

# async def get_admission_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
#     """
#     総合型選抜AI用のAgentを利用し、応答を生成します。
#     """
#     try:
#         print(f"Running {admission_agent.name} with input: {user_input[:50]}...")
#         result = await Runner.run(admission_agent, user_input)
#         # print(f"Agent {admission_agent.name} run finished. Status: {result.status}") # Comment out problematic line
#         if result.final_output: return str(result.final_output).strip()
#         else:
#             # print(f"Agent {admission_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
#             print(f"Agent {admission_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
#             return "申し訳ありません、AIからの応答を取得できませんでした。"
#     except ImportError as e:
#          print(f"Error importing openai-agents: {e}. Make sure it is installed.")
#          return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
#     except Exception as e:
#         logger.error(f"An unexpected error occurred while running agent {getattr(admission_agent, 'name', 'Admission')}: {e}", exc_info=True)
#         return "申し訳ありません、総合型選抜AIの実行中にエラーが発生しました。"

# async def get_study_support_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
#     """
#     汎用学習支援AI用のAgentを利用し、応答を生成します。
#     """
#     try:
#         print(f"Running {study_support_agent.name} with input: {user_input[:50]}...")
#         result = await Runner.run(study_support_agent, user_input)
#         # print(f"Agent {study_support_agent.name} run finished. Status: {result.status}") # Comment out problematic line
#         if result.final_output: return str(result.final_output).strip()
#         else:
#             # print(f"Agent {study_support_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
#             print(f"Agent {study_support_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
#             return "申し訳ありません、AIからの応答を取得できませんでした。"
#     except ImportError as e:
#          print(f"Error importing openai-agents: {e}. Make sure it is installed.")
#          return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
#     except Exception as e:
#         logger.error(f"An unexpected error occurred while running agent {getattr(study_support_agent, 'name', 'StudySupport')}: {e}", exc_info=True)
#         return "申し訳ありません、学習支援AIの実行中にエラーが発生しました。"

# # --- 以前のコードは削除済 --- 

# # ai_service = AIService()

# # async def get_self_analysis_response(user_input: str, history: List[Dict[str, str]]) -> Optional[str]:
# #     ... 

from uuid import uuid4
from app.services.agents.self_analysis_langchain.main import SelfAnalysisOrchestrator
import logging
from typing import List, Dict, Optional, Any
import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.personal_statement import PersonalStatement
from app.models.user import User
from sqlalchemy.orm import Session
import difflib

logger = logging.getLogger(__name__)

async def get_self_analysis_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    monono_agent の SelfAnalysisAdvisor を利用して応答を生成します。
    history は現状サポートせず、毎回新規会話として扱います。
    """
    try:
        # 新しいセッションIDを生成し、オーケストレーターで自己分析を実行
        session_id = str(uuid4())
        orchestrator = SelfAnalysisOrchestrator()
        # messages リストを渡して実行
        result = await orchestrator.run([{"role": "user", "content": user_input}], session_id)
        # user_visible にクライアントに返す内容が含まれる
        if isinstance(result, dict):
            return result.get("user_visible") or result.get("final_notes") or None
        return str(result)
    except Exception as e:
        logger.error(f"Unexpected error in get_self_analysis_agent_response: {e}", exc_info=True)
        return "申し訳ありません、自己分析AIの実行中にエラーが発生しました。"

async def get_admission_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    総合型選抜AI用のAgentは未実装のため、簡易メッセージを返却します。
    """
    try:
        return "申し訳ありません、現在総合型選抜AIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_admission_agent_response: {e}", exc_info=True)
        return "申し訳ありません、総合型選抜AIの実行中にエラーが発生しました。"

async def get_study_support_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    学習支援AI用のAgentは未実装のため、簡易メッセージを返却します。
    """
    try:
        return "申し訳ありません、現在学習支援AIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_study_support_agent_response: {e}", exc_info=True)
        return "申し訳ありません、学習支援AIの実行中にエラーが発生しました。"

async def get_review_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    レビューAI用のAgentを利用して応答を生成します。
    """
    try:
        return "申し訳ありません、現在レビューAIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_review_agent_response: {e}", exc_info=True)
        return "申し訳ありません、レビューAIの実行中にエラーが発生しました。"

async def generate_statement_ai_response(
    statement: PersonalStatement,
    message: str,
    chat_history: List[dict],
    user: User,
    db: Session
) -> Dict[str, Any]:
    """
    志望理由書に関するAIチャット応答を生成
    """
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 志望理由書のコンテキストを構築
        context = build_statement_context(statement, db)
        
        # システムメッセージを構築
        system_message = f"""あなたは志望理由書の作成をサポートする専門的なAIアシスタントです。

現在編集中の志望理由書の情報:
- 志望大学: {context.get('university_name', '未設定')}
- 志望学部: {context.get('department_name', '未設定')}
- 現在の内容: 「{statement.content[:500]}{'...' if len(statement.content) > 500 else ''}」
- 文字数: {len(statement.content)}文字
- ステータス: {statement.status}

あなたの役割:
1. 志望理由書の内容について具体的で建設的なアドバイスを提供する
2. 文章の構成、論理性、表現力の改善提案をする
3. 志望動機の明確化をサポートする
4. 必要に応じて具体的な修正案を提示する

回答は以下の点を心がけてください:
- 具体的で実行可能なアドバイスを提供
- 学生の主体性を尊重し、考える機会を提供
- 志望大学・学部の特色を考慮したアドバイス
- 簡潔で分かりやすい日本語で回答"""

        # メッセージ履歴を構築
        messages = [{"role": "system", "content": system_message}]
        
        # チャット履歴を追加
        for hist_msg in chat_history[-10:]:  # 直近10件のみ使用
            if hist_msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": hist_msg['role'],
                    "content": hist_msg['content']
                })
        
        # 現在のメッセージを追加
        messages.append({"role": "user", "content": message})
        
        # OpenAI APIを呼び出し
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # 改善提案があるかチェック
        suggestions = extract_suggestions_from_response(ai_response)
        
        return {
            "response": ai_response,
            "suggestions": suggestions,
            "session_id": str(statement.id)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_statement_ai_response: {e}", exc_info=True)
        return {
            "response": "申し訳ありません、AI応答の生成中にエラーが発生しました。再度お試しください。",
            "suggestions": [],
            "session_id": str(statement.id)
        }

async def generate_statement_improvement(
    statement: PersonalStatement,
    improvement_type: str,
    specific_focus: str,
    user: User,
    db: Session
) -> Dict[str, Any]:
    """
    志望理由書の改善提案を生成（差分表示用）
    """
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 志望理由書のコンテキストを構築
        context = build_statement_context(statement, db)
        
        # 改善タイプに応じたプロンプトを選択
        improvement_prompts = {
            "general": "全体的な改善を行ってください。文章の流れ、論理性、表現力を向上させてください。",
            "structure": "文章の構成と構造を改善してください。段落の配置や論理的な流れを最適化してください。",
            "expression": "表現力と文体を改善してください。より印象的で説得力のある表現に変更してください。",
            "logic": "論理性を強化してください。主張と根拠の関係を明確にし、一貫性を高めてください。"
        }
        
        prompt = improvement_prompts.get(improvement_type, improvement_prompts["general"])
        if specific_focus:
            prompt += f"\n特に以下の点に注意してください: {specific_focus}"
        
        system_message = f"""あなたは志望理由書の添削専門家です。
        
現在の志望理由書の情報:
- 志望大学: {context.get('university_name', '未設定')}
- 志望学部: {context.get('department_name', '未設定')}
- 文字数: {len(statement.content)}文字

以下の志望理由書を改善してください:
{prompt}

改善要求:
1. 元の文章の意図や内容は保持してください
2. 改善された文章を提供してください
3. 主要な変更点を説明してください

元の文章:
{statement.content}

回答は以下のJSON形式で提供してください:
{{
    "improved_text": "改善された志望理由書の全文",
    "explanation": "改善内容の説明",
    "major_changes": ["主要な変更点1", "主要な変更点2", ...]
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": system_message}],
            temperature=0.5,
            max_tokens=2000
        )
        
        # JSON形式の応答をパース
        try:
            result = json.loads(response.choices[0].message.content)
            improved_text = result.get("improved_text", statement.content)
            explanation = result.get("explanation", "改善内容の説明を取得できませんでした。")
            major_changes = result.get("major_changes", [])
        except json.JSONDecodeError:
            # JSONパースに失敗した場合は、応答テキストをそのまま使用
            improved_text = response.choices[0].message.content
            explanation = "AI による改善提案です。"
            major_changes = []
        
        # 差分を生成
        changes = generate_diff_changes(statement.content, improved_text)
        
        return {
            "improved_text": improved_text,
            "changes": changes,
            "explanation": explanation,
            "major_changes": major_changes
        }
        
    except Exception as e:
        logger.error(f"Error in generate_statement_improvement: {e}", exc_info=True)
        return {
            "improved_text": statement.content,
            "changes": [],
            "explanation": "改善提案の生成中にエラーが発生しました。",
            "major_changes": []
        }

def build_statement_context(statement: PersonalStatement, db: Session) -> Dict[str, str]:
    """志望理由書のコンテキスト情報を構築"""
    context = {}
    
    if statement.desired_department and hasattr(statement.desired_department, 'department'):
        if statement.desired_department.department:
            context['department_name'] = statement.desired_department.department.name
            if hasattr(statement.desired_department.department, 'university') and statement.desired_department.department.university:
                context['university_name'] = statement.desired_department.department.university.name
    
    # 自己分析チャットの情報も含める場合は、ここで追加
    if statement.self_analysis_chat_id:
        # TODO: 自己分析チャットの内容を取得して要約を追加
        context['has_self_analysis'] = 'true'
    
    return context

def extract_suggestions_from_response(response_text: str) -> List[str]:
    """AI応答から改善提案を抽出"""
    suggestions = []
    
    # 簡単なパターンマッチングで提案を抽出
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in ['提案', '改善', '修正', 'おすすめ', '変更']):
            if len(line) > 10 and len(line) < 200:  # 適切な長さの提案のみ
                suggestions.append(line)
    
    return suggestions[:5]  # 最大5個まで

def generate_diff_changes(original: str, improved: str) -> List[Dict[str, Any]]:
    """原文と改善文の差分を生成"""
    changes = []
    
    # 文単位で差分を生成
    original_sentences = split_sentences(original)
    improved_sentences = split_sentences(improved)
    
    diff = list(difflib.unified_diff(
        original_sentences,
        improved_sentences,
        lineterm='',
        n=0
    ))
    
    change_id = 0
    for line in diff:
        if line.startswith('-') and not line.startswith('---'):
            # 削除された行
            changes.append({
                "id": f"change_{change_id}",
                "type": "delete",
                "original": line[1:].strip(),
                "improved": "",
                "line_number": change_id
            })
            change_id += 1
        elif line.startswith('+') and not line.startswith('+++'):
            # 追加された行
            changes.append({
                "id": f"change_{change_id}",
                "type": "add",
                "original": "",
                "improved": line[1:].strip(),
                "line_number": change_id
            })
            change_id += 1
    
    return changes

def split_sentences(text: str) -> List[str]:
    """文章を文単位で分割"""
    import re
    
    # 日本語の文の区切りを検出
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences 