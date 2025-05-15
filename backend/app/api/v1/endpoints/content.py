from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_current_user, get_async_db, require_permission
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse, ContentCategoryInfo
from app.crud import content as crud_content
from app.models.user import User
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_content(
    content: ContentCreate,
    current_user: User = Depends(require_permission('content_write')),
    db: AsyncSession = Depends(get_async_db)
):
    """新しいコンテンツを作成 ('content_write' 権限が必要)"""
    try:
        new_content = await crud_content.create_content(db=db, content=content)
        return new_content
    except Exception as e:
        logger.error(f"Error creating content: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="コンテンツ作成エラー")

@router.get("/", response_model=List[ContentResponse])
async def list_contents(
    content_type: Optional[str] = Query(None, description="フィルタリングするコンテンツタイプ"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission('content_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """コンテンツ一覧を取得 ('content_read' 権限が必要)"""
    try:
        contents = await crud_content.get_contents(db=db, skip=skip, limit=limit, content_type=content_type)
        return contents
    except Exception as e:
        logger.error(f"Error listing contents: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="コンテンツ一覧取得エラー")

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content_by_id(
    content_id: str,
    current_user: User = Depends(require_permission('content_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """特定のコンテンツを取得 ('content_read' 権限が必要)"""
    try:
        content_uuid = uuid.UUID(content_id)
        content = await crud_content.get_content(db=db, content_id=content_uuid)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="コンテンツが見つかりません")
        return content
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なコンテンツID形式です")
    except Exception as e:
        logger.error(f"Error getting content {content_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="コンテンツ取得エラー")

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content_by_id(
    content_id: str,
    content_update: ContentUpdate,
    current_user: User = Depends(require_permission('content_write')),
    db: AsyncSession = Depends(get_async_db)
):
    """コンテンツを更新 ('content_write' 権限が必要)"""
    try:
        content_uuid = uuid.UUID(content_id)
        content = await crud_content.update_content(db=db, content_id=content_uuid, content_update=content_update)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="コンテンツが見つかりません")
        return content
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なコンテンツID形式です")
    except Exception as e:
        logger.error(f"Error updating content {content_id}: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="コンテンツ更新エラー")

@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_by_id(
    content_id: str,
    current_user: User = Depends(require_permission('content_write')),
    db: AsyncSession = Depends(get_async_db)
):
    """コンテンツを削除 ('content_write' 権限が必要)"""
    try:
        content_uuid = uuid.UUID(content_id)
        deleted_content = await crud_content.delete_content(db=db, content_id=content_uuid)
        if not deleted_content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="コンテンツが見つかりません")
        return None
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なコンテンツID形式です")
    except Exception as e:
        logger.error(f"Error deleting content {content_id}: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="コンテンツ削除エラー")

@router.get("/categories/", response_model=List[ContentCategoryInfo], tags=["content"])
async def read_content_categories_from_contents_router(
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_permission('content_read')) # カテゴリーは一般公開情報として権限不要にするか、別途検討
):
    """
    全てのコンテンツカテゴリーを取得します。
    """
    categories = await crud_content.get_all_content_categories(db)
    return categories 