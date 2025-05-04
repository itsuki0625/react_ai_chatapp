import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas, models
from app.api import deps
from app.services.s3_service import S3Service

router = APIRouter()
s3_service = S3Service()

@router.post("/me/icon", response_model=schemas.UserResponse, summary="Upload user icon")
async def upload_user_icon(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_user)
):
    """現在のユーザーのプロフィールアイコンをアップロードします。"""
    _, file_extension = os.path.splitext(file.filename)
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}
    if file_extension.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image format. Allowed formats: {', '.join(allowed_extensions)}"
        )

    if current_user.profile_image_url:
        _, old_extension = os.path.splitext(current_user.profile_image_url)
        if old_extension:
             await s3_service.delete_icon(str(current_user.id), old_extension)

    object_key = await s3_service.upload_icon(file, str(current_user.id), file_extension)
    if not object_key:
        raise HTTPException(status_code=500, detail="Failed to upload icon to S3.")

    user_update = schemas.UserUpdate(profile_image_url=object_key)
    updated_user = await crud.user.update_user(db, db_user=current_user, user_in=user_update)

    return updated_user


@router.delete("/me/icon", response_model=schemas.UserResponse, summary="Delete user icon")
async def delete_user_icon(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """現在のユーザーのプロフィールアイコンを削除します。"""
    if not current_user.profile_image_url:
        raise HTTPException(status_code=404, detail="User icon not found.")

    _, file_extension = os.path.splitext(current_user.profile_image_url)
    if not file_extension:
         raise HTTPException(status_code=500, detail="Could not determine file extension from stored URL.")

    success = await s3_service.delete_icon(str(current_user.id), file_extension)
    if not success:
        pass

    user_update = schemas.UserUpdate(profile_image_url=None)
    updated_user = await crud.user.update_user(db, db_user=current_user, user_in=user_update)

    return updated_user

# 注意: ユーザー取得エンドポイント (/users/me など) が更新された UserResponse を返すことを確認してください。
# deps.get_current_active_user が返す User モデルに profile_image_url が含まれていることも前提です。 