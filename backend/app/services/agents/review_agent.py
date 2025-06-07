# from __future__ import annotations
# from typing import List, Dict, Any, Literal, Optional, Union, AsyncIterator
# from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict
# import uuid # TokenGuardParams で UUID を使用するために確認
# import asyncio
# import time
# from datetime import datetime, timezone
# import json # 追加

# # from agents import Agent, function_tool # OpenAI SDK のインポートを削除
# from .monono_agent.base_agent import BaseAgent # 新しいBaseAgentをインポート

# # --- ここからログ関連の追加 ---
# # SQLAlchemyセッションとモデルのインポート (実際のパスに合わせてください)
# # from sqlalchemy.orm import Session
# # from app.models.agent_call import AgentCall # 作成済みのモデル
# # from app.models.agent_log import AgentInteractionEvent # 作成済みのモデル

# # --- プレースホルダー: SQLAlchemyモデル定義 (実際のモデルは別ファイルにあると想定) ---
# # 以下は、AgentCall と AgentInteractionEvent の仮定義です。
# # 実際の運用では、 from ..models import AgentCall, AgentInteractionEvent のようにインポートしてください。
# class AgentCallPlaceholder: # Placeholder - 名前を AgentCall から変更して衝突回避
#     def __init__(self, **kwargs): self.__dict__.update(kwargs); self.id = uuid.uuid4()
#     def __repr__(self): return f"<AgentCallPlaceholder id={self.id}>"

# class AgentInteractionEventPlaceholder: # Placeholder - 名前を AgentInteractionEvent から変更して衝突回避
#     def __init__(self, **kwargs): self.__dict__.update(kwargs); self.id = uuid.uuid4()
#     def __repr__(self): return f"<AgentInteractionEventPlaceholder id={self.id}>"

# # --- プレースホルダー: DBセッション取得関数 ---
# def get_db_session_placeholder():
#     # print("TODO: Implement actual DB session acquisition")
#     return None # In a real scenario, this would return an SQLAlchemy Session

# # --- ログ保存ヘルパー関数 (スタブ) ---
# # これらは新しいTraceLoggerに置き換えられる想定なので、一旦そのまま残すが、最終的には削除またはTraceLogger経由に変更
# def _log_agent_call_start(
#     session_id: uuid.UUID,
#     agent_name: str,
#     model_name: str,
#     current_prompt: Optional[str] = None # プロンプト内容をログに残す場合
# ) -> Optional[AgentCallPlaceholder]: # Placeholderモデルを使用
#     """AgentCallレコードのロギングを開始（LLM呼び出し前）。"""
#     db = get_db_session_placeholder()
#     # if db is None: print("DB session not available for logging AgentCall start.")

#     call_data = {
#         "id": uuid.uuid4(), # Placeholder内でidを生成しているので合わせる
#         "session_id": session_id,
#         "agent_name": agent_name,
#         "model": model_name,
#         "prompt_tok": None, # LLM呼び出し後に更新
#         "completion_tok": None, # LLM呼び出し後に更新
#         "yen": None, # LLM呼び出し後に更新
#         "duration_ms": None, # LLM呼び出し後に更新
#         "created_at": datetime.now(timezone.utc),
#         # "prompt_content": current_prompt # 必要であればプロンプト自体も記録
#     }
#     print(f"[LOG STUB AgentCall START]: {call_data}")
#     return AgentCallPlaceholder(**call_data) # スタブなのでインスタンスを返すだけ


# def _log_agent_call_end(
#     agent_call_to_update: Optional[AgentCallPlaceholder], # Placeholderモデルを使用
#     prompt_tokens: int,
#     completion_tokens: int,
#     duration_ms: float,
#     # cost: float # yen
# ):
#     """AgentCallレコードを更新（LLM呼び出し後）。"""
#     db = get_db_session_placeholder()
#     if agent_call_to_update is None: print("[LOG STUB] AgentCall instance not provided for update."); return
#     cost_yen = (prompt_tokens / 1000 * 0.40) + (completion_tokens / 1000 * 1.60) # 仮: o4-mini相当
#     agent_call_to_update.prompt_tok = prompt_tokens
#     agent_call_to_update.completion_tok = completion_tokens
#     agent_call_to_update.duration_ms = int(duration_ms)
#     agent_call_to_update.yen = cost_yen
#     print(f"[LOG STUB AgentCall END]: Updated {agent_call_to_update.__dict__}")


# def _log_interaction_event(
#     session_id: uuid.UUID,
#     event_type: str,
#     agent_name: Optional[str] = None,
#     tool_name: Optional[str] = None,
#     content: Optional[str] = None,
#     structured_content: Optional[Dict[str, Any]] = None,
#     metadata: Optional[Dict[str, Any]] = None,
#     agent_call_id: Optional[uuid.UUID] = None,
#     parent_interaction_id: Optional[uuid.UUID] = None
# ) -> Optional[AgentInteractionEventPlaceholder]: # Placeholderモデルを使用
#     """AgentInteractionEventレコードをロギング。"""
#     db = get_db_session_placeholder()
#     event_data = {
#         "id": uuid.uuid4(), 
#         "session_id": session_id,
#         "timestamp": datetime.now(timezone.utc),
#         "event_type": event_type,
#         "agent_name": agent_name,
#         "tool_name": tool_name,
#         "content": content,
#         "structured_content": structured_content if structured_content else None,
#         "metadata": metadata if metadata else None,
#         "agent_call_id": agent_call_id,
#         "parent_interaction_id": parent_interaction_id
#     }
#     print(f"[LOG STUB InteractionEvent]: {event_data}")
#     return AgentInteractionEventPlaceholder(**event_data) 
# # --- ここまでログ関連の追加 ---

# # --- Pydanticモデル定義 ---

