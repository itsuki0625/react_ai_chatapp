# from __future__ import annotations
# import json
# import uuid # UUIDをインポート
# from typing import List, Dict, Any, Optional, AsyncIterator, Union

# import google.generativeai as genai
# from google.generativeai.types.content_types import Part, FunctionCall
# from google.generativeai.types.generation_types import GenerateContentResponse, GenerationConfig
# from google.generativeai.types.helper_types import FunctionDeclaration, ToolConfig
# from google.generativeai.types.prompt_feedback_types import PromptFeedback

# # from google.api_core.exceptions import GoogleAPIError # エラーハンドリング用

# from .base_llm_adapter import BaseLLMAdapter

# # プロジェクト共通のエラーにマップすることも検討
# # from app.core.errors import LLMCommunicationError, LLMAuthenticationError, LLMRateLimitError

# class GoogleGeminiAdapter(BaseLLMAdapter):
#     """
#     Google Gemini API との通信を行うアダプター。
#     """

#     def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
#         super().__init__(model_name, api_key, base_url, **kwargs)
        
#         if not self.api_key:
#             raise ValueError("Google Gemini API key is required.")
        
#         try:
#             genai.configure(api_key=self.api_key)
#             system_instruction_content = kwargs.get("system_instruction")
            
#             # system_instructionが文字列で提供された場合、GeminiのSystemInstruction型に変換
#             system_instruction_for_model = None
#             if isinstance(system_instruction_content, str):
#                 system_instruction_for_model = genai.types.Content(role="system", parts=[genai.types.Part(text=system_instruction_content)])
#             elif isinstance(system_instruction_content, dict) and system_instruction_content.get('role') == 'system': # 既にContent形式の場合
#                 system_instruction_for_model = genai.types.Content(**system_instruction_content)

#             self.model = genai.GenerativeModel(
#                 model_name=self.model_name,
#                 system_instruction=system_instruction_for_model # ここで設定
#             )
#         except Exception as e:
#             print(f"[GoogleGeminiAdapter] Failed to initialize Google Gemini client: {e}")
#             # raise LLMInitializationError(f"Failed to initialize Google Gemini client: {e}") from e
#             raise

#     async def chat_completion(
#         self,
#         messages: List[Dict[str, Any]],
#         stream: bool = False,
#         tools: Optional[List[Dict[str, Any]]] = None, 
#         tool_choice: Optional[Union[str, Dict[str, Any]]] = None, 
#         temperature: Optional[float] = None,
#         max_tokens: Optional[int] = None,
#         top_p: Optional[float] = None,
#         top_k: Optional[int] = None,
#         **kwargs: Any
#     ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        
#         processed_messages = self._convert_messages_to_gemini_format(messages)
        
#         generation_config_dict = {}
#         if temperature is not None: generation_config_dict["temperature"] = temperature
#         if max_tokens is not None: generation_config_dict["max_output_tokens"] = max_tokens
#         if top_p is not None: generation_config_dict["top_p"] = top_p
#         if top_k is not None: generation_config_dict["top_k"] = top_k
#         if kwargs.get("stop_sequences"): generation_config_dict["stop_sequences"] = kwargs["stop_sequences"]
#         if kwargs.get("candidate_count") is not None: generation_config_dict["candidate_count"] = kwargs["candidate_count"]

#         gemini_generation_config = GeminiGenerationConfig(**generation_config_dict) if generation_config_dict else None

