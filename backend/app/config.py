import os

# 国内直连 huggingface.co 会一直超时重试，导致模型下载永远完不成。
# HF_ENDPOINT 是在 huggingface_hub 首次 import 时被读取成常量的，
# 所以必须在任何 chromadb / sentence_transformers 导入之前设置。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 后端项目的根路径

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    LLM_API_KEY: str
    LLM_MODEL: str
    LLM_BASE_URL: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )

settings = Settings()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB 文件最大大小
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip",
}