import pytest
import uuid
import json

from app.services.agents.monono_agent.components.planning_engine import PlanningEngine, Plan, SubTask

class DummyLLMAdapter:
    def __init__(self, response_content: str):
        self.response_content = response_content

    async def chat_completion(self, messages, stream=False, **kwargs):
        return {"content": self.response_content}

@pytest.mark.asyncio
async def test_create_plan_parses_valid_json():
    # Prepare a plan JSON with session_id and one task
    session_id = uuid.uuid4()
    plan_dict = {
        "session_id": str(session_id),
        "tasks": [
            {"id": "task1", "description": "Do something", "depends_on": []}
        ]
    }
    adapter = DummyLLMAdapter(json.dumps(plan_dict))
    engine = PlanningEngine(llm_adapter=adapter, model="test-model")
    messages = [{"role": "user", "content": "Test input"}]
    plan = await engine.create_plan(messages, session_id)
    assert isinstance(plan, Plan)
    assert plan.session_id == session_id
    assert len(plan.tasks) == 1
    task = plan.tasks[0]
    assert isinstance(task, SubTask)
    assert task.id == "task1"
    assert task.description == "Do something"
    assert task.depends_on == []

@pytest.mark.asyncio
async def test_create_plan_parses_json_with_noise():
    # Simulate LLM response with noise around JSON
    session_id = uuid.uuid4()
    inner = {
       "session_id": str(session_id),
       "tasks": [
           {"id": "t2", "description": "Another", "depends_on": ["task1"]}
       ]
    }
    noisy = "Noise before\n" + json.dumps(inner) + "\nNoise after"
    adapter = DummyLLMAdapter(noisy)
    engine = PlanningEngine(llm_adapter=adapter, model="test-model")
    messages = [{"role": "user", "content": "Another input"}]
    plan = await engine.create_plan(messages, session_id)
    assert plan.session_id == session_id
    assert len(plan.tasks) == 1
    t = plan.tasks[0]
    assert t.depends_on == ["task1"]

@pytest.mark.asyncio
async def test_execute_sub_task_invokes_agent_run():
    # Prepare a dummy subtask and dummy agent
    sub = SubTask(id="sub1", description="Task description", depends_on=[])
    class DummyAgent:
        def __init__(self):
            self.called = False
        async def run(self, messages, session_id=None):
            self.called = True
            return {"success": True, "messages": messages}
    dummy_agent = DummyAgent()
    adapter = DummyLLMAdapter("")  
    engine = PlanningEngine(llm_adapter=adapter, model="test-model")
    result = await engine.execute_sub_task(sub, dummy_agent, uuid.uuid4())
    assert dummy_agent.called
    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["messages"] == [{"role": "user", "content": "Task description"}] 