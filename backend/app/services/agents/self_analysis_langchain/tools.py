from langchain.tools import Tool, StructuredTool
from langchain_core.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from app.services.agents.self_analysis_monono_agent.tools.notes import (
    note_store as note_store_fn,
    list_notes as list_notes_fn,
    get_summary as get_summary_fn,
)
from .markdown import render_markdown_timeline as render_timeline_fn

class AsyncNoteTool(BaseTool):
    name: str = "note_store"
    description: str = "自己分析セッションおよびステップのノートを保存するツール"
    
    async def _arun(self, session_id: str, step: str = "default", content: dict = None) -> str:
        if content is None:
            content = {}
        return await note_store_fn(session_id, step, content)
    
    def _run(self, session_id: str, step: str = "default", content: dict = None) -> str:
        raise NotImplementedError("This tool only supports async execution")

class AsyncListNotesTool(BaseTool):
    name: str = "list_notes"
    description: str = "自己分析セッションのノート一覧を取得するツール"
    
    async def _arun(self, session_id: str, step: Optional[str] = None) -> List[dict]:
        return await list_notes_fn(session_id, step)
    
    def _run(self, session_id: str, step: Optional[str] = None) -> List[dict]:
        raise NotImplementedError("This tool only supports async execution")

class AsyncGetSummaryTool(BaseTool):
    name: str = "get_summary"
    description: str = "自己分析セッションのサマリーを取得するツール"
    
    async def _arun(self, session_id: str) -> str:
        return await get_summary_fn(session_id)
    
    def _run(self, session_id: str) -> str:
        raise NotImplementedError("This tool only supports async execution")

class RenderTimelineInput(BaseModel):
    timeline_json: str = Field(description="Timeline JSON to render")

note_store = AsyncNoteTool()
list_notes = AsyncListNotesTool()
get_summary = AsyncGetSummaryTool()

render_markdown_timeline = StructuredTool.from_function(
    render_timeline_fn,
    name="render_markdown_timeline",
    description="履歴タイムラインのJSONをMarkdownの表に変換するツール",
    args_schema=RenderTimelineInput,
)
