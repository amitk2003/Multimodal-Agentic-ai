"""
Application configuration using pydantic-settings.
Loads from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Month-End Close Orchestrator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://neondb_owner:npg_iz5bIjFCLr8n@ep-holy-unit-amu73g0x-pooler.c-5.us-east-1.aws.neon.tech/month-end-close?sslmode=require&channel_binding=require"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://default:qHuQAzs1RDbLRhPAvfggL0yUtgo2lYrD@redis-18198.c244.us-east-1-2.ec2.cloud.redislabs.com:18198/0"
    REDIS_CELERY_URL: str = "redis://default:qHuQAzs1RDbLRhPAvfggL0yUtgo2lYrD@redis-18198.c244.us-east-1-2.ec2.cloud.redislabs.com:18198/1"

    # LLM - Anthropic Claude
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    # OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None

    # Google Gemini (fallback)
    GEMINI_API_KEY: Optional[str] ="AIzaSyBcMcOjTmZSbSa4hzJYIywuAF7O5Oxs_1g"


    # Email - Resend
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@apexcapital.com"
    EMAIL_ENABLED: bool = False

    # Email Recipients
    PE_PARTNER_EMAIL: str = "partners@apexcapital.com"
    CFO_EMAILS: str = "cfo@techforge.com,cfo@precisionmfg.com,cfo@retailco.com,cfo@healthservices.com,cfo@logisticspro.com,cfo@industrialsupply.com,cfo@dataanalytics.com,cfo@ecopackaging.com"

    # Langflow
    LANGFLOW_URL: str = "http://localhost:7860"
    LANGFLOW_API_KEY: Optional[str] = None

    # Agent Settings
    VARIANCE_THRESHOLD_PCT: float = 10.0
    VARIANCE_THRESHOLD_AMT: float = 50000.0
    MAX_AGENT_RETRIES: int = 3
    AGENT_RETRY_DELAY: int = 5

    # Scheduler
    DAILY_CLOSE_HOUR: int = 9
    DAILY_CLOSE_MINUTE: int = 0
    MONITORING_INTERVAL_MINUTES: int = 5

    # WebSocket
    WS_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Data
    DATA_DIR: str = "./data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
