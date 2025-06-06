import pytest
import uuid
import json

from app.services.agents.monono_agent.components.context_manager import ContextManager


def test_update_context_session_only():
    cm = ContextManager()
    sid = uuid.uuid4()
    entry = {"foo": "bar"}
    cm.update_context(sid, entry)
    # active_contextsにセッションのエントリが追加されていること
    assert str(sid) in cm.active_contexts
    assert cm.active_contexts[str(sid)] == [entry]
    # user_profiles, global_contextは空のまま
    assert cm.user_profiles == {}
    assert cm.global_context == {}


def test_update_context_user_and_global():
    cm = ContextManager()
    sid = uuid.uuid4()
    new_data = {"user_id": "u1", "global_context": {"gkey": "gval"}, "info": 123}
    cm.update_context(sid, new_data)
    # session context
    assert cm.active_contexts[str(sid)][0] == new_data
    # user_profilesが更新されていること
    assert "u1" in cm.user_profiles
    assert cm.user_profiles["u1"]["info"] == 123
    # global_contextが更新されていること
    assert cm.global_context.get("gkey") == "gval"


def test_get_relevant_context_basic():
    cm = ContextManager()
    q = "Hello Context"
    out = cm.get_relevant_context(q)
    # セッションもユーザーも指定しない場合、クエリのみ
    assert out == f"CurrentQuery: {q}"


def test_get_relevant_context_with_session():
    cm = ContextManager()
    sid = uuid.uuid4()
    entry = {"k": 1}
    cm.update_context(sid, entry)
    q = "TestQ"
    out = cm.get_relevant_context(q, session_id=sid)
    parts = out.split("\n")
    # 最初にSessionContext
    assert parts[0] == f"SessionContext: {json.dumps(entry)}"
    # 最後にクエリ
    assert parts[-1] == f"CurrentQuery: {q}"


def test_get_relevant_context_with_user_and_global():
    cm = ContextManager()
    # user_profilesを手動設定
    cm.user_profiles["user1"] = {"user_id": "user1", "role": "admin"}
    cm.global_context = {"a": "1", "b": "2"}
    q = "Q2"
    out = cm.get_relevant_context(q, user_id="user1")
    parts = out.split("\n")
    # UserProfileが含まれる
    assert any(p.startswith("UserProfile:") for p in parts)
    # global_contextの行が含まれる
    assert any(p == "GlobalContext[a]: 1" for p in parts)
    assert any(p == "GlobalContext[b]: 2" for p in parts)
    # 最後にクエリ
    assert parts[-1] == f"CurrentQuery: {q}"


def test_get_relevant_context_full_order():
    cm = ContextManager()
    sid = uuid.uuid4()
    cm.update_context(sid, {"x": "y"})
    # user_profilesも更新
    cm.user_profiles["u2"] = {"user_id": "u2", "pref": "z"}
    # global_contextも追加
    cm.global_context = {"k1": "v1", "k2": "v2"}
    q = "FinalQ"
    out = cm.get_relevant_context(q, session_id=sid, user_id="u2")
    parts = out.split("\n")
    # 順序: SessionContext, UserProfile, GlobalContext[k1], GlobalContext[k2], CurrentQuery
    assert parts[0].startswith("SessionContext:")
    assert parts[1].startswith("UserProfile:")
    assert parts[2] == "GlobalContext[k1]: v1"
    assert parts[3] == "GlobalContext[k2]: v2"
    assert parts[4] == f"CurrentQuery: {q}" 