# class ChangeMapItem(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     op: str
#     start: int
#     end: int
#     text: str

# class PatchJSON(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     new_text: str
#     change_map: List[ChangeMapItem]

# class StreamingScoreJSONDelta(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     delta: Dict[str, Any]

# class StreamingScoreJSONFinal(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     score_table: Dict[str, Any] # 具体的なテーブル構造による
#     advice_md: str

# # Tool I/O Models (一部例)
# class GenerateDraftParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     user_msg: str
#     draft: str
#     depth: int = Field(default=2, ge=1, le=5, description="下書き生成時の深掘りレベル (1-5)。")

# class ToneStyleAdjustParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str
#     tone: Literal["casual", "polite", "neutral"]

# class EvaluateDraftParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str
#     rubric_id: str

# class IntrospectivePromptParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     profile: dict

# class IntrospectivePromptResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     questions: List[str]

# class InterviewQuestionGenParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     ps: str # Personal Statement
#     n: int = 10

# class InterviewQuestionGenResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     q_and_hints: List[Dict[str, str]] # 例: {"question": "...", "hint": "..."}

# class FetchPolicyParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     policy_id: str # ここは department_id や admission_policy_id を指すように変更検討

# class FetchPolicyResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     content: str

# class SearchReferenceParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     topic: str
#     limit: int = 3

# class SearchReferenceResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     papers: List[Any] # 論文情報による

# class WebSearchParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     query: str
#     n: int = 5

# class WebSearchResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     articles: List[Any] # 記事情報による

# class GrammarCheckParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str

# class GrammarCheckResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     issues: List[Any] # 問題点の詳細による

# class CulturalContextCheckParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str

# class ReadabilityScoreParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str

# class ReadabilityScoreResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     flesch: float
#     grade: float

# class PlagiarismCheckParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str

# class PlagiarismCheckResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     similarity: float
#     sources: List[str]
#     action: Literal["pass", "warn", "block"] # GuardAgentのレスポンスに合わせて追加

# class KeywordTagExtractorParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID
#     draft: str
#     top_n: int = 8

# class KeywordTagExtractorResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     keywords: List[str]

# class TokenGuardParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # review.md に合わせて UUID 型に変更
#     new_prompt_tok: int
#     new_completion_tok: int

# class TokenGuardResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     action: Literal["pass", "warn", "block"]

# class ApplyReflexionParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     session_id: uuid.UUID # ログ記録用のセッションID (型をUUIDに修正)

# class ApplyReflexionResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     reflection_md: str
#     next_actions: List[str]

# # DataService Utility Models
# class DiffVersionsParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     old_text: str
#     new_text: str
#     session_id: uuid.UUID # Adding session_id for consistency if logging is desired here too

# class SaveRevisionParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     draft_id: int # 実際は UUID かもしれないので、DBスキーマと整合性を確認
#     content: str
#     session_id: uuid.UUID # Adding session_id for consistency

# class SaveRevisionResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     version: str # または UUID

# class ListRevisionsParams(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     draft_id: int # UUID かもしれない
#     limit: int = 10
#     session_id: uuid.UUID # Adding session_id for consistency

# class ListRevisionsResponse(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     versions: List[Any] # バージョン情報の詳細による


# # --- エージェント定義 ---
# class DraftAgent(BaseAgent):
#     """下書きの生成、自己分析プロンプト、面接用質問の生成を担当するエージェント。(カスタム版)"""
#     def __init__(self):
#         draft_agent_instructions = """ユーザーの入力と自己分析に基づいて下書きを生成・洗練します。主要なプロンプトルール：「各段落に具体的な例を1つ追加する」。生成する下書きでは、マークダウンの見出し（# や ##）の変更や削除を行わないでください。深掘りレベルは1から5まで指定可能です。"""
#         tools_definitions = [
#             {
#                 "name": "generate_draft", 
#                 "function": self.generate_draft, 
#                 "description": "ユーザーの指示に基づいて下書きを生成または編集します。",
#                 "parameters_schema": GenerateDraftParams.model_json_schema()
#             },
#             {
#                 "name": "introspective_prompt", 
#                 "function": self.introspective_prompt,
#                 "description": "ユーザーの自己分析を促すための質問を生成します。",
#                 "parameters_schema": IntrospectivePromptParams.model_json_schema()
#             },
#             {
#                 "name": "interview_question_gen", 
#                 "function": self.interview_question_gen,
#                 "description": "ユーザーの志望理由書に基づいて面接用の質問とヒントを生成します。",
#                 "parameters_schema": InterviewQuestionGenParams.model_json_schema()
#             },
#         ]
#         super().__init__(
#             name="DraftAgent",
#             instructions=draft_agent_instructions,
#             tools=tools_definitions,
#             model="gpt-4o" 
#         )

#     async def generate_draft(self, params: GenerateDraftParams) -> PatchJSON:
#         session_id = params.session_id 
#         print(f"[{self.name}] generate_draft called. Session: {session_id}, User Msg: {params.user_msg[:50]}...")
        
#         # TODO: self.llm_adapter を使用したLLM呼び出しを実装
#         # messages_for_llm = self._preprocess_messages([
#         #     {"role": "user", "content": f"Draft content based on: {params.user_msg}, current draft: {params.draft}, depth: {params.depth}. Instructions: {self.instructions}"}
#         # ])
#         # raw_llm_response = await self.llm_adapter.chat(messages=messages_for_llm, model=self.model, stream=False) # stream=False for run-like behavior
#         # generated_text = self.llm_adapter.get_content_from_response(raw_llm_response)
        
