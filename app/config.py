from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    public_base_url: str = "http://localhost:8000"  # ngrok URL in dev
    owner_phone: str = ""  # E.164, e.g. +91XXXXXXXXXX

    gemini_api_key: str = ""
    groq_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    database_url: str = ""  # Neon


settings = Settings()
