from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_current_user, get_db
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse
from app.crud.content import create_content, get_content, get_contents, update_content, delete_content
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ContentResponse)
async def create_new_content(
    content: ContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新しいコンテンツを作成"""
    return create_content(db=db, content=content)

@router.get("/", response_model=List[ContentResponse])
async def list_contents(
    content_type: Optional[str] = Query(None, description="フィルタリングするコンテンツタイプ"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """コンテンツ一覧を取得"""
    return get_contents(db=db, skip=skip, limit=limit, content_type=content_type)

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content_by_id(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """特定のコンテンツを取得"""
    content = get_content(db=db, content_id=content_id)
    if not content:
        raise HTTPException(status_code=404, detail="コンテンツが見つかりません")
    return content

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content_by_id(
    content_id: str,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """コンテンツを更新"""
    content = update_content(db=db, content_id=content_id, content_update=content_update)
    if not content:
        raise HTTPException(status_code=404, detail="コンテンツが見つかりません")
    return content

@router.delete("/{content_id}")
async def delete_content_by_id(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """コンテンツを削除"""
    success = delete_content(db=db, content_id=content_id)
    if not success:
        raise HTTPException(status_code=404, detail="コンテンツが見つかりません")
    return {"message": "コンテンツが削除されました"} 