#         gemini_tools_list: Optional[List[GeminiTool]] = None
#         if tools:
#             # BaseAdapterのツール形式からGeminiのFunctionDeclarationリストに変換
#             function_declarations = []
#             for tool_def in tools:
#                 if tool_def.get("type") == "function" and isinstance(tool_def.get("function"), dict):
#                     func_data = tool_def["function"]
#                     # GeminiのパラメータスキーマはOpenAPIスキーマオブジェクト
#                     # parameters の型チェックと変換を厳密に行う必要がある
#                     parameters_schema = func_data.get("parameters")
#                     if not (isinstance(parameters_schema, dict) and parameters_schema.get("type") == "object" and isinstance(parameters_schema.get("properties"), dict)):
#                         # print(f"[GoogleGeminiAdapter] Warning: Tool '{func_data.get('name')}' has invalid parameters schema. Skipping. Schema: {parameters_schema}")
#                         # parameters_schema = {"type": "object", "properties": {}} # 空のスキーマとして扱うか、エラーにする
#                         # FunctionDeclarationにはnameが必須
#                          if func_data.get("name"):
#                             function_declarations.append(
#                                 GeminiFunctionDeclaration(
#                                     name=func_data["name"],
#                                     description=func_data.get("description",""),
#                                     parameters=None # スキーマが無効な場合はNone
#                                 )
#                             )
#                     else:
#                         if func_data.get("name"):
#                             function_declarations.append(
#                                 GeminiFunctionDeclaration(
#                                     name=func_data["name"],
#                                     description=func_data.get("description",""),
#                                     parameters=parameters_schema
#                                 )
#                             )
#             if function_declarations:
#                 gemini_tools_list = [GeminiTool(function_declarations=function_declarations)]


#         gemini_tool_config: Optional[GeminiToolConfig] = None
#         if tool_choice:
#             if isinstance(tool_choice, str):
#                 mode_map = {"auto": "AUTO", "any": "ANY", "none": "NONE", "function": "ANY"} # "function" も ANYとして扱う
#                 gemini_mode_str = mode_map.get(tool_choice.lower())
#                 if gemini_mode_str:
#                     gemini_tool_config = GeminiToolConfig(function_calling_config={"mode": GeminiToolConfig.FunctionCallingConfig.Mode[gemini_mode_str]})
#             elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function" and isinstance(tool_choice.get("function"), dict):
#                  # 特定の関数名を指定する場合: {"type": "function", "function": {"name": "my_func"}}
#                  # Gemini形式: {"function_calling_config": {"mode": "ANY", "allowed_function_names": ["my_func"]}}
#                 func_name_to_allow = tool_choice["function"].get("name")
#                 if func_name_to_allow:
#                     gemini_tool_config = GeminiToolConfig(
#                         function_calling_config={
#                             "mode": "ANY", # ANY または AUTO
#                             "allowed_function_names": [func_name_to_allow]
#                         }
#                     )
#             elif isinstance(tool_choice, dict): # 既にGeminiのToolConfig形式であると仮定
#                  gemini_tool_config = GeminiToolConfig(**tool_choice)


#         # ツールがあり、tool_choiceが明示的にNONEでない場合、デフォルトでAUTOにする
#         if gemini_tools_list and (not gemini_tool_config or gemini_tool_config.function_calling_config.mode != GeminiToolConfig.FunctionCallingConfig.Mode.NONE):
#             if not gemini_tool_config: # tool_choiceが指定されていない
#                 gemini_tool_config = GeminiToolConfig(function_calling_config={"mode": "AUTO"})
#             # tool_choice が "ANY" や特定の関数指定の場合、それは尊重する。それ以外（例：無効な文字列）なら AUTO に。
#             elif gemini_tool_config.function_calling_config.mode not in [GeminiToolConfig.FunctionCallingConfig.Mode.ANY, GeminiToolConfig.FunctionCallingConfig.Mode.NONE]:
#                  gemini_tool_config.function_calling_config.mode = GeminiToolConfig.FunctionCallingConfig.Mode.AUTO
#         elif not gemini_tools_list and gemini_tool_config and gemini_tool_config.function_calling_config.mode != GeminiToolConfig.FunctionCallingConfig.Mode.NONE :
#             # ツールがないのに tool_choice が ANY などになっている場合は NONE に強制
#             # print("[GoogleGeminiAdapter] Warning: tool_choice implies tool use, but no tools are provided. Setting tool_config mode to NONE.")
#             gemini_tool_config.function_calling_config.mode = GeminiToolConfig.FunctionCallingConfig.Mode.NONE


#         safety_settings_val = kwargs.get("safety_settings")
#         request_options_val = kwargs.get("request_options")

