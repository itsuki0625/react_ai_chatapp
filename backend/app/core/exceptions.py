from fastapi import HTTPException, status

class BaseCustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundError(BaseCustomException):
    """リソースが見つからない場合のエラー (404 Not Found)"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ConflictError(BaseCustomException):
    """データ競合や制約違反が発生した場合のエラー (409 Conflict)"""
    def __init__(self, detail: str = "Conflict occurred"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class DatabaseError(BaseCustomException):
    """データベース操作中に予期せぬエラーが発生した場合 (500 Internal Server Error)"""
    # 本番環境では詳細なエラーメッセージを返さないように注意
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class ForbiddenError(BaseCustomException):
    """アクセス権限がない場合のエラー (403 Forbidden)"""
    def __init__(self, detail: str = "Operation not permitted"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class BadRequestError(BaseCustomException):
    """リクエストが無効な場合のエラー (400 Bad Request)"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class UnprocessableEntityError(BaseCustomException):
    """リクエストは理解できたが、処理できない場合のエラー (422 Unprocessable Entity)"""
    # FastAPIのバリデーションエラーは通常422を返す
    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail) 