#         await asyncio.sleep(0.1) # LLM呼び出しのシミュレーション
#         generated_text = f"Generated draft for '{params.user_msg}' (depth {params.depth}) by {self.name}. Original draft hint: {params.draft[:30]}..."
        
#         # TODO: PatchJSONのchange_mapを正しく生成するロジック (diffライブラリ等を使用)
#         result = PatchJSON(new_text=generated_text, change_map=[])
#         print(f"[{self.name}] generate_draft finished. Session: {session_id}. Result: {result.new_text[:50]}...")
#         return result

#     async def introspective_prompt(self, params: IntrospectivePromptParams) -> IntrospectivePromptResponse:
#         session_id = params.session_id
#         print(f"[{self.name}] introspective_prompt called. Session: {session_id}, Profile: {params.profile}")
#         # TODO: self.llm_adapter を使用したLLM呼び出しを実装
#         await asyncio.sleep(0.05)
#         questions = [f"What are your core values related to your profile (custom {self.name})?", f"Describe a past experience relevant to your profile (custom {self.name})."]
#         response = IntrospectivePromptResponse(questions=questions)
#         print(f"[{self.name}] introspective_prompt finished. Session: {session_id}.")
#         return response

#     async def interview_question_gen(self, params: InterviewQuestionGenParams) -> InterviewQuestionGenResponse:
#         session_id = params.session_id
#         print(f"[{self.name}] interview_question_gen called. Session: {session_id}, PS: {params.ps[:50]}...")
#         # TODO: self.llm_adapter を使用したLLM呼び出しを実装
#         await asyncio.sleep(0.07)
#         q_and_hints = [{"question": f"Can you elaborate on your PS for {self.name} (custom)?", "hint": f"Use STAR method, focusing on aspect X (custom {self.name})."}]
#         response = InterviewQuestionGenResponse(q_and_hints=q_and_hints)
#         print(f"[{self.name}] interview_question_gen finished. Session: {session_id}.")
#         return response

# class StyleAgent(BaseAgent):
#     def __init__(self):
#         style_agent_instructions = """トーン調整（casual/polite/neutral）、敬体整合、文法チェック、スタイル、可読性、キーワード抽出、異文化不適切表現の検出を行います。(カスタム版)"""
#         tools_definitions = [
#             {
#                 "name": "tone_style_adjust", 
#                 "function": self.tone_style_adjust, 
#                 "description": "指定されたトーン（casual, polite, neutral）に基づいてドラフトのトーンを調整します。",
#                 "parameters_schema": ToneStyleAdjustParams.model_json_schema()
#             },
#             {
#                 "name": "grammar_check", 
#                 "function": self.grammar_check, 
#                 "description": "ドラフトの文法およびスペルをチェックし、問題点を報告します。",
#                 "parameters_schema": GrammarCheckParams.model_json_schema()
#             },
#             {
#                 "name": "cultural_context_check", 
#                 "function": self.cultural_context_check, 
#                 "description": "ドラフトが異文化間で不適切な表現を含んでいないかチェックします。",
#                 "parameters_schema": CulturalContextCheckParams.model_json_schema()
#             },
#             {
#                 "name": "readability_score", 
#                 "function": self.readability_score, 
#                 "description": "ドラフトの可読性スコア（フレッシュ指数など）を計算します。",
#                 "parameters_schema": ReadabilityScoreParams.model_json_schema()
#             },
#             {
#                 "name": "keyword_tag_extractor", 
#                 "function": self.keyword_tag_extractor, 
#                 "description": "ドラフトから主要なキーワードやタグを抽出します。",
#                 "parameters_schema": KeywordTagExtractorParams.model_json_schema()
#             }
#         ]
#         super().__init__(
#             name="StyleAgent",
#             instructions=style_agent_instructions,
#             tools=tools_definitions, 
#             model="gpt-4o"
#         )

#     async def tone_style_adjust(self, params: ToneStyleAdjustParams) -> PatchJSON:
#         print(f"[{self.name}] tone_style_adjust called. Session: {params.session_id}. Tone: {params.tone}")
#         # TODO: self.llm_adapter を使用したLLM呼び出しを実装
#         await asyncio.sleep(0.1)
#         # TODO: PatchJSONのchange_mapを正しく生成するロジック
#         return PatchJSON(new_text=f"Adjusted text by {self.name} to {params.tone} for draft starting with: {params.draft[:30]}...", change_map=[])

#     async def grammar_check(self, params: GrammarCheckParams) -> GrammarCheckResponse:
#         print(f"[{self.name}] grammar_check called. Session: {params.session_id}. Draft: {params.draft[:30]}...")
#         # TODO: self.llm_adapter を使用したLLM呼び出し/外部ライブラリ連携を実装
#         await asyncio.sleep(0.05)
#         return GrammarCheckResponse(issues=[{"message": f"Grammar issue found by {self.name} (custom StyleAgent)"}])

#     async def cultural_context_check(self, params: CulturalContextCheckParams) -> PatchJSON:
#         print(f"[{self.name}] cultural_context_check called. Session: {params.session_id}. Draft: {params.draft[:30]}...")
#         # TODO: self.llm_adapter を使用したLLM呼び出しを実装
#         await asyncio.sleep(0.1)
#         # TODO: PatchJSONのchange_mapを正しく生成するロジック
#         return PatchJSON(new_text=f"Culturally checked text by {self.name} for draft starting with: {params.draft[:30]}...", change_map=[])

#     async def readability_score(self, params: ReadabilityScoreParams) -> ReadabilityScoreResponse:
#         print(f"[{self.name}] readability_score called. Session: {params.session_id}. Draft: {params.draft[:30]}...")
#         # TODO: 実際の可読性計算ロジックを実装 (例: textstat ライブラリ)
#         await asyncio.sleep(0.02)
#         return ReadabilityScoreResponse(flesch=70.0, grade=7.0) # 固定値を返すスタブ

