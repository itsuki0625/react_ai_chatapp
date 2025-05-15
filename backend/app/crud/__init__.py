# backend/app/crud/__init__.py

# 他の crud モジュールがインポートされている場合はそれに倣う
from . import crud_permission
from . import crud_role
from . import token # 例: 他のモジュール
# from . import crud_content_category # ★ 変更前
from . import content_category as crud_content_category # ★ crud_content_category.py を content_category としてインポート
# ... 他のインポート ...

# ★ user.py モジュールを crud_user という名前でインポート可能にする
from . import user as crud_user

# ★ desired_school.py モジュールをインポート
from . import desired_school

# ★ content.py モジュールをインポート
from . import content

# 特定の関数を直接エクスポートしたい場合は以下のように書くこともできる
# from .user import (
#     get_user,
#     get_user_by_email,
#     create_user,
#     update_user,
#     remove_user,
#     get_multi_users,
#     # ... 他に必要な関数
# )
