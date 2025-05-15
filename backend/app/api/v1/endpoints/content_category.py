from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_async_db, require_permission # 権限に応じて調整
from app.schemas.content import (
    ContentCategoryCreate, ContentCategoryUpdate, ContentCategoryInfo
)
from app.crud import content_category as crud_cc # crud_content_category を短縮名でインポート
from app.models.user import User # current_user の型ヒント用 (get_current_user を使う場合)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/", 
    response_model=ContentCategoryInfo, 
    status_code=status.HTTP_201_CREATED,
    summary="新しいコンテンツカテゴリを作成",
    # dependencies=[Depends(require_permission('category_manage'))] # 例: カテゴリ管理権限 (一旦コメントアウト)
)
async def create_new_content_category(
    category_in: ContentCategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(get_current_user) # ログ記録や作成者情報紐付けに使う場合 (一旦コメントアウト)
):
    """新しいコンテンツカテゴリを作成します。"""
    try:
        created_category = await crud_cc.create_content_category(db=db, category_in=category_in)
        return created_category
    except ValueError as ve: # nameの重複など
        logger.warning(f"Failed to create category: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating content category: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="カテゴリ作成中に予期せぬエラーが発生しました。")

@router.get(
    "/", 
    response_model=List[ContentCategoryInfo],
    summary="コンテンツカテゴリ一覧を取得",
    # dependencies=[Depends(require_permission('category_read'))] # 読み取り権限 (一旦コメントアウト)
)
async def read_content_categories(
    skip: int = Query(0, ge=0, description="スキップするアイテム数"),
    limit: int = Query(100, ge=1, le=200, description="取得する最大アイテム数"),
    is_active: Optional[bool] = Query(None, description="有効なカテゴリのみフィルタリングする場合 True/False"),
    db: AsyncSession = Depends(get_async_db),
):
    """コンテンツカテゴリの一覧を取得します。is_active フィルタ、ページネーション対応。"""
    try:
        categories = await crud_cc.get_content_categories(db=db, skip=skip, limit=limit, is_active=is_active)
        return categories
    except Exception as e:
        logger.error(f"Error reading content categories: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="カテゴリ一覧取得中にエラーが発生しました。")

@router.get(
    "/{category_id}", 
    response_model=ContentCategoryInfo,
    summary="特定のコンテンツカテゴリを取得",
    # dependencies=[Depends(require_permission('category_read'))] # (一旦コメントアウト)
)
async def read_content_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """IDで指定された単一のコンテンツカテゴリを取得します。"""
    db_category = await crud_cc.get_content_category(db=db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定されたIDのカテゴリが見つかりません。")
    return db_category

@router.put(
    "/{category_id}", 
    response_model=ContentCategoryInfo,
    summary="コンテンツカテゴリを更新",
    # dependencies=[Depends(require_permission('category_manage'))] # (一旦コメントアウト)
)
async def update_existing_content_category(
    category_id: UUID,
    category_in: ContentCategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """既存のコンテンツカテゴリ情報を更新します。"""
    try:
        updated_category = await crud_cc.update_content_category(db=db, category_id=category_id, category_in=category_in)
        if updated_category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="更新対象のカテゴリが見つかりません。")
        return updated_category
    except ValueError as ve: # nameの重複など
        logger.warning(f"Failed to update category {category_id}: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating content category {category_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="カテゴリ更新中に予期せぬエラーが発生しました。")

@router.delete(
    "/{category_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="コンテンツカテゴリを削除",
    # dependencies=[Depends(require_permission('category_manage'))] # (一旦コメントアウト)
)
async def delete_existing_content_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """コンテンツカテゴリを削除します。"""
    try:
        deleted_success = await crud_cc.delete_content_category(db=db, category_id=category_id)
        if not deleted_success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="削除対象のカテゴリが見つからないか、削除に失敗しました。")
        return None # No content
    except Exception as e:
        logger.error(f"Error deleting content category {category_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="カテゴリ削除中に予期せぬエラーが発生しました。") 