import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        PROJECT_NAME: str = "VocalChaos"
        PROJECT_DESCRIPTION: str = "AI Supervisor for Voice Agents"
        PROJECT_VERSION: str = "0.1.0"
        
        # Server Settings
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        
        # LLM Settings
        LLM_API_KEY: Optional[str] = None
        GEMINI_API_KEY: Optional[str] = None
        GOOGLE_API_KEY: Optional[str] = None
        LLM_MODEL: str = "gemini-3.6-flash"
        LLM_BASE_URL: Optional[str] = None

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )

        def get_api_key(self) -> Optional[str]:
            return (
                self.GEMINI_API_KEY
                or self.GOOGLE_API_KEY
                or self.LLM_API_KEY
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("LLM_API_KEY")
            )

    settings = Settings()

except ImportError:
    # Graceful fallback when running in an environment where pydantic-settings is not yet installed
    class Settings:  # type: ignore
        PROJECT_NAME: str = os.getenv("PROJECT_NAME", "VocalChaos")
        PROJECT_DESCRIPTION: str = os.getenv("PROJECT_DESCRIPTION", "AI Supervisor for Voice Agents")
        PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "0.1.0")
        
        HOST: str = os.getenv("HOST", "0.0.0.0")
        PORT: int = int(os.getenv("PORT", "8000"))
        
        LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", None)
        GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
        GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY", None)
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.6-flash")
        LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL", None)

        def get_api_key(self) -> Optional[str]:
            return (
                self.GEMINI_API_KEY
                or self.GOOGLE_API_KEY
                or self.LLM_API_KEY
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("LLM_API_KEY")
            )

    settings = Settings()


