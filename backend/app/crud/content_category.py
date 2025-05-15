from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from typing import List, Optional
from uuid import UUID
from app.models.content import ContentCategory # ContentCategory モデルをインポート
from app.schemas.content import ContentCategoryCreate, ContentCategoryUpdate, ContentCategoryInfo # スキーマをインポート

async def create_content_category(db: AsyncSession, category_in: ContentCategoryCreate) -> ContentCategory:
    """新しいコンテンツカテゴリを作成します。"""
    # name の重複チェック (任意だが推奨)
    existing_category_by_name = await db.execute(
        select(ContentCategory).filter(ContentCategory.name == category_in.name)
    )
    if existing_category_by_name.scalars().first():
        raise ValueError(f"Category with name '{category_in.name}' already exists.")

    db_category = ContentCategory(**category_in.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def get_content_category(db: AsyncSession, category_id: UUID) -> Optional[ContentCategory]:
    """IDで特定のコンテンツカテゴリを取得します。"""
    result = await db.execute(select(ContentCategory).filter(ContentCategory.id == category_id))
    return result.scalars().first()

async def get_content_categories(
    db: AsyncSession, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
) -> List[ContentCategory]:
    """コンテンツカテゴリのリストを取得します。is_activeでフィルタリング可能。"""
    query = select(ContentCategory).order_by(ContentCategory.display_order, ContentCategory.name)
    if is_active is not None:
        query = query.filter(ContentCategory.is_active == is_active)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def update_content_category(
    db: AsyncSession, category_id: UUID, category_in: ContentCategoryUpdate
) -> Optional[ContentCategory]:
    """既存のコンテンツカテゴリを更新します。"""
    db_category = await get_content_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category_in.model_dump(exclude_unset=True)

    # name が更新される場合、重複チェック (任意だが推奨)
    if "name" in update_data and update_data["name"] != db_category.name:
        existing_category_by_name = await db.execute(
            select(ContentCategory).filter(ContentCategory.name == update_data["name"])
        )
        if existing_category_by_name.scalars().first():
            raise ValueError(f"Category with name '{update_data['name']}' already exists.")

    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def delete_content_category(db: AsyncSession, category_id: UUID) -> bool:
    """コンテンツカテゴリを削除します。成功すればTrue、見つからなければFalseを返します。"""
    db_category = await get_content_category(db, category_id)
    if not db_category:
        return False
    
    # 関連するContentCategoryRelationが存在するかチェック (今回はエラーにせず、削除を試みる)
    # from app.models.content import ContentCategoryRelation
    # relations_exist = await db.execute(
    #     select(ContentCategoryRelation).filter(ContentCategoryRelation.category_id == category_id)
    # )
    # if relations_exist.scalars().first():
    #     # 関連コンテンツがある場合は削除しない、またはis_active=Falseにするなどの処理
    #     raise ValueError("Cannot delete category with associated content. Deactivate it instead.")

    await db.delete(db_category)
    await db.commit()
    return True 