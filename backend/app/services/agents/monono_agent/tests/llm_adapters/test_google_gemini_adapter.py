# import pytest
# import json
# import uuid
# from typing import Dict, Any, List, Optional

# # テスト対象のGoogleGeminiAdapterをインポート
# from app.services.agents.monono_agent.llm_adapters.google_gemini_adapter import GoogleGeminiAdapter
# # Geminiライブラリの型をインポート (モックデータ生成のため)
# from google.generativeai.types.content_types import Part, FunctionCall
# from google.generativeai.types.generation_types import GenerateContentResponse, GenerationConfig
# from google.generativeai.types.helper_types import FunctionDeclaration, ToolConfig
# from google.generativeai.types.prompt_feedback_types import PromptFeedback
# import google.generativeai as genai # genai.types.Content のためにインポート

# # --- モックデータの準備 ---

# def create_gemini_response_chunk(
#     text: Optional[str] = None, 
#     function_calls: Optional[List[GeminiFunctionCall]] = None,
#     finish_reason: Optional[FinishReason] = None, # 型ヒントを具体的に
#     prompt_feedback_block_reason: Optional[PromptFeedback.BlockReason] = None, # 型ヒントを具体的に
#     citation_metadata: Optional[genai.types.CitationMetadata] = None, # 型ヒントを具体的に
#     usage_metadata_dict: Optional[Dict[str, int]] = None
# ) -> GenerateContentResponse: # 戻り値の型ヒントはGenerateContentResponseのままで良い(モックのため)
#     """Gemini形式のストリーミングチャンク (GenerateContentResponse) を模倣するオブジェクトを生成するヘルパー関数"""
#     parts = []
#     if text:
#         parts.append(Part(text=text))
#     if function_calls:
#         for fc in function_calls:
#             parts.append(Part(function_call=fc))
    
#     current_content = None
#     if parts:
#         current_content = genai.types.Content(parts=parts, role="model")

#     current_candidates = [
#         genai.types.Candidate( # 明示的に genai.types.Candidate を使用
#             content=current_content, 
#             finish_reason=finish_reason,
#             citation_metadata=citation_metadata,
#             token_count = sum(usage_metadata_dict.values()) if usage_metadata_dict else 0,
#             # safety_ratings も必要に応じて genai.types.SafetyRating を使って生成
#         )
#     ]
    
#     current_prompt_feedback = None
#     if prompt_feedback_block_reason:
#         current_prompt_feedback = genai.types.PromptFeedback(block_reason=prompt_feedback_block_reason)

#     current_usage_metadata = None
#     if usage_metadata_dict:
#         current_usage_metadata = UsageMetadata(
#             prompt_token_count=usage_metadata_dict.get("prompt_token_count",0),
#             candidates_token_count=usage_metadata_dict.get("candidates_token_count",0),
#             total_token_count=usage_metadata_dict.get("total_token_count",0)
#         )

#     # GenerateContentResponseのインスタンス化は複雑なので、
#     # 必要な属性を持つシンプルなモックオブジェクトで代用する。
#     # parse_llm_response_chunk がアクセスするインターフェースを模倣する。
#     class MockGenerateContentResponse:
#         def __init__(self, text_content, candidates_list, prompt_feedback_obj, usage_metadata_obj):
#             self._text_content = text_content
#             self._candidates_list = candidates_list
#             self._prompt_feedback_obj = prompt_feedback_obj
#             self._usage_metadata_obj = usage_metadata_obj

#         @property
#         def text(self) -> Optional[str]:
#             # 実際のGenerateContentResponseでは、複数のパートのテキストが結合される
#             # ここでは、text引数で渡されたものを優先し、なければpartsから構築
#             if self._text_content:
#                 return self._text_content
#             if self._candidates_list and self._candidates_list[0].content:
#                 combined_text = "".join(p.text for p in self._candidates_list[0].content.parts if p.text)
#                 return combined_text if combined_text else None
#             return None

