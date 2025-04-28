from typing import List, Dict, Optional, Any
from agents import Runner # OpenAI Agents SDK をインポート
# from app.core.config import settings # APIキーは環境変数から直接読み込む想定
from app.services.agents import self_analysis_agent, admission_agent, study_support_agent # エージェント定義をインポート
import logging

# Agent SDKは環境変数 OPENAI_API_KEY を参照する想定

logger = logging.getLogger(__name__)

async def get_self_analysis_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    自己分析用のAgentを利用し、ユーザー入力に基づいて応答を生成します。
    history: Agent SDK で会話履歴を渡す方法はドキュメント参照が必要。
             現時点ではAgentのstate管理外とし、都度実行。
    """
    try:
        print(f"Running {self_analysis_agent.name} with input: {user_input[:50]}...")

        # Runnerを使ってエージェントを実行 (非同期)
        # TODO: 会話履歴をAgentに渡す方法を調査・実装する
        # シンプルな実行: 毎回新しい会話として扱われる
        result: Any = await Runner.run(self_analysis_agent, user_input)

        # print(f"Agent {self_analysis_agent.name} run finished. Status: {result.status}") # Comment out problematic line

        if result.final_output:
            # result.output に最終的な応答が含まれると想定 (ドキュメント確認推奨)
            final_output = str(result.final_output) # 型が不明なためstrに変換
            print(f"Agent {self_analysis_agent.name} final output: {final_output[:100]}...")
            return final_output.strip()
        else:
            # 応答がない、またはエラーの場合の処理
            # print(f"Agent {self_analysis_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
            # Accessing result.error directly is likely fine
            print(f"Agent {self_analysis_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
            # result.history や result.events で詳細を確認できる可能性
            # print(f"Agent run events: {result.events}")
            return "申し訳ありません、AIからの応答を取得できませんでした。" # エラー時のデフォルトメッセージ

    except ImportError as e:
         print(f"Error importing openai-agents: {e}. Make sure it is installed.")
         return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
    except Exception as e:
        logger.error(f"An unexpected error occurred while running agent {getattr(self_analysis_agent, 'name', 'SelfAnalysis')}: {e}", exc_info=True)
        return "申し訳ありません、自己分析AIの実行中にエラーが発生しました。"

async def get_admission_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    総合型選抜AI用のAgentを利用し、応答を生成します。
    """
    try:
        print(f"Running {admission_agent.name} with input: {user_input[:50]}...")
        result = await Runner.run(admission_agent, user_input)
        # print(f"Agent {admission_agent.name} run finished. Status: {result.status}") # Comment out problematic line
        if result.final_output: return str(result.final_output).strip()
        else:
            # print(f"Agent {admission_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
            print(f"Agent {admission_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
            return "申し訳ありません、AIからの応答を取得できませんでした。"
    except ImportError as e:
         print(f"Error importing openai-agents: {e}. Make sure it is installed.")
         return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
    except Exception as e:
        logger.error(f"An unexpected error occurred while running agent {getattr(admission_agent, 'name', 'Admission')}: {e}", exc_info=True)
        return "申し訳ありません、総合型選抜AIの実行中にエラーが発生しました。"

async def get_study_support_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    汎用学習支援AI用のAgentを利用し、応答を生成します。
    """
    try:
        print(f"Running {study_support_agent.name} with input: {user_input[:50]}...")
        result = await Runner.run(study_support_agent, user_input)
        # print(f"Agent {study_support_agent.name} run finished. Status: {result.status}") # Comment out problematic line
        if result.final_output: return str(result.final_output).strip()
        else:
            # print(f"Agent {study_support_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
            print(f"Agent {study_support_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
            return "申し訳ありません、AIからの応答を取得できませんでした。"
    except ImportError as e:
         print(f"Error importing openai-agents: {e}. Make sure it is installed.")
         return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
    except Exception as e:
        logger.error(f"An unexpected error occurred while running agent {getattr(study_support_agent, 'name', 'StudySupport')}: {e}", exc_info=True)
        return "申し訳ありません、学習支援AIの実行中にエラーが発生しました。"

# --- 以前のコードは削除済 --- 

# ai_service = AIService()

# async def get_self_analysis_response(user_input: str, history: List[Dict[str, str]]) -> Optional[str]:
#     ... 