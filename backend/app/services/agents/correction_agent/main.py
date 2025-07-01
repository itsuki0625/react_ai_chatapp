from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import inspect
import json
import logging

# ステップエージェントのインポート
from .steps.analysis import AnalysisStepAgent
from .steps.structure import StructureStepAgent
from .steps.content import ContentStepAgent
from .steps.expression import ExpressionStepAgent
from .steps.coherence import CoherenceStepAgent
from .steps.polish import PolishStepAgent

logger = logging.getLogger(__name__)

# ステートスキーマ定義
class CorrectionState(TypedDict):
    statement_text: str          # 志望理由書本文
    messages: list               # メッセージ履歴
    session_id: str              # セッションID
    university_info: str         # 志望大学情報
    self_analysis_context: str   # 自己分析コンテキスト
    current_step: str | None     # 現在のステップ
    next_step: str | None        # 次のステップ
    current_response: str | None # 現在のレスポンス
    user_message: str | None     # ユーザー向けメッセージ
    step_results: dict           # 各ステップの結果

# ステップ実行のラッパー関数を定義
async def run_analysis_step(state: CorrectionState) -> CorrectionState:
    agent = AnalysisStepAgent()
    response = await agent(state)
    
    logger.info(f"ANALYSIS step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "ANALYSIS")
    step_completed = is_step_completed("ANALYSIS", response)
    next_step = determine_next_step("ANALYSIS", response, step_completed)
    
    logger.info(f"ANALYSIS step completed: {step_completed}, next_step: {next_step}")
    
    # ステップ結果を保存
    step_results = state.get("step_results", {})
    step_results["analysis"] = response
    
    return {
        **state, 
        "current_step": "ANALYSIS",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

async def run_structure_step(state: CorrectionState) -> CorrectionState:
    agent = StructureStepAgent()
    response = await agent(state)
    
    logger.info(f"STRUCTURE step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "STRUCTURE")
    step_completed = is_step_completed("STRUCTURE", response)
    next_step = determine_next_step("STRUCTURE", response, step_completed)
    
    logger.info(f"STRUCTURE step completed: {step_completed}, next_step: {next_step}")
    
    step_results = state.get("step_results", {})
    step_results["structure"] = response
    
    return {
        **state, 
        "current_step": "STRUCTURE",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

async def run_content_step(state: CorrectionState) -> CorrectionState:
    agent = ContentStepAgent()
    response = await agent(state)
    
    logger.info(f"CONTENT step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "CONTENT")
    step_completed = is_step_completed("CONTENT", response)
    next_step = determine_next_step("CONTENT", response, step_completed)
    
    logger.info(f"CONTENT step completed: {step_completed}, next_step: {next_step}")
    
    step_results = state.get("step_results", {})
    step_results["content"] = response
    
    return {
        **state, 
        "current_step": "CONTENT",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

async def run_expression_step(state: CorrectionState) -> CorrectionState:
    agent = ExpressionStepAgent()
    response = await agent(state)
    
    logger.info(f"EXPRESSION step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "EXPRESSION")
    step_completed = is_step_completed("EXPRESSION", response)
    next_step = determine_next_step("EXPRESSION", response, step_completed)
    
    logger.info(f"EXPRESSION step completed: {step_completed}, next_step: {next_step}")
    
    step_results = state.get("step_results", {})
    step_results["expression"] = response
    
    return {
        **state, 
        "current_step": "EXPRESSION",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

async def run_coherence_step(state: CorrectionState) -> CorrectionState:
    agent = CoherenceStepAgent()
    response = await agent(state)
    
    logger.info(f"COHERENCE step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "COHERENCE")
    step_completed = is_step_completed("COHERENCE", response)
    next_step = determine_next_step("COHERENCE", response, step_completed)
    
    logger.info(f"COHERENCE step completed: {step_completed}, next_step: {next_step}")
    
    step_results = state.get("step_results", {})
    step_results["coherence"] = response
    
    return {
        **state, 
        "current_step": "COHERENCE",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

async def run_polish_step(state: CorrectionState) -> CorrectionState:
    agent = PolishStepAgent()
    response = await agent(state)
    
    logger.info(f"POLISH step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "POLISH")
    # POLISHは最終ステップなので常にNone
    next_step = None
    
    logger.info(f"POLISH step completed, next_step: {next_step}")
    
    step_results = state.get("step_results", {})
    step_results["polish"] = response
    
    return {
        **state, 
        "current_step": "POLISH",
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message,
        "step_results": step_results
    }

def extract_user_message(response: str | dict, step: str) -> str:
    """エージェントレスポンスからユーザー向けメッセージを抽出"""
    try:
        if isinstance(response, dict):
            if "chat" in response and "question" in response["chat"]:
                return response["chat"]["question"]
            elif "chat" in response and "summary" in response["chat"]:
                return response["chat"]["summary"]
            elif "user_visible" in response:
                return response["user_visible"]
            else:
                return get_step_continuation_message(step)
        
        elif isinstance(response, str):
            if "Agent stopped due to iteration limit" in response or "time limit" in response:
                return get_step_continuation_message(step)
                
            if response.strip().startswith('{'):
                data = json.loads(response)
                if isinstance(data, dict):
                    if "chat" in data and "question" in data["chat"]:
                        return data["chat"]["question"]
                    elif "chat" in data and "summary" in data["chat"]:
                        return data["chat"]["summary"]
                    elif "user_visible" in data:
                        return data["user_visible"]
                    else:
                        return get_step_continuation_message(step)
            
            if response and ("?" in response or "？" in response or "ください" in response):
                return response
            
            return get_step_continuation_message(step)
            
    except Exception as e:
        logger.error(f"Error extracting user message: {e}")
        return get_step_continuation_message(step)

def get_step_continuation_message(step: str) -> str:
    """ステップ継続用のデフォルトメッセージ"""
    messages = {
        "ANALYSIS": "志望理由書の分析を完了しました。どの部分から改善を始めますか？",
        "STRUCTURE": "構成の改善案を提案しました。どの部分を見直しますか？",
        "CONTENT": "内容の深掘り案を提案しました。どのエピソードを詳しく書きますか？",
        "EXPRESSION": "表現の改善案を提案しました。どの表現を採用しますか？",
        "COHERENCE": "一貫性の確認を完了しました。全体的な流れはいかがですか？",
        "POLISH": "最終仕上げが完了しました。志望理由書の完成度はいかがですか？"
    }
    return messages.get(step, "次のステップに進みますか？")

def determine_next_step(current_step: str, response: str | dict, step_completed: bool) -> str | None:
    """次のステップを決定"""
    # ユーザーリクエストに基づく動的ステップ選択をここで実装
    # 基本的な順序: ANALYSIS → STRUCTURE → CONTENT → EXPRESSION → COHERENCE → POLISH
    
    step_flow = {
        "ANALYSIS": "STRUCTURE",
        "STRUCTURE": "CONTENT",
        "CONTENT": "EXPRESSION", 
        "EXPRESSION": "COHERENCE",
        "COHERENCE": "POLISH",
        "POLISH": None
    }
    
    if step_completed:
        return step_flow.get(current_step)
    else:
        return None  # 同じステップを継続

def is_step_completed(step: str, response: str | dict) -> bool:
    """ステップが完了したかどうかを判定"""
    try:
        # ユーザーからの特定のリクエストがない限り、一度の実行で完了とみなす
        # より高度な判定ロジックをここに実装可能
        return True
        
    except Exception as e:
        logger.error(f"Error checking step completion: {e}")
        return True  # エラー時は完了とみなす

def select_step_node(state: CorrectionState) -> str:
    """現在のステートに基づいて次に実行するステップを選択"""
    current_step = state.get("current_step")
    next_step = state.get("next_step")
    messages = state.get("messages", [])
    
    # 初回実行時はANALYSISから開始
    if not current_step and not next_step:
        return "ANALYSIS"
    
    # ユーザーからの特定のリクエストを解析
    if messages:
        last_message = messages[-1].get("content", "").lower()
        
        # 特定のステップに対するユーザーリクエストを検出
        if any(keyword in last_message for keyword in ["分析", "解析", "評価"]):
            return "ANALYSIS"
        elif any(keyword in last_message for keyword in ["構成", "構造", "流れ"]):
            return "STRUCTURE"
        elif any(keyword in last_message for keyword in ["内容", "詳しく", "具体的"]):
            return "CONTENT"
        elif any(keyword in last_message for keyword in ["表現", "言葉", "文章"]):
            return "EXPRESSION"
        elif any(keyword in last_message for keyword in ["一貫性", "論理", "矛盾"]):
            return "COHERENCE"
        elif any(keyword in last_message for keyword in ["仕上げ", "完成", "最終"]):
            return "POLISH"
    
    # デフォルトは次のステップまたは指定されたステップ
    return next_step or current_step or "ANALYSIS"

def decide_next_step(state: CorrectionState) -> str:
    """次のステップを決定する（エンド条件をチェック）"""
    next_step = state.get("next_step")
    
    if next_step is None:
        return END
    else:
        return next_step

class CorrectionOrchestrator:
    """志望理由書添削オーケストレーター"""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """LangGraphのワークフローを構築"""
        workflow = StateGraph(CorrectionState)
        
        # ノードを追加
        workflow.add_node("ANALYSIS", run_analysis_step)
        workflow.add_node("STRUCTURE", run_structure_step)
        workflow.add_node("CONTENT", run_content_step)
        workflow.add_node("EXPRESSION", run_expression_step)
        workflow.add_node("COHERENCE", run_coherence_step)
        workflow.add_node("POLISH", run_polish_step)
        
        # 条件付きエッジを追加
        workflow.add_conditional_edges(
            START,
            select_step_node,
            {
                "ANALYSIS": "ANALYSIS",
                "STRUCTURE": "STRUCTURE", 
                "CONTENT": "CONTENT",
                "EXPRESSION": "EXPRESSION",
                "COHERENCE": "COHERENCE",
                "POLISH": "POLISH"
            }
        )
        
        # 各ステップから次のステップまたはENDへの条件付きエッジ
        for step in ["ANALYSIS", "STRUCTURE", "CONTENT", "EXPRESSION", "COHERENCE", "POLISH"]:
            workflow.add_conditional_edges(
                step,
                decide_next_step,
                {
                    "ANALYSIS": "ANALYSIS",
                    "STRUCTURE": "STRUCTURE",
                    "CONTENT": "CONTENT", 
                    "EXPRESSION": "EXPRESSION",
                    "COHERENCE": "COHERENCE",
                    "POLISH": "POLISH",
                    END: END
                }
            )
        
        return workflow.compile()
    
    async def run(self, statement_text: str, messages: list, session_id: str, 
                  university_info: str = "", self_analysis_context: str = ""):
        """添削ワークフローを実行"""
        try:
            initial_state = {
                "statement_text": statement_text,
                "messages": messages,
                "session_id": session_id,
                "university_info": university_info,
                "self_analysis_context": self_analysis_context,
                "current_step": None,
                "next_step": None,
                "current_response": None,
                "user_message": None,
                "step_results": {}
            }
            
            logger.info(f"Starting correction workflow for session {session_id}")
            
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(f"Correction workflow completed for session {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in correction workflow: {e}", exc_info=True)
            raise e 