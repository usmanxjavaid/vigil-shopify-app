from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Shopify
    shopify_api_key: str
    shopify_api_secret: str
    shopify_api_version: str = "2026-07"

    # Phase 2 proof-of-concept only — real per-shop tokens come from the
    # database starting Phase 3. Delete these two once that's wired up.
    test_shop_domain: str
    test_shopify_access_token: str

    # Internal API auth (Node -> Python)
    internal_api_secret: str

    # Database (used starting Phase 3, declared now so .env.example is complete)
    database_url: str

    # Email — Gmail SMTP for now, swapped for Resend once a domain exists
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_address: str
    email_app_password: str

    # LLM — Groq first, OpenRouter fallback
    groq_api_key: str
    openrouter_api_key: str

    # Logging
    console_log_level: str = "INFO"


settings = Settings()