#     async def keyword_tag_extractor(self, params: KeywordTagExtractorParams) -> KeywordTagExtractorResponse:
#         print(f"[{self.name}] keyword_tag_extractor called. Session: {params.session_id}. TopN: {params.top_n}. Draft: {params.draft[:30]}...")
#         # TODO: self.llm_adapter を使用したLLM呼び出し/キーワード抽出ロジックを実装
#         await asyncio.sleep(0.08)
#         return KeywordTagExtractorResponse(keywords=[f"custom_keyword_by_{self.name}", f"tag_for_draft_len_{len(params.draft)}"])

# class RefAgent(BaseAgent):
#     def __init__(self):
#         ref_agent_instructions = """学校ポリシー全文の取得、学術論文のDOI取得、最新ニュースの要約など、参照情報を取得・生成します。(カスタム版)"""
#         tools_definitions = [
#             {
#                 "name": "fetch_policy",
#                 "function": self.fetch_policy,
#                 "description": "指定されたIDに基づいて学校のポリシー全文を取得します。",
#                 "parameters_schema": FetchPolicyParams.model_json_schema()
#             },
#             {
#                 "name": "search_reference",
#                 "function": self.search_reference,
#                 "description": "指定されたトピックに関連する学術論文を検索し、情報を返します。",
#                 "parameters_schema": SearchReferenceParams.model_json_schema()
#             },
#             {
#                 "name": "web_search",
#                 "function": self.web_search,
#                 "description": "指定されたクエリでウェブ検索を実行し、結果の要約を返します。",
#                 "parameters_schema": WebSearchParams.model_json_schema()
#             }
#         ]
#         super().__init__(
#             name="RefAgent",
#             instructions=ref_agent_instructions,
#             tools=tools_definitions,
#             model="gpt-4o"
#         )

#     async def fetch_policy(self, params: FetchPolicyParams) -> FetchPolicyResponse:
#         print(f"[{self.name}] fetch_policy called. Session: {params.session_id}. Policy ID: {params.policy_id}")
#         # TODO: self.llm_adapter を使用したLLM呼び出し、または外部API/DBアクセスを実装
#         await asyncio.sleep(0.1)
#         return FetchPolicyResponse(content=f"Policy content for {params.policy_id} from {self.name}. Searched at {datetime.now(timezone.utc).isoformat()}")

#     async def search_reference(self, params: SearchReferenceParams) -> SearchReferenceResponse:
#         print(f"[{self.name}] search_reference called. Session: {params.session_id}. Topic: {params.topic}, Limit: {params.limit}")
#         # TODO: self.llm_adapter を使用したLLM呼び出し、またはOpenAlex等の外部API連携を実装
#         await asyncio.sleep(0.15)
#         return SearchReferenceResponse(papers=[{"title": f"Paper on '{params.topic}' by {self.name}", "doi": f"10.xxxx/example.paper.{uuid.uuid4().hex[:4]}"} for _ in range(params.limit)])

#     async def web_search(self, params: WebSearchParams) -> WebSearchResponse:
#         print(f"[{self.name}] web_search called. Session: {params.session_id}. Query: '{params.query}', N: {params.n}")
#         # TODO: self.llm_adapter を使用したLLM呼び出し、またはBing Search API等の外部API連携を実装
#         await asyncio.sleep(0.12)
#         return WebSearchResponse(articles=[{"title": f"Web result for '{params.query}' from {self.name} ({i+1}/{params.n})", "snippet": f"Snippet for '{params.query}'..."} for i in range(params.n)])

# class GuardAgent(BaseAgent):
#     def __init__(self):
#         guard_agent_instructions = """盗用チェックとトークン使用量を管理します。(カスタム版)
#         - `plagiarism_check`: 指定されたドラフトの盗用をチェックし、類似度と参照元（もしあれば）を返します。
#         - `token_guard`: セッションの累積トークン使用量と新規リクエストのトークン数に基づいて、処理を許可(pass)、警告(warn)、またはブロック(block)します。"""
#         tools_definitions = [
#             {
#                 "name": "plagiarism_check",
#                 "function": self.plagiarism_check,
#                 "description": "指定されたドラフトの盗用をチェックし、類似度、参照元、およびアクション（pass/warn/block）を返します。",
#                 "parameters_schema": PlagiarismCheckParams.model_json_schema()
#             },
#             {
#                 "name": "token_guard",
#                 "function": self.token_guard,
#                 "description": "セッションのトークン使用量をチェックし、処理を許可するかどうかを決定します。",
#                 "parameters_schema": TokenGuardParams.model_json_schema()
#             }
#         ]
#         super().__init__(
#             name="GuardAgent",
#             instructions=guard_agent_instructions,
#             tools=tools_definitions,
#             model="gpt-4o" # ルールベースの場合はモデル不要かもしれないが、一旦設定
#         )

#     async def plagiarism_check(self, params: PlagiarismCheckParams) -> PlagiarismCheckResponse:
#         session_id = params.session_id
#         draft_preview = params.draft[:50]
#         print(f"[{self.name}] plagiarism_check called. Session: {session_id}. Draft preview: '{draft_preview}...'")
#         # TODO: 実際の盗用チェックロジックを実装 (例: Turnitin API連携、またはn-gram比較など)
#         await asyncio.sleep(0.1) # 外部API呼び出しのシミュレーション
        
#         # 仮のロジック
#         similarity = 0.15 # 仮の類似度
#         sources = []
#         action: Literal["pass", "warn", "block"] = "pass"
#         if "example" in params.draft.lower(): # 簡単なルールでテスト
#             similarity = 0.30
#             sources = ["http://example.com/source1"]
#             action = "warn"
#         if "forbidden phrase" in params.draft.lower():
#             similarity = 0.55
#             sources.append("http://example.com/source2")
#             action = "block"
            
