import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

# note_store_fn が定義されていると仮定されるパス
# 実際のプロジェクト構造に合わせてパスを修正してください。
# from app.services.agents.self_analysis_monono_agent.tools.notes import note_store_fn
# 仮に note_store_fn がこのパスにあるとします。実際のパスに置き換えてください。
PATH_TO_NOTE_STORE_FN = "app.services.agents.self_analysis_monono_agent.tools.notes.note_store_fn"

# テスト用のデータベースモデルのモック (実際のモデル構造を反映)
class MockSelfAnalysisNote:
    def __init__(self, session_id, step, content_json):
        self.session_id = session_id
        self.step = step
        self.content_json = content_json
    
    def update_content(self, new_content_json):
        self.content_json = new_content_json


@pytest.mark.asyncio
@patch(f"{PATH_TO_NOTE_STORE_FN}_db_session_dependency", new_callable=AsyncMock) # DBセッションの依存関係をモック
async def test_note_store_fn_new_note(mock_db_session_dep):
    # TEST.MD: I.B-1-1 (新規ノートの保存)
    # note_store_fn がインポート可能であると仮定
    try:
        from app.services.agents.self_analysis_monono_agent.tools.notes import note_store_fn
    except ImportError:
        pytest.skip(f"{PATH_TO_NOTE_STORE_FN} not found, skipping test.")

    session_id = "test_session"
    current_step = "FUTURE"
    note_data = {"future_vision": "test vision", "values": ["value1"]}
    note_content_json = json.dumps(note_data)

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=None) # 既存ノートなし
    mock_db_session_dep.return_value.__aenter__.return_value = mock_db # async context manager

    result = await note_store_fn(
        session_id=session_id,
        current_step=current_step,
        note_content=note_content_json,
        # db_session=mock_db # 関数が直接DBセッションを引数に取る場合
    )

    assert result == "ノートを保存しました。"
    mock_db.get.assert_called_once() # 検索を試みることを期待
    
    # db.add が SelfAnalysisNote インスタンスで呼ばれたことを確認
    # 実際の SelfAnalysisNote モデルの構造に合わせる
    mock_db.add.assert_called_once()
    added_instance = mock_db.add.call_args[0][0]
    assert added_instance.session_id == session_id
    assert added_instance.step == current_step
    assert json.loads(added_instance.content_json) == note_data
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
@patch(f"{PATH_TO_NOTE_STORE_FN}_db_session_dependency", new_callable=AsyncMock)
async def test_note_store_fn_update_note(mock_db_session_dep):
    # TEST.MD: I.B-1-2 (既存ノートの更新)
    try:
        from app.services.agents.self_analysis_monono_agent.tools.notes import note_store_fn
    except ImportError:
        pytest.skip(f"{PATH_TO_NOTE_STORE_FN} not found, skipping test.")

    session_id = "test_session_update"
    current_step = "MOTIVATION"
    old_note_data = {"motivation_episode": "old episode"}
    new_note_data = {"motivation_episode": "new_episode", "emotion": "happy"}
    new_note_content_json = json.dumps(new_note_data)

    # 既存ノートのモック
    # MockSelfAnalysisNote を使うか、実際のモデルに合わせてモックする
    existing_note_mock = MagicMock() # or MockSelfAnalysisNote(session_id, current_step, json.dumps(old_note_data))
    existing_note_mock.session_id = session_id
    existing_note_mock.step = current_step
    existing_note_mock.content_json = json.dumps(old_note_data)
    # existing_note_mock.update_content = MagicMock() # もしメソッドで更新する場合

    mock_db = AsyncMock()
    # 既存ノートを返すようにgetをモック (キーは (Model, (pk_col1, pk_col2)) のようになる場合もある)
    # ここでは (session_id, step) で引数を取ると仮定
    mock_db.query = MagicMock()
    mock_db.query.return_value.filter_by.return_value.one_or_none = AsyncMock(return_value=existing_note_mock)
    
    mock_db_session_dep.return_value.__aenter__.return_value = mock_db

    result = await note_store_fn(
        session_id=session_id,
        current_step=current_step,
        note_content=new_note_content_json,
        # db_session=mock_db
    )

    assert result == "ノートを更新しました。"
    mock_db.query.return_value.filter_by.return_value.one_or_none.assert_called_once()
    # 既存ノートの content_json が更新されたことを確認
    # 実際の更新ロジックに合わせる (e.g., existing_note_mock.content_json = new_note_content_json)
    # ここでは、add が再度呼ばれる (SQLAlchemy の場合、セッションに追加してコミットで更新)
    mock_db.add.assert_called_once_with(existing_note_mock) 
    assert json.loads(existing_note_mock.content_json) == new_note_data
    mock_db.commit.assert_called_once()

# TODO: (TEST.MD I.B-1-4, I.B-1-5) list_notes_fn のテスト
# TODO: (TEST.MD I.B-2) ツールの引数バリデーションテスト
# TODO: 他のツール関数 (get_summary_fn, render_timeline_fn) のテスト 