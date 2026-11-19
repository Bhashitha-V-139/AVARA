from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: E:\Avara (this file is in backend\app\config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings. Values can be overridden in a .env file or environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AVARA"
    app_version: str = "0.1.0"
    data_dir: Path = PROJECT_ROOT / "data"
    max_upload_mb: int = 20

    # LLM settings, read from .env. The key is never stored in code.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "avara.sqlite3"

    def ensure_directories(self) -> None:
        """Create the data folders if they don't exist yet."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()