#         print(f"[{self.name}] Plagiarism check for session {session_id}: Similarity={similarity}, Action={action}")
#         return PlagiarismCheckResponse(similarity=similarity, sources=sources, action=action)
    
#     async def token_guard(self, params: TokenGuardParams) -> TokenGuardResponse:
#         session_id = params.session_id
#         print(f"[{self.name}] token_guard called. Session: {session_id}. New Prompt Tokens: {params.new_prompt_tok}, New Completion Tokens: {params.new_completion_tok}")
        
#         # TODO: Redis等と連携した実際のトークンカウント管理ロジックを実装 (AgentSDK.md参照)
#         # current_total_tokens = await self._get_current_session_tokens(session_id)  # Redisなどから取得
#         # prospective_total_tokens = current_total_tokens + params.new_prompt_tok + params.new_completion_tok
        
#         # TOKEN_LIMIT_WARN = self.extra_cfg.get("token_limit_warn", 20000)
#         # TOKEN_LIMIT_BLOCK = self.extra_cfg.get("token_limit_block", 25000)
        
#         action: Literal["pass", "warn", "block"] = "pass" # デフォルトは許可
        
#         # 仮のロジック (スタブ)
#         # if prospective_total_tokens > TOKEN_LIMIT_BLOCK:
#         #     action = "block"
#         # elif prospective_total_tokens > TOKEN_LIMIT_WARN:
#         #     action = "warn"
        
#         # if action != "block":
#         #     await self._update_session_tokens(session_id, prospective_total_tokens) # Redisなどに保存
            
#         await asyncio.sleep(0.01) # 処理のシミュレーション
#         print(f"[{self.name}] Token guard action for session {session_id}: {action}")
#         return TokenGuardResponse(action=action)

# class EvalAgent(BaseAgent):
#     def __init__(self):
#         eval_agent_instructions = """ルーブリックを使用して下書きを評価し、具体的な改善コメントを生成します。(カスタム版)
#         - `evaluate_draft`: 指定されたルーブリックIDとドラフトに基づいて評価を行い、スコアテーブルとアドバイスをストリーミングで返します。
#         - `apply_reflexion`: 過去のインタラクションや評価結果に基づいて自己リフレクションを行い、改善のための次のアクションや考察を返します。"""
#         tools_definitions = [
#             {
#                 "name": "evaluate_draft",
#                 "function": self.evaluate_draft,
#                 "description": "指定されたルーブリックIDとドラフトに基づいて評価を行い、スコアテーブルとアドバイスをストリーミングで返します。",
#                 "parameters_schema": EvaluateDraftParams.model_json_schema()
#             },
#             {
#                 "name": "apply_reflexion",
#                 "function": self.apply_reflexion,
#                 "description": "過去のインタラクションや評価結果に基づいて自己リフレクションを行い、改善のための次のアクションや考察を返します。",
#                 "parameters_schema": ApplyReflexionParams.model_json_schema()
#             }
#         ]
#         super().__init__(
#             name="EvalAgent",
#             instructions=eval_agent_instructions,
#             tools=tools_definitions,
#             model="gpt-4o"
#         )

#     async def evaluate_draft(self, params: EvaluateDraftParams) -> StreamingScoreJSONFinal:
#         session_id = params.session_id
#         rubric_id = params.rubric_id
#         draft_preview = params.draft[:50]
#         print(f"[{self.name}] evaluate_draft called. Session: {session_id}. Rubric: {rubric_id}. Draft preview: '{draft_preview}...'")
        
#         # TODO: 実際のLLM呼び出しとストリーミング処理を実装。
#         # AgentSDK.md 5.7 によると、このメソッドはSSEチャンクを生成する (最終的に StreamingScoreJSONFinal を構築)。
#         # BaseAgent.stream メソッドのようなストリーミングロジックをここに実装するか、
#         # または self.llm_adapter を用いてストリーミング応答を取得し、それをチャンク化して返す必要がある。
#         # 現状は最終結果を一度に返すスタブ。
#         await asyncio.sleep(0.2) # LLM処理のシミュレーション
        
#         # ダミーのスコアテーブルとアドバイス
#         score_table = {
#             "clarity": 4,
#             "persuasiveness": 3,
#             "grammar": 5,
#             f"custom_rubric_{rubric_id}": 4.5
#         }
#         advice_md = f"### Evaluation for Rubric {rubric_id} by {self.name}\n\nGreat effort on the draft! Here are some points:\n- Consider adding more specific examples for section X.\n- The tone is generally good, but could be more persuasive in section Y."
        
#         print(f"[{self.name}] evaluate_draft finished for session {session_id}. Returning final score table and advice.")
#         return StreamingScoreJSONFinal(score_table=score_table, advice_md=advice_md)
    
#     async def apply_reflexion(self, params: ApplyReflexionParams) -> ApplyReflexionResponse:
#         session_id = params.session_id
#         print(f"[{self.name}] apply_reflexion called for session: {session_id}")
#         # TODO: 実際のLLM呼び出しを実装し、過去のログや評価を考慮したリフレクションを行う。
#         # (例: self.trace_logger から関連情報を取得し、プロンプトに含める)
#         await asyncio.sleep(0.1) # LLM処理のシミュレーション
        
#         reflection_md = f"## Reflexion by {self.name} (Session: {session_id})\n\nBased on recent interactions, the agent identified areas for improvement in prompt clarity and tool usage analysis. Future iterations will focus on refining these aspects."
#         next_actions = [
#             "Review agent logs for common error patterns.",
#             "Experiment with alternative prompting strategies for StyleAgent.",
#             f"Schedule a knowledge base update for RefAgent based on policy changes (session: {session_id})."
#         ]
#         print(f"[{self.name}] apply_reflexion finished for session {session_id}.")
#         return ApplyReflexionResponse(reflection_md=reflection_md, next_actions=next_actions)

