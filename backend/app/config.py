from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    FRONTEND_URL: str = "https://ta.userwei.com"
    FRONTEND_REDIRECT_PATH: str = "/login"
    REDIRECT_URI: str = "https://ta.userwei.com/api/oauth/callback"
    AUTHORIZE_URL: str = "https://id.nycu.edu.tw/o/authorize/"
    TOKEN_URL: str = "https://id.nycu.edu.tw/o/token/"
    PROFILE_URL: str = "https://id.nycu.edu.tw/api/profile/"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 36000
    
    MYSQL_HOST: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    class Config:
        env_file = ".env"

settings = Settings()
