from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import uuid
import json
import re
import logging
import httpx
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from ..base_agent import BaseAgent # 循環インポートを避けるため TYPE_CHECKING を使用

class SubTask(BaseModel):
    id: str
    description: str
    depends_on: List[str] = []

class Plan(BaseModel):
    session_id: Optional[uuid.UUID] = None
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

        active_model = self.model
        if not active_model:
            logging.error("PlanningEngine: self.model is None or empty. This indicates a configuration issue.")
            raise ValueError("PlanningEngine model is not properly configured (None or empty).")

        logging.debug(f"PlanningEngine: Creating plan with model '{active_model}'. Messages: {[system_prompt, user_prompt]}")
        content = ""
        try:
            # A: JSON形式を強制する
            llm_response = await self.llm_adapter.chat_completion(
                messages=[system_prompt, user_prompt],
                stream=False,
                model=active_model,
                response_format={"type": "json_object"}
            )
            # C: tool_calls経由でJSONが返る場合に対応
            content = llm_response.get("content", "")
            if not content and "tool_calls" in llm_response and llm_response["tool_calls"]:
                first_call = llm_response["tool_calls"][0]
                args = first_call.get("function", {}).get("arguments")
                content = args if isinstance(args, str) else json.dumps(args)
            # B: まずは直接JSONとしてパースを試みる
            try:
                plan_dict = json.loads(content)
            except json.JSONDecodeError:
                # コードブロック内のJSONを最優先
                match_code_block = re.search(r"```json([\s\S]*?)```", content, re.IGNORECASE)
                if match_code_block:
                    json_str = match_code_block.group(1).strip()
                else:
                    # 貪欲マッチで最初の '{' から最後の '}' まで抽出
                    match_json = re.search(r"\{[\s\S]*\}", content)
                    if not match_json:
                        logging.error(f"PlanningEngine: No JSON found in LLM response. Content: '{content}'")
                        raise json.JSONDecodeError("No JSON object could be found", content, 0)
                    json_str = match_json.group(0)
                plan_dict = json.loads(json_str)

        except httpx.HTTPStatusError as e:
            logging.error(f"PlanningEngine: OpenAI API request failed with status {e.response.status_code} for model {active_model}.")
            error_body = "<Could not decode error response>"
            try:
                error_details = e.response.json()
                error_body = json.dumps(error_details)
                logging.error(f"PlanningEngine: OpenAI API error details (JSON): {error_details}")
            except json.JSONDecodeError:
                error_body = e.response.text
                logging.error(f"PlanningEngine: OpenAI API error response (text): {e.response.text}")
            raise RuntimeError(f"OpenAI API error during plan creation: {e.response.status_code} - {error_body}") from e
        except json.JSONDecodeError as e:
            logging.error(f"PlanningEngine: Failed to decode LLM response as JSON. Model: {active_model}. Content: '{content}'. Error: {e}")
            raise RuntimeError(f"Failed to decode plan from LLM response: {e}. Response content: {content}") from e
        except Exception as e:
            logging.error(f"PlanningEngine: Unexpected error during create_plan. Model: {active_model}. Error: {e}", exc_info=True)
            raise

        if "tasks" not in plan_dict or not isinstance(plan_dict["tasks"], list):
            logging.warning(f"PlanningEngine: LLM response for plan does not contain a valid 'tasks' list. Plan dict: {plan_dict}")
            plan_obj = Plan(session_id=session_id, tasks=[])
        else:
            # Convert task IDs and dependencies to strings to satisfy SubTask model
            raw_tasks = plan_dict.get("tasks", [])
            converted_tasks = []
            for t in raw_tasks:
                task_id = str(t.get("id"))
                description = t.get("description")
                depends_raw = t.get("depends_on", [])
                depends = [str(dep) for dep in depends_raw]
                converted_tasks.append({"id": task_id, "description": description, "depends_on": depends})
            plan_obj = Plan(tasks=converted_tasks)

        plan_obj.session_id = session_id
        return plan_obj

    async def execute_sub_task(self, sub_task: SubTask, agent: 'BaseAgent', session_id: Optional[uuid.UUID] = None) -> Any:
        messages = [{"role": "user", "content": sub_task.description}]
        logging.debug(f"PlanningEngine: Executing sub_task '{sub_task.id}': {sub_task.description[:50]}... with agent '{agent.name}'")
        # Avoid recursive planning by temporarily disabling the agent's planning_engine
        original_engine = getattr(agent, 'planning_engine', None)
        original_registry = getattr(agent, 'tool_registry', None)
        agent.planning_engine = None
        agent.tool_registry = None
        try:
            result = await agent.run(messages, session_id=session_id)
        finally:
            agent.planning_engine = original_engine
            agent.tool_registry = original_registry
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
        tasks_map = {t.id: t for t in plan.tasks}
        indegree = {t.id: len(t.depends_on) for t in plan.tasks}
        queue: List[str] = [tid for tid, deg in indegree.items() if deg == 0]
        results: Dict[str, Any] = {}

        execution_order = [] # 実行順序の記録用
        while queue:
            tid = queue.pop(0)
            execution_order.append(tid)
            sub = tasks_map[tid]
            logging.info(f"PlanningEngine: Executing subtask '{tid}' ({sub.description[:50]}...) as part of plan for session {session_id}")
            res = await self.execute_sub_task(sub, agent, session_id)
            results[tid] = res
            for t_dependent in plan.tasks: # t_dependent は Toplevel Plan のタスクオブジェクト
                if tid in t_dependent.depends_on:
                    indegree[t_dependent.id] -= 1
                    if indegree[t_dependent.id] == 0:
                        queue.append(t_dependent.id)

        # Check for cycles (if not all tasks were executed)
        if len(results) != len(plan.tasks):
            unexecuted_tasks = [t.id for t in plan.tasks if t.id not in results]
            logging.error(f"PlanningEngine: Cycle detected or some tasks failed to execute. Unexecuted tasks: {unexecuted_tasks}. Executed: {execution_order}")
            # ここでエラーを発生させるか、部分的な結果を返すか
            # raise RuntimeError(f"Cycle detected in plan or tasks failed. Unexecuted: {unexecuted_tasks}")

        return {"plan": plan, "results": results} 