# class Coordinator(BaseAgent):
#     def __init__(self) -> None:
#         coordinator_instructions = """
# ## エージェントキャラクター
# あなたは **「Master Conductor」**（マスター・コンダクター）。
# SmartAO Coach ライティング支援AIシステム全体の指揮者として、ユーザーからのリクエストを最適な専門エージェントに割り当て、処理フローを管理します。
# DataService関連のユーティリティは自身で直接ツールとして実行し、専門エージェントへの処理は `stream` メソッド内で直接呼び出すか、将来的にRouter経由で呼び出します。
# ツール実行前にはGuardAgentのtoken_guardを呼び出し、トークン制限を遵守します。
# ## モデル
# - プライマリ: "gpt-4o" (o4-mini相当)
# - フォールバック: "gpt-3.5-turbo" (o3-mini相当)
# ## 主要目標
# 1.  ユーザーリクエストを正確に理解し、適切な専門エージェントに処理を委任するか、DataServiceユーティリティを直接実行する。
# 2.  専門エージェントへの委任時には、そのエージェントが持つツール名と必要なパラメータを正確に指定する。
# 3.  GuardAgentを常駐ツールとして扱い、他のツール実行前に`token_guard`を先行実行し、セッションのトークン使用量が上限（例: 25kトークン）を超過しないか確認する。GuardAgentから "block" が返された場合は処理を中断しユーザーに通知する。
#         """.strip()

#         tools_definitions = [
#             {
#                 "name": "diff_versions", 
#                 "function": self.diff_versions, 
#                 "description": "二つのテキストバージョンの差分を計算し、PatchJSON形式で返します。",
#                 "parameters_schema": DiffVersionsParams.model_json_schema()
#             },
#             {
#                 "name": "save_revision", 
#                 "function": self.save_revision, 
#                 "description": "指定されたドラフトIDの新しいリビジョンとしてコンテンツを保存します。",
#                 "parameters_schema": SaveRevisionParams.model_json_schema()
#             },
#             {
#                 "name": "list_revisions", 
#                 "function": self.list_revisions,
#                 "description": "指定されたドラフトIDのリビジョンリストを取得します。",
#                 "parameters_schema": ListRevisionsParams.model_json_schema()
#             },
#         ]

#         super().__init__(
#             name="Coordinator",
#             instructions=coordinator_instructions,
#             tools=tools_definitions, # DataServiceユーティリティなどをToolとして登録
#             model="gpt-4o", # o4-mini相当
#             extra_cfg={"fallback_model": "gpt-3.5-turbo", "max_handoff_depth": 3, "token_limit_warn": 20000, "token_limit_block": 25000}
#         )
        
#         self.draft_agent = DraftAgent()
#         self.style_agent = StyleAgent()
#         self.ref_agent = RefAgent()
#         self.guard_agent = GuardAgent() 
#         self.eval_agent = EvalAgent()   

#         self._handoff_targets = { # Routerや直接呼び出しで使用する想定
#             "DraftAgent": self.draft_agent,
#             "StyleAgent": self.style_agent,
#             "RefAgent": self.ref_agent,
#             "GuardAgent": self.guard_agent,
#             "EvalAgent": self.eval_agent,
#         }
#         # self.router = SimpleRouter(self._handoff_targets) # 将来的なRouterの初期化例 (SimpleRouterは未定義)
#         # self.llm_adapter は BaseAgent内で初期化されるか、別途設定される想定 (現時点ではBaseAgentにLLMAdapterの初期化はない)

#     async def stream(self, messages: List[Dict[str, str]], session_id: Optional[uuid.UUID] = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
#         _seq_counter_coord = 0
#         def _create_coord_chunk(type: str, data: Optional[Dict] = None, agent_override:Optional[str]=None) -> Dict[str, Any]:
#             nonlocal _seq_counter_coord
#             _seq_counter_coord += 1
#             # agent_override があればそれを使い、なければ Coordinator の名前を使う
#             # また、data が None の場合は空の辞書を渡すように修正
#             return {
#                 "time": datetime.now(timezone.utc).isoformat(), 
#                 "agent": agent_override if agent_override else self.name, 
#                 "type": type, 
#                 "data": data if data is not None else {},
#                 "seq": _seq_counter_coord
#             }

#         print(f"[{self.name}] Coordinator stream orchestrating... Session: {session_id}, kwargs: {kwargs}")
#         # if self.trace_logger: self.trace_logger.trace("agent_start", {"agent_name": self.name, "session_id": str(session_id), "messages": messages, "kwargs": kwargs})

#         # --- Session ID の処理 ---
#         current_session_id: uuid.UUID
#         if isinstance(session_id, str):
#             try:
#                 current_session_id = uuid.UUID(session_id)
#             except ValueError:
#                 print(f"[{self.name} WARNING] Invalid session_id string: {session_id}. Generating new one.")
#                 current_session_id = uuid.uuid4()
#         elif isinstance(session_id, uuid.UUID):
#             current_session_id = session_id
#         else:
#             print(f"[{self.name} INFO] No session_id provided or invalid type. Generating new one.")
#             current_session_id = uuid.uuid4()
#         yield _create_coord_chunk("session_id", {"session_id": str(current_session_id)})

#         # --- 1. Routerで処理方針を決定 (スタブ) ---
#         target_agent_name: Optional[str] = None
#         tool_to_call: Optional[str] = None
#         params_for_tool_obj: Optional[BaseModel] = None # Pydanticモデルを期待
        