#         try:
#             if stream:
#                 return self._stream_chat_completion(
#                     contents=processed_messages,
#                     generation_config=gemini_generation_config,
#                     tools=gemini_tools_list,
#                     tool_config=gemini_tool_config,
#                     safety_settings=safety_settings_val,
#                     request_options=request_options_val
#                 )
#             else:
#                 response: GenerateContentResponse = await self.model.generate_content_async(
#                     contents=processed_messages,
#                     generation_config=gemini_generation_config,
#                     tools=gemini_tools_list,
#                     tool_config=gemini_tool_config,
#                     request_options=request_options_val,
#                     safety_settings=safety_settings_val
#                 )
                
#                 if hasattr(response, 'usage_metadata') and response.usage_metadata:
#                     self._set_latest_usage({
#                         "prompt_tokens": response.usage_metadata.prompt_token_count,
#                         "completion_tokens": response.usage_metadata.candidates_token_count,
#                         "total_tokens": response.usage_metadata.total_token_count
#                     })
#                 else:
#                     self._set_latest_usage(None) 

#                 return self._parse_gemini_response_to_common_format(response)

#         except Exception as e: 
#             error_message = str(e)
#             error_code = "unknown"
#             # より具体的なエラー情報を取得する試み
#             if hasattr(e, 'message') and e.message: error_message = e.message
#             if hasattr(e, 'code') and e.code: error_code = e.code
#             elif hasattr(e, 'status_code') and e.status_code: error_code = e.status_code
#             elif hasattr(e, 'grpc_status_code'): error_code = f"grpc_{e.grpc_status_code}"

#             print(f"[GoogleGeminiAdapter] Google Gemini API error: {error_message} (Code: {error_code})")
#             if stream:
#                 raise # ストリーミング中のエラーは _stream_chat_completion でエラーチャンクを生成
#             return {"type": "error", "message": error_message, "code": error_code}

#     def _convert_messages_to_gemini_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         gemini_contents = []
#         for msg in messages:
#             role = msg.get("role", "user").lower()
            
#             if role == "system":
#                 # system_instructionはモデル初期化時に設定される想定なので、ここでは無視
#                 continue
#             elif role == "assistant":
#                 role = "model"
#             elif role == "tool":
#                 role = "function"
            
#             content_data = msg.get("content")
#             parts = []

#             if isinstance(content_data, str):
#                 if content_data.strip(): parts.append(Part(text=content_data))
#             elif isinstance(content_data, list): # マルチパートコンテンツ (OpenAI Vision形式など)
#                 for item in content_data:
#                     if item.get("type") == "text" and item.get("text","").strip():
#                         parts.append(Part(text=item["text"]))
#                     # TODO: 画像などのマルチモーダルパートの変換
#                     # elif item.get("type") == "image_url" and item.get("image_url",{}).get("url"):
#                     #    image_url = item["image_url"]["url"]
#                     #    # image_urlからデータを取得し、GeminiのPart形式 (inline_data) に変換する処理が必要
#                     #    # parts.append(Part(inline_data=...))
#                     #    pass

#             # アシスタントからのツール呼び出し指示 (OpenAI形式からの変換)
#             if role == "model" and msg.get("tool_calls"):
#                 for tc in msg["tool_calls"]:
#                     if tc.get("type") == "function" and isinstance(tc.get("function"), dict):
#                         func_info = tc["function"]
#                         try:
#                             # argumentsはJSON文字列のはずなのでパース
#                             arguments_dict = json.loads(func_info.get("arguments", "{}"))
#                         except (json.JSONDecodeError, TypeError):
#                             print(f"[GoogleGeminiAdapter] Warning: Could not parse tool_call arguments for '{func_info.get('name')}': {func_info.get('arguments')}. Using empty dict.")
#                             arguments_dict = {}
                        
#                         parts.append(Part(function_call=GeminiFunctionCall(name=func_info["name"], args=arguments_dict)))
            
#             # ツール実行結果 (role: function)
#             elif role == "function":
#                 tool_name = msg.get("name")
#                 tool_response_str = msg.get("content") # 通常はJSON文字列
                
