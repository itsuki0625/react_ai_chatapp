from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import uuid
import json
import re
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from ..base_agent import BaseAgent # 循環インポートを避けるため TYPE_CHECKING を使用

class SubTask(BaseModel):
    id: str
    description: str
    depends_on: List[str] = []

class Plan(BaseModel):
    session_id: Optional[uuid.UUID]
    tasks: List[SubTask] = []

class PlanningEngine(BaseModel):
    llm_adapter: Any  # Adapter must have chat_completion method
    model: Optional[str] = None

    # Pydantic v2 style configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def create_plan(self, messages: List[Dict[str, str]], session_id: Optional[uuid.UUID] = None) -> Plan:
        system_prompt = {
            "role": "system",
            "content": (
                "You are a planning assistant that decomposes complex user requests into executable sub-tasks. "
                "Provide the plan as a JSON object with key 'tasks', where each task has 'id', 'description', and 'depends_on' (list of task IDs)."
            )
        }
        user_content = "\n".join(msg.get("content", "") for msg in messages)
        user_prompt = {
            "role": "user",
            "content": f"Based on the following messages, create a plan:\n{user_content}"
        }
        llm_response = await self.llm_adapter.chat_completion(
            messages=[system_prompt, user_prompt],
            stream=False,
            model=self.model or "",
            tool_choice="none"
        )
        content = llm_response.get("content", "")
        try:
            plan_dict = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise
            plan_dict = json.loads(match.group(0))
        plan = Plan(**plan_dict)
        return plan

    async def execute_sub_task(self, sub_task: SubTask, agent: 'BaseAgent', session_id: Optional[uuid.UUID] = None) -> Any:
        messages = [{"role": "user", "content": sub_task.description}]
        result = await agent.run(messages, session_id=session_id)
        return result

    async def execute_plan(
        self,
        messages: List[Dict[str, str]],
        agent: 'BaseAgent',
        session_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a plan and execute all subtasks in dependency order.
        Returns a dict with 'plan' (as Plan) and 'results' mapping subtask id to execution result.
        """
        plan = await self.create_plan(messages, session_id)
        # Build id->task map and indegree
        tasks_map = {t.id: t for t in plan.tasks}
        indegree = {t.id: len(t.depends_on) for t in plan.tasks}
        # Initialize queue with tasks without dependencies
        queue: List[str] = [tid for tid, deg in indegree.items() if deg == 0]
        results: Dict[str, Any] = {}
        # Execute tasks in topological order
        while queue:
            tid = queue.pop(0)
            sub = tasks_map[tid]
            # Execute subtask
            res = await self.execute_sub_task(sub, agent, session_id)
            results[tid] = res
            # Decrement indegree of dependents
            for t in plan.tasks:
                if tid in t.depends_on:
                    indegree[t.id] -= 1
                    if indegree[t.id] == 0:
                        queue.append(t.id)
        return {"plan": plan, "results": results} 