#         last_user_message = ""
#         if messages and messages[-1]["role"] == "user":
#             last_user_message = messages[-1]["content"].lower()

#         # kwargs から draft や rubric_id などを取得
#         current_draft = kwargs.get("draft", "")
#         current_rubric_id = kwargs.get("rubric_id", "default_rubric")
#         default_tone: Literal["casual", "polite", "neutral"] = "neutral"
#         current_tone = kwargs.get("tone", default_tone)
#         if current_tone not in ["casual", "polite", "neutral"]:
#             current_tone = default_tone
#         current_depth = kwargs.get("depth", 2)
#         current_policy_id = kwargs.get("policy_id", "general_policy_v1")
#         current_plagiarism_check_draft = kwargs.get("plagiarism_check_draft", current_draft) # 盗用チェック対象が指定されていなければ現在のドラフト

#         if not messages: # メッセージがない場合はエラーまたはデフォルトアクション
#             yield _create_coord_chunk("error", {"message": "No messages provided to Coordinator."})
#             return

#         # シンプルなキーワードベースのルーティングスタブ
#         if "style" in last_user_message or "トーン" in last_user_message or "スタイル" in last_user_message:
#             target_agent_name = "StyleAgent"
#             tool_to_call = "tone_style_adjust"
#             params_for_tool_obj = ToneStyleAdjustParams(session_id=current_session_id, draft=current_draft, tone=current_tone)
#         elif "eval" in last_user_message or "評価" in last_user_message or "点数" in last_user_message:
#             target_agent_name = "EvalAgent"
#             tool_to_call = "evaluate_draft"
#             params_for_tool_obj = EvaluateDraftParams(session_id=current_session_id, draft=current_draft, rubric_id=current_rubric_id)
#         elif "policy" in last_user_message or "ポリシー" in last_user_message:
#             target_agent_name = "RefAgent"
#             tool_to_call = "fetch_policy"
#             params_for_tool_obj = FetchPolicyParams(session_id=current_session_id, policy_id=current_policy_id) # policy_id はどこから？ kwargs想定
#         elif "plagiarism" in last_user_message or "盗用" in last_user_message:
#             target_agent_name = "GuardAgent"
#             tool_to_call = "plagiarism_check"
#             params_for_tool_obj = PlagiarismCheckParams(session_id=current_session_id, draft=current_plagiarism_check_draft)
#         elif "draft" in last_user_message or "下書き" in last_user_message or "肉付け" in last_user_message or "生成" in last_user_message:
#             target_agent_name = "DraftAgent"
#             tool_to_call = "generate_draft"
#             params_for_tool_obj = GenerateDraftParams(session_id=current_session_id, user_msg=messages[-1]["content"], draft=current_draft, depth=current_depth)
#         else: # デフォルトはDraftAgent
#             target_agent_name = "DraftAgent"
#             tool_to_call = "generate_draft"
#             params_for_tool_obj = GenerateDraftParams(session_id=current_session_id, user_msg=messages[-1]["content"], draft=current_draft, depth=current_depth)

#         if not target_agent_name or not tool_to_call or not params_for_tool_obj:
#             yield _create_coord_chunk("error", {"message": "Coordinator could not determine target agent or tool based on the input."})
#             return
            
#         yield _create_coord_chunk("routing_info", {"target_agent": target_agent_name, "tool_to_call": tool_to_call, "params_preview": params_for_tool_obj.model_dump_json(indent=2)[:200]+"..."})

#         # --- 2. GuardAgent.token_guard の先行実行 ---
#         token_guard_action = "pass" # デフォルトはパス
#         try:
#             # TODO: トークン消費量の見積もりをより正確に。
#             #       実際にLLMを呼び出す専門エージェントのプロンプトや、想定される応答長に基づいて計算する必要がある。
#             #       ここでは一旦固定値を使用。
#             estimated_prompt_tok = 100 
#             estimated_completion_tok = 200
#             if isinstance(params_for_tool_obj, GenerateDraftParams):
#                  estimated_prompt_tok += len(params_for_tool_obj.user_msg) // 3 # 文字数から大まかにトークン数を仮定
#                  estimated_prompt_tok += len(params_for_tool_obj.draft) // 3
#                  estimated_completion_tok = estimated_prompt_tok * 2 # 生成量はプロンプト量に比例すると仮定
            
#             guard_params = TokenGuardParams(
#                 session_id=current_session_id, 
#                 new_prompt_tok=estimated_prompt_tok, 
#                 new_completion_tok=estimated_completion_tok
#             )
#             # Coordinator自身がGuardAgentのツールを直接呼び出す
#             guard_response = await self.guard_agent.token_guard(guard_params)
#             token_guard_action = guard_response.action

#             if token_guard_action == "block":
#                 yield _create_coord_chunk("error", {"message": "Token limit would be exceeded. Request blocked by Coordinator pre-check.", "details": guard_response.model_dump()})
#                 # if self.trace_logger: self.trace_logger.trace("agent_end", {"agent_name": self.name, "session_id": str(current_session_id), "error": "Token block by pre-check"})
#                 return
#             elif token_guard_action == "warn":
#                  yield _create_coord_chunk("warning", {"message": "[Coordinator Notice: Token usage is high for this session.]", "details": guard_response.model_dump()})
        
#         except Exception as e:
#             print(f"[{self.name} ERROR] Token guard pre-check failed: {e}")
#             # import traceback; traceback.print_exc(); # デバッグ用
#             yield _create_coord_chunk("error", {"message": f"Token guard pre-check failed in Coordinator: {str(e)}"})
#             # if self.trace_logger: self.trace_logger.trace("agent_end", {"agent_name": self.name, "session_id": str(current_session_id), "error": f"Token guard pre-check fail: {e}"})
#             return

