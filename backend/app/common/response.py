from pydantic import BaseModel
from typing import Any

class Response(BaseModel):
    """统一封装的相应格式"""
    code: int
    message: str
    data: Any = None

    @classmethod
    def success(cls, message: str = "请求成功", data: Any = None):
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 400, message: str = "请求失败"):
        return cls(code = code,message = message)

class PageResponse(BaseModel):
    """分页的返回结果"""

    list: Any = []
    total: int = 0