#                 response_payload_dict = {}
#                 try:
#                     loaded_json = json.loads(tool_response_str)
#                     # Geminiは response が dict であることを期待
#                     if isinstance(loaded_json, dict):
#                         response_payload_dict = loaded_json
#                     else: # リストや単一の値なら "output" でラップ
#                         response_payload_dict = {"output": loaded_json}
#                 except (json.JSONDecodeError, TypeError):
#                     response_payload_dict = {"output": tool_response_str} # パース失敗時は文字列としてラップ
                
#                 if tool_name: # tool_nameがないとGemini側でエラーになる
#                     parts.append(Part(function_response=genai.types.FunctionResponse(name=tool_name, response=response_payload_dict)))
#                 else:
#                     print(f"[GoogleGeminiAdapter] Warning: Tool response for role 'function' is missing 'name'. Skipping part. Content: {tool_response_str[:50]}")


#             if parts:
#                 gemini_contents.append(genai.types.Content(role=role, parts=parts))
        
#         return gemini_contents

#     def _parse_gemini_response_to_common_format(self, response: GenerateContentResponse) -> Dict[str, Any]:
#         text_parts_list = []
#         tool_calls_list = []

#         if response.candidates:
#             for candidate_obj in response.candidates: # candidate_obj は genai.types.Candidate 型
#                 if candidate_obj.content and candidate_obj.content.parts:
#                     for part in candidate_obj.content.parts:
#                         if part.text:
#                             text_parts_list.append(part.text)
#                         if hasattr(part, 'function_call') and part.function_call:
#                             fc = part.function_call
#                             tool_calls_list.append({
#                                 "id": f"call_{fc.name}_{str(uuid.uuid4())[:8]}",
#                                 "type": "function",
#                                 "function": {"name": fc.name, "arguments": json.dumps(fc.args if fc.args is not None else {})}
#                             })
        
#         # finish_reason の取得と整形
#         finish_reason_val = "unknown"
#         if response.candidates and response.candidates[0].finish_reason:
#             finish_reason_name = FinishReason(response.candidates[0].finish_reason).name # Enum値を名前に変換
#             finish_reason_val = finish_reason_name.lower()

#         common_response = {
#             "role": "assistant",
#             "content": "".join(text_parts_list),
#             "finish_reason": finish_reason_val
#         }
#         if tool_calls_list:
#             common_response["tool_calls"] = tool_calls_list
        
#         # usage情報は self.get_latest_usage() で取得できるので、ここでは含めない
            
#         return common_response

#     async def _stream_chat_completion(self, **request_params: Any) -> AsyncIterator[Dict[str, Any]]:
#         try:
#             stream_response = await self.model.generate_content_async(stream=True, **request_params)
#             async for chunk in stream_response:
#                 # parse_llm_response_chunk はリストでチャンクを返す可能性がある
#                 parsed_chunks_list = self.parse_llm_response_chunk(chunk)
                
#                 for p_chunk in parsed_chunks_list:
#                     yield p_chunk
                
#                 if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
#                     usage_data = {
#                         "prompt_tokens": chunk.usage_metadata.prompt_token_count,
#                         "completion_tokens": chunk.usage_metadata.candidates_token_count,
#                         "total_tokens": chunk.usage_metadata.total_token_count
#                     }
#                     self._set_latest_usage(usage_data) 
#                     yield {"type": "usage", **usage_data}

#         except Exception as e:
#             error_message = str(e)
#             error_code = "unknown"
#             if hasattr(e, 'message') and e.message: error_message = e.message
#             if hasattr(e, 'code') and e.code: error_code = e.code
#             elif hasattr(e, 'status_code') and e.status_code: error_code = e.status_code
#             elif hasattr(e, 'grpc_status_code'): error_code = f"grpc_{e.grpc_status_code}"

#             print(f"[GoogleGeminiAdapter] Google Gemini API error during stream: {error_message} (Code: {error_code})")
#             yield {"type": "error", "message": error_message, "code": error_code}