#         @property
#         def candidates(self) -> List[genai.types.Candidate]: # 型ヒントを修正
#             return self._candidates_list

#         @property
#         def prompt_feedback(self) -> Optional[genai.types.PromptFeedback]:
#             return self._prompt_feedback_obj
        
#         @property
#         def usage_metadata(self) -> Optional[UsageMetadata]:
#             return self._usage_metadata_obj

#     # ヘルパーのtext引数は、直接 .text プロパティに反映されるようにする
#     # function_calls などは candidates 経由で設定
#     return MockGenerateContentResponse(text, current_candidates, current_prompt_feedback, current_usage_metadata) # type: ignore


# # --- テストケース ---

# @pytest.fixture
# def gemini_adapter() -> GoogleGeminiAdapter:
#     """GoogleGeminiAdapterのインスタンスを生成するフィクスチャ"""
#     return GoogleGeminiAdapter(model_name="gemini-1.5-flash-test", api_key="fake_gemini_key")

# def test_parse_text_delta(gemini_adapter: GoogleGeminiAdapter):
#     """テキストデルタチャンクのパーステスト"""
#     raw_chunk = create_gemini_response_chunk(text="Hello Gemini!")
    
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 
    
#     assert parsed_chunks is not None
#     assert len(parsed_chunks) == 1
#     text_chunk = parsed_chunks[0]
#     assert text_chunk.get("type") == "delta"
#     assert text_chunk.get("content") == "Hello Gemini!"

# def test_parse_single_function_call(gemini_adapter: GoogleGeminiAdapter):
#     """単一のFunction Callチャンクのパーステスト"""
#     fc = GeminiFunctionCall(name="get_current_weather", args={"location": "Tokyo", "unit": "celsius"})
#     raw_chunk = create_gemini_response_chunk(function_calls=[fc])
    
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 
    
#     assert parsed_chunks is not None
#     assert len(parsed_chunks) == 2 # tool_call_start と tool_call_end

#     start_chunk = parsed_chunks[0]
#     end_chunk = parsed_chunks[1]

#     assert start_chunk.get("type") == "tool_call_start"
#     assert start_chunk.get("name") == "get_current_weather"
#     assert start_chunk.get("id") is not None
#     expected_args_str = json.dumps({"location": "Tokyo", "unit": "celsius"})
#     assert start_chunk.get("input_so_far") == expected_args_str

#     assert end_chunk.get("type") == "tool_call_end"
#     assert end_chunk.get("name") == "get_current_weather"
#     assert end_chunk.get("id") == start_chunk.get("id")
#     assert end_chunk.get("arguments") == expected_args_str

# def test_parse_multiple_function_calls(gemini_adapter: GoogleGeminiAdapter):
#     """複数のFunction Callが1つのチャンクに含まれる場合のパーステスト"""
#     fc1 = GeminiFunctionCall(name="tool_A", args={"param1": "valueA"})
#     fc2 = GeminiFunctionCall(name="tool_B", args={"param2": 123})
#     raw_chunk = create_gemini_response_chunk(function_calls=[fc1, fc2])

#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 

#     assert parsed_chunks is not None
#     assert len(parsed_chunks) == 4 

#     assert parsed_chunks[0].get("type") == "tool_call_start"
#     assert parsed_chunks[0].get("name") == "tool_A"
#     assert parsed_chunks[1].get("type") == "tool_call_end"
#     assert parsed_chunks[1].get("name") == "tool_A"
#     assert parsed_chunks[0].get("id") == parsed_chunks[1].get("id")
#     assert parsed_chunks[1].get("arguments") == json.dumps({"param1": "valueA"})

#     assert parsed_chunks[2].get("type") == "tool_call_start"
#     assert parsed_chunks[2].get("name") == "tool_B"
#     assert parsed_chunks[3].get("type") == "tool_call_end"
#     assert parsed_chunks[3].get("name") == "tool_B"
#     assert parsed_chunks[2].get("id") == parsed_chunks[3].get("id")
#     assert parsed_chunks[3].get("arguments") == json.dumps({"param2": 123})

