import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def dummy_user():
    class Role:
        name = "管理者"
    class UserRole:
        def __init__(self):
            self.role = Role()
    class User:
        def __init__(self):
            self.id = str(uuid.uuid4())
            self.email = "test@example.com"
            # 管理者ロールを持つことで権限チェックをスキップ
            self.user_roles = [UserRole()]
            self.permissions = ["chat_session_read", "chat_message_send"]
    return User()

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch, dummy_user):
    # 認証・権限チェックをモック
    # AuthMiddleware をバイパスして認証をスキップ
    async def bypass_auth(self, request, call_next):
        # リクエスト状態にユーザーIDをセットして認証を模倣
        request.state.user_id = dummy_user.id
        return await call_next(request)
    monkeypatch.setattr('app.middleware.auth.AuthMiddleware.dispatch', bypass_auth)
    # v1 APIパスの認証を無効化
    monkeypatch.setattr('app.middleware.auth.NO_AUTH_PATHS', ['/api/v1'])
    # chatエンドポイントの require_permission をバイパス
    monkeypatch.setattr('app.api.v1.endpoints.chat.require_permission', lambda perm: lambda: dummy_user)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    # require_permission('chat_session_read') 等を常に成功とする
    monkeypatch.setattr('app.api.deps.get_current_user', lambda: dummy_user)
    monkeypatch.setattr('app.api.deps.get_current_user_from_token', lambda token, db: dummy_user)
    monkeypatch.setattr('app.api.deps.check_permissions_for_user', lambda user, perms: True)
    # DB依存をモック
    monkeypatch.setattr('app.api.deps.get_async_db', lambda: None)
    # crudのget_user_chat_sessionsを非同期でスタブ
    async def fake_crud_get_user_chat_sessions(db, user_id, chat_type, status):
        return []
    monkeypatch.setattr('app.crud.chat.get_user_chat_sessions', fake_crud_get_user_chat_sessions)
    # crud_user.get_userを非同期でバイパス
    async def fake_crud_user_get_user(db, user_id):
        return dummy_user
    monkeypatch.setattr('app.crud.user.get_user', fake_crud_user_get_user)
    # FastAPIの依存関係をオーバーライドして get_current_user をバイパス
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    # chatエンドポイントの get_user_chat_sessions を非同期でスタブ
    async def fake_chat_get_user_chat_sessions(db, user_id, chat_type, status):
        return []
    monkeypatch.setattr('app.api.v1.endpoints.chat.get_user_chat_sessions', fake_chat_get_user_chat_sessions)
    # chatエンドポイントの get_async_db をモックしてDB呼び出しを抑制
    monkeypatch.setattr('app.api.v1.endpoints.chat.get_async_db', lambda: None)

@pytest.mark.asyncio
async def test_get_sessions_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get('/api/v1/chat/sessions?chat_type=SELF_ANALYSIS&status=ACTIVE')
        assert resp.status_code == 200
        assert resp.json() == []

@pytest.mark.asyncio
async def test_get_sessions_non_empty(monkeypatch, dummy_user):
    sample = [{
        "id": str(uuid.uuid4()),
        "title": "サンプルセッション",
        "chat_type": "self_analysis",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": None,
        "last_message_summary": None,
    }]
    # chatエンドポイントの get_user_chat_sessions を非同期でスタブ（非空ケース）
    async def fake_nonempty_get_user_chat_sessions(db, user_id, chat_type, status):
        return sample
    monkeypatch.setattr('app.api.v1.endpoints.chat.get_user_chat_sessions', fake_nonempty_get_user_chat_sessions)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get('/api/v1/chat/sessions?chat_type=SELF_ANALYSIS&status=ACTIVE')
        assert resp.status_code == 200
        assert resp.json() == sample 