#     def format_tool_call_response(
#         self,
#         tool_call_id: str, 
#         tool_name: str,    
#         result: Any
#     ) -> Dict[str, Any]:
#         response_payload_dict = {}
#         try:
#             if isinstance(result, str):
#                 loaded_json = json.loads(result)
#                 if isinstance(loaded_json, dict): response_payload_dict = loaded_json
#                 else: response_payload_dict = {"output": loaded_json}
#             elif isinstance(result, dict):
#                 response_payload_dict = result
#             elif isinstance(result, list): # リストの場合も "output" でラップ
#                 response_payload_dict = {"output": result}
#             else: # int, float, boolなど
#                 response_payload_dict = {"output": result}
#         except (json.JSONDecodeError, TypeError):
#              response_payload_dict = {"output": str(result)}

#         # Geminiに渡すメッセージ形式
#         return {
#             "role": "function", 
#             "parts": [
#                 {
#                     "function_response": {
#                         "name": tool_name,
#                         "response": response_payload_dict 
#                     }
#                 }
#             ]
#         }

#     def parse_llm_response_chunk(
#         self,
#         chunk: GenerateContentResponse,
#     ) -> List[Dict[str, Any]]:
#         chunks_to_yield: List[Dict[str, Any]] = []

#         if chunk.text:
#             chunks_to_yield.append({"type": "delta", "content": chunk.text})
        
#         if chunk.candidates:
#             for candidate_obj in chunk.candidates: # genai.types.Candidate オブジェクト
#                 if candidate_obj.content and candidate_obj.content.parts:
#                     for part in candidate_obj.content.parts:
#                         if hasattr(part, 'function_call') and part.function_call:
#                             fc: GeminiFunctionCall = part.function_call
#                             tool_call_id = f"call_{fc.name}_{str(uuid.uuid4())[:8]}"
                            
#                             arguments_json_str = json.dumps(fc.args if fc.args is not None else {})

#                             chunks_to_yield.append({
#                                 "type": "tool_call_start",
#                                 "id": tool_call_id,
#                                 "name": fc.name,
#                                 "input_so_far": arguments_json_str 
#                             })
#                             chunks_to_yield.append({
#                                 "type": "tool_call_end",
#                                 "id": tool_call_id,
#                                 "name": fc.name,
#                                 "arguments": arguments_json_str
#                             })
        
#         finish_reason_val: Optional[str] = None
#         if chunk.candidates and chunk.candidates[0].finish_reason:
#             finish_reason_name = FinishReason(chunk.candidates[0].finish_reason).name # Enum値を名前に変換
#             finish_reason_val = finish_reason_name.lower()
#             chunks_to_yield.append({"type": "meta", "finish_reason": finish_reason_val})
            
#             if finish_reason_val == "safety" and chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
#                 # prompt_feedback.block_reason も Enum のはずなので名前に変換
#                 block_reason_name = PromptFeedback.BlockReason(chunk.prompt_feedback.block_reason).name
#                 chunks_to_yield.append({
#                     "type": "meta", 
#                     "safety_block_reason": block_reason_name,
#                     "message": f"Content generation stopped due to safety reasons: {block_reason_name}"
#                 })
#             elif finish_reason_val == "recitation" and candidate_obj.citation_metadata:
#                  chunks_to_yield.append({
#                     "type": "meta",
#                     "citation_metadata": str(candidate_obj.citation_metadata.citation_sources) 
#                  })


#         if chunk.prompt_feedback and chunk.prompt_feedback.block_reason and not finish_reason_val:
#              block_reason_name = PromptFeedback.BlockReason(chunk.prompt_feedback.block_reason).name
#              chunks_to_yield.append({
#                  "type": "error", 
#                  "message": f"Prompt processing stopped due to: {block_reason_name}",
#                  "code": f"PROMPT_BLOCK_{block_reason_name}"
#              })
        
#         # usage情報は _stream_chat_completion で処理するため、ここでは含めない

#         return chunks_to_yield

#     async def close(self):
#         print("[GoogleGeminiAdapter] close() called. No specific client resources to close for google-generativeai by default.")
#         pass

# # 必要な型定義 (例)
# # class GeminiTool(TypedDict):
# #    function_declarations: List[FunctionDeclaration]

# # class FunctionDeclaration(TypedDict):
# #    name: str
# #    description: str
# #    parameters: Dict[str, Any] # JSON Schema 