# def test_parse_text_and_function_call(gemini_adapter: GoogleGeminiAdapter):
#     """テキストとFunction Callが混在するチャンクのパーステスト"""
#     # このテストは、chunk.text と chunk.candidates[].content.parts の両方をアダプタが考慮することを意図
#     text_content = "Okay, I will search for that."
#     fc = GeminiFunctionCall(name="do_search", args={"term": "adapters"})
#     raw_chunk = create_gemini_response_chunk(text=text_content, function_calls=[fc])
        
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk)

#     assert len(parsed_chunks) == 3 
#     assert parsed_chunks[0].get("type") == "delta"
#     assert parsed_chunks[0].get("content") == text_content
#     assert parsed_chunks[1].get("type") == "tool_call_start"
#     assert parsed_chunks[1].get("name") == "do_search"
#     assert parsed_chunks[2].get("type") == "tool_call_end"
#     assert parsed_chunks[2].get("name") == "do_search"


# def test_parse_finish_reason_stop(gemini_adapter: GoogleGeminiAdapter):
#     """finish_reason 'STOP' のパーステスト"""
#     raw_chunk = create_gemini_response_chunk(finish_reason=genai.types.FinishReason.STOP)
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 
    
#     assert parsed_chunks is not None
#     meta_chunk_found = any(c.get("type") == "meta" and c.get("finish_reason") == "stop" for c in parsed_chunks)
#     assert meta_chunk_found

# def test_parse_finish_reason_safety(gemini_adapter: GoogleGeminiAdapter):
#     """finish_reason 'SAFETY' (ブロック理由あり) のパーステスト"""
#     raw_chunk = create_gemini_response_chunk(
#         finish_reason=genai.types.FinishReason.SAFETY,
#         prompt_feedback_block_reason=genai.types.PromptFeedback.BlockReason.HARM_CATEGORY_HARASSMENT
#     )
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 
    
#     assert parsed_chunks is not None
#     meta_chunk_found = False
#     safety_message_found = False
#     for c in parsed_chunks:
#         if c.get("type") == "meta" and c.get("finish_reason") == "safety":
#             meta_chunk_found = True
#         if c.get("type") == "meta" and "safety_block_reason" in c:
#             safety_message_found = True
#             assert c.get("safety_block_reason") == "HARM_CATEGORY_HARASSMENT" 
#             assert "message" in c

#     assert meta_chunk_found
#     assert safety_message_found

# def test_parse_prompt_feedback_block_direct(gemini_adapter: GoogleGeminiAdapter):
#     """finish_reasonなしでprompt_feedbackによるブロックが発生した場合のパーステスト"""
#     raw_chunk = create_gemini_response_chunk(
#         prompt_feedback_block_reason=genai.types.PromptFeedback.BlockReason.SAFETY 
#     )
    
#     parsed_chunks = gemini_adapter.parse_llm_response_chunk(raw_chunk) 
    
#     assert parsed_chunks is not None
#     error_chunk_found = False
#     for c in parsed_chunks:
#         if c.get("type") == "error" and c.get("code") == "PROMPT_BLOCK_SAFETY": 
#             error_chunk_found = True
#             assert "message" in c
#     assert error_chunk_found


# # TODO:
# # - _convert_messages_to_gemini_format のテスト (特にtool_calls, tool_responseの変換)
# # - format_tool_call_response のテスト
# # - _stream_chat_completion メソッド自体のテスト (モックした model.generate_content_async を使用)
# # - chat_completion メソッド (非ストリーミング) のテスト (_parse_gemini_response_to_common_format を含む)
# # - usage_metadata が含まれるチャンクのテスト (create_gemini_response_chunk ヘルパーと連携)
# # - citation_metadata が含まれるチャンクのテスト
