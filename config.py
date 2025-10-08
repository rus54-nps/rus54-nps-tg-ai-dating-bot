from pydantic import BaseSettings

class Config(BaseSettings):
    bot_token: str
    db_url: str
    redis_url: str
    secret_key: str

    class Config:
        env_file = ".env"

config = Config()