#         # --- 3. 専門エージェントのツール呼び出しと結果の処理 ---
#         if target_agent_name in self._handoff_targets:
#             target_agent_instance = self._handoff_targets[target_agent_name]
#             print(f"[{self.name}] Calling tool '{tool_to_call}' on agent '{target_agent_name}'. Session: {current_session_id}")
#             # if self.trace_logger: self.trace_logger.trace("specialized_agent_tool_start", {"coordinator": self.name, "target_agent": target_agent_name, "tool": tool_to_call, "session_id": str(current_session_id)})

#             if hasattr(target_agent_instance, tool_to_call):
#                 tool_method = getattr(target_agent_instance, tool_to_call)
#                 try:
#                     tool_result_obj = await tool_method(params_for_tool_obj)
                    
#                     # 専門エージェントのツール結果をSSEチャンクとして送信
#                     # ツール結果がPydanticモデルであることを期待
#                     if isinstance(tool_result_obj, BaseModel):
#                         yield _create_coord_chunk(
#                             type="tool_response", # または "final_result" など、ツールの性質に応じて変更検討
#                             data=tool_result_obj.model_dump(),
#                             agent_override=target_agent_name
#                         )
#                     else:
#                         # Pydanticモデルでない場合のフォールバック
#                         yield _create_coord_chunk(
#                             type="tool_response", 
#                             data={"raw_result": str(tool_result_obj)}, 
#                             agent_override=target_agent_name
#                         )
#                     # if self.trace_logger: self.trace_logger.trace("specialized_agent_tool_end", {"coordinator": self.name, "target_agent": target_agent_name, "tool": tool_to_call, "session_id": str(current_session_id), "result_type": type(tool_result_obj).__name__})

#                 except Exception as tool_exec_e:
#                     print(f"[{self.name} ERROR] Error executing tool '{tool_to_call}' on '{target_agent_name}': {tool_exec_e}")
#                     # import traceback; traceback.print_exc(); # デバッグ用
#                     yield _create_coord_chunk("error", {"message": f"Error executing tool {tool_to_call} on {target_agent_name}: {str(tool_exec_e)}"})
#                     # if self.trace_logger: self.trace_logger.trace("specialized_agent_tool_error", {"coordinator": self.name, "target_agent": target_agent_name, "tool": tool_to_call, "session_id": str(current_session_id), "error": str(tool_exec_e)})
#             else:
#                 yield _create_coord_chunk("error", {"message": f"Tool '{tool_to_call}' not found on agent '{target_agent_name}'."})
#         else:
#             # このケースはRouterスタブの設計上、通常は発生しないはず (必ずtarget_agent_nameが設定されるため)
#             # もしCoordinator自身がLLM応答を生成するようなパスが必要な場合は、BaseAgent.streamを呼び出すロジックをここに実装
#             yield _create_coord_chunk("error", {"message": f"Target agent '{target_agent_name}' not found in handoff_targets."})
        
#         # 最終的なUsage情報を送信 (現時点ではダミー)
#         # TODO: Coordinator呼び出し全体のトークン数や、専門エージェント呼び出しの合計トークン数を集計するロジックが必要
#         final_usage_data = {"prompt_tokens": estimated_prompt_tok + 10, "completion_tokens": estimated_completion_tok + 10, "total_tokens": estimated_prompt_tok + estimated_completion_tok + 20} # 仮の値
#         yield _create_coord_chunk("usage", final_usage_data)
#         print(f"[{self.name}] Coordinator stream finished. Session: {current_session_id}")
#         # if self.trace_logger: self.trace_logger.trace("agent_end", {"agent_name": self.name, "session_id": str(current_session_id), "final_usage": final_usage_data})

#     async def diff_versions(self, params: DiffVersionsParams) -> PatchJSON:
#         print(f"[{self.name}] diff_versions called. Session: {params.session_id}")
#         await asyncio.sleep(0.02)
#         return PatchJSON(new_text=f"Diff calculated by {self.name} for session {params.session_id}", change_map=[])

#     async def save_revision(self, params: SaveRevisionParams) -> SaveRevisionResponse:
#         print(f"[{self.name}] save_revision called. Session: {params.session_id}. Draft ID: {params.draft_id}")
#         await asyncio.sleep(0.02)
#         return SaveRevisionResponse(version=f"v_custom_{params.draft_id} by {self.name}")

#     async def list_revisions(self, params: ListRevisionsParams) -> ListRevisionsResponse:
#         print(f"[{self.name}] list_revisions called. Session: {params.session_id}. Draft ID: {params.draft_id}")
#         await asyncio.sleep(0.02)
#         return ListRevisionsResponse(versions=[f"v_custom_A by {self.name}", f"v_custom_B by {self.name}"])

# # 既存の call_xxx_agent メソッド群は新しいHandoff/Routerの仕組みに置き換えられるため削除またはコメントアウト
# # class CoordinatorAgent(Agent): # ...
# # @function_tool
# # async def call_draft_agent(self, tool_name: str, params: dict) -> Any:
# # ... (これらのメソッドはCoordinator.stream内部のロジックに統合される)

# # グローバルスコープにあった system_prompt_coordinator は Coordinator の __init__ に移動したため、
# # ここでの定義は不要か、あるいは読み込み方法を再検討。
# # system_prompt_coordinator = """...""" 

# # メインの実行部分やエージェントのインスタンス化はアプリケーションのエントリーポイントで行う
# # (例: FastAPIのルーター部分など)
# # async def main():
# #    coord = Coordinator()
# #    test_session_id = uuid.uuid4()
# #    async for chunk in coord.stream([{"role":"user", "content":"Hello, DraftAgent!"}], session_id=test_session_id):
# #        print(chunk)
# # if __name__ == "__main__":
# #    asyncio.run(main())