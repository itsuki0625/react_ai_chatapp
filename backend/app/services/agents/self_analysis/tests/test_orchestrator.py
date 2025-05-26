import pytest
import uuid
from app.services.agents.self_analysis.orchestrator import SelfAnalysisOrchestrator, get_progress, AGENTS, STEP_FLOW

class DummyAgent:
    def __init__(self):
        self.call_count = 0

    async def run(self, messages, session_id):
        self.call_count += 1
        return {
            "additional": {},
            "final_notes": f"notes{self.call_count}",
            "next_step": "FIN",
            "user_visible": f"visible{self.call_count}"
        }

async def fake_note_store(*args, **kwargs):
    pass

async def fake_reflection_store(*args, **kwargs):
    pass

@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # get_progressと外部依存をモンキーパッチ
    async def fake_get_progress(session_id):
        return STEP_FLOW[0]
    monkeypatch.setattr('app.services.agents.self_analysis.orchestrator.get_progress', fake_get_progress)
    monkeypatch.setattr('app.services.agents.self_analysis.orchestrator.note_store', fake_note_store)
    monkeypatch.setattr('app.services.agents.self_analysis.orchestrator.reflection_store', fake_reflection_store)
    dummy = DummyAgent()
    AGENTS[STEP_FLOW[0]] = dummy
    return dummy

@pytest.mark.asyncio
async def test_orchestrator_basic(patch_dependencies):
    orchestrator = SelfAnalysisOrchestrator()
    session_id = str(uuid.uuid4())
    result = await orchestrator.run(session_id, "テスト入力")
    assert result == "visible1"
    # 再度実行してDummyAgentの挙動を確認
    result2 = await orchestrator.run(session_id, "別の入力")
    assert result2 == "visible2"

@pytest.mark.asyncio
async def test_orchestrator_retry(patch_dependencies, monkeypatch):
    # 1回目は retry 指示、2回目は完了
    calls = []
    async def fake_reflection_store(session_id, step, kind, reason):
        calls.append((session_id, step, kind, reason))
    monkeypatch.setattr('app.services.agents.self_analysis.orchestrator.reflection_store', fake_reflection_store)

    class RetryDummy:
        def __init__(self):
            self.call_count = 0
        async def run(self, messages, session_id):
            self.call_count += 1
            if self.call_count == 1:
                return {
                    'additional': {'reflexion_status': 'retry', 'reason': 'need_retry', 'next_action': 'retry_input'},
                    'final_notes': 'notes1', 'next_step': STEP_FLOW[0], 'user_visible': 'visible1'
                }
            return {
                'additional': {}, 'final_notes': 'notes2', 'next_step': 'FIN', 'user_visible': 'visible2'
            }
    dummy = RetryDummy()
    AGENTS[STEP_FLOW[0]] = dummy

    orchestrator = SelfAnalysisOrchestrator()
    session_id = str(uuid.uuid4())
    result = await orchestrator.run(session_id, '初回入力')
    assert result == 'visible2'
    # ツールエージェントは2回呼び出されている
    assert dummy.call_count == 2
    # reflection_store が2回呼ばれている（micro と macro）
    assert len(calls) == 2
    # 1回目はマイクロリフレクション
    assert calls[0] == (session_id, STEP_FLOW[0], 'micro', 'need_retry')
    # 2回目はマクロリフレクション
    assert calls[1][1:3] == ('ALL', 'macro')

@pytest.mark.asyncio
async def test_orchestrator_macro_reflexion(patch_dependencies, monkeypatch):
    # DummyAgent は即完了
    class FinalDummy:
        async def run(self, messages, session_id):
            return {'additional': {}, 'final_notes': 'foo', 'next_step': 'FIN', 'user_visible': 'done'}
    AGENTS[STEP_FLOW[0]] = FinalDummy()

    # プロセス後に呼ばれる PostSessionReflexionAgent をモック
    class FakeMacroAgent:
        async def run(self, messages, session_id):
            return {'content': 'macro result', 'additional': {'patch': 'data'}}
    monkeypatch.setattr(
        'app.services.agents.self_analysis.orchestrator.PostSessionReflexionAgent',
        lambda: FakeMacroAgent()
    )
    calls = []
    async def fake_reflection_store(session_id, step, kind, content):
        calls.append((session_id, step, kind, content))
    monkeypatch.setattr('app.services.agents.self_analysis.orchestrator.reflection_store', fake_reflection_store)

    orchestrator = SelfAnalysisOrchestrator()
    session_id = str(uuid.uuid4())
    result = await orchestrator.run(session_id, 'テスト')
    assert result == 'done'
    # マクロリフレクションが呼ばれている
    assert calls == [(session_id, 'ALL', 'macro', 'macro result')] 