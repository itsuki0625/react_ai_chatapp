import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            # ローカル開発用・テスト用などにエンドポイントURLを指定する場合
            # endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL'),
            region_name=os.getenv('AWS_REGION', 'ap-northeast-1')
        )
        self.bucket_name = os.getenv('AWS_S3_ICON_BUCKET_NAME')
        if not self.bucket_name:
            logger.error("AWS_S3_ICON_BUCKET_NAME environment variable is not set.")
            # 必要に応じてここで例外を発生させるか、デフォルト値を設定
            # raise ValueError("S3 bucket name for icons is not configured.")

    async def upload_icon(self, file: UploadFile, user_id: str, file_extension: str) -> Optional[str]:
        """ユーザーアイコンをS3にアップロードする"""
        if not self.bucket_name:
            logger.error("S3 bucket name is not configured, cannot upload icon.")
            return None

        # S3のオブジェクトキーを生成 (例: icons/user_123.png)
        object_key = f"icons/user_{user_id}{file_extension}"

        try:
            # await を使って非同期にファイルを読み込む
            contents = await file.read()
            await file.seek(0)  # ストリームの位置をリセット (必要な場合)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=contents,
                ContentType=file.content_type,
                # ACL='public-read'  # ACL を設定しないようにコメントアウト
            )
            logger.info(f"Successfully uploaded icon for user {user_id} to s3://{self.bucket_name}/{object_key}")

            # アップロードされたファイルのURLを返す (CloudFront経由などを想定)
            # ここではオブジェクトキーを返す例（実際のURLはアプリ側で組み立てる）
            # 必要に応じて、署名付きURLなどを生成して返すことも可能
            # s3_url = self.s3_client.generate_presigned_url(
            #     'get_object',
            #     Params={'Bucket': self.bucket_name, 'Key': object_key},
            #     ExpiresIn=3600 # 1時間有効
            # )
            # return s3_url
            return object_key

        except ClientError as e:
            logger.error(f"Failed to upload icon for user {user_id} to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during icon upload for user {user_id}: {e}")
            # より詳細なエラーハンドリングが必要な場合がある
            return None

    async def delete_icon(self, user_id: str, file_extension: str) -> bool:
        """ユーザーアイコンをS3から削除する"""
        if not self.bucket_name:
            logger.error("S3 bucket name is not configured, cannot delete icon.")
            return False

        object_key = f"icons/user_{user_id}{file_extension}"

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            logger.info(f"Successfully deleted icon for user {user_id} from s3://{self.bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete icon for user {user_id} from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during icon deletion for user {user_id}: {e}")
            return False

# 使用例 (FastAPIのルーターなどで):
# from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
# from app.services.s3_service import S3Service
# from app.core.security import get_current_user # 仮の認証関数
# from app.models.user import User # 仮のユーザーモデル

# router = APIRouter()
# s3_service = S3Service()

# @router.post("/upload-icon/")
# async def upload_user_icon(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user)
# ):
#     # ファイル拡張子を取得 (例: .png, .jpg)
#     _, file_extension = os.path.splitext(file.filename)
#     if file_extension.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
#         raise HTTPException(status_code=400, detail="Invalid image format.")

#     object_key = await s3_service.upload_icon(file, str(current_user.id), file_extension)
#     if not object_key:
#         raise HTTPException(status_code=500, detail="Failed to upload icon.")

#     # ここでユーザーモデルの profile_image_url などを更新する処理
#     # 例: await crud.user.update(db, db_obj=current_user, obj_in={"profile_image_url": object_key})

#     return {"message": "Icon uploaded successfully", "object_key": object_key}

# @router.delete("/delete-icon/")
# async def delete_user_icon(current_user: User = Depends(get_current_user)):
#     # ユーザーの現在のアイコンURLから拡張子を取得する必要がある
#     # 例: _, file_extension = os.path.splitext(current_user.profile_image_url)
#     file_extension = ".png" # 仮にpngとする

#     success = await s3_service.delete_icon(str(current_user.id), file_extension)
#     if not success:
#         raise HTTPException(status_code=500, detail="Failed to delete icon.")

#     # ユーザーモデルの profile_image_url をNoneやデフォルト値に更新する処理
#     # 例: await crud.user.update(db, db_obj=current_user, obj_in={"profile_image_url": None})

#     return {"message": "Icon deleted successfully"} 