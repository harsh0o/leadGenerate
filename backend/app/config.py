import pathlib as _pathlib
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = _pathlib.Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    openrouter_model: str = 'mistralai/mistral-7b-instruct:free'
    database_url: str = 'sqlite:///./leadhunter.db'
    rsshub_base_url: str = 'http://localhost:1200'
    scan_interval_hours: int = 2
    log_level: str = 'INFO'
    reddit_user_agent: str = 'script:LeadHunterAI:v1.0 (by /u/leadhunter_bot)'
    linkedin_profile_dir: str = './linkedin_chrome_profile'
    linkedin_headless: bool = True
    linkedin_user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    intent_confidence_threshold: float = 0.80
    match_confidence_threshold: float = 0.85
    max_concurrent_scrapes: int = 3
    cors_origins: str = ''

    model_config = SettingsConfigDict(env_file=str(_BACKEND_DIR / '.env'), extra='ignore')


@lru_cache
def get_settings() -> Settings:
    return Settings()
