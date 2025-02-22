from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FRONTEND_URL: str = "https://ta.userwei.com"
    FRONTEND_REDIRECT_PATH: str = "/login"
    
    NYCU_CLIENT_ID: str
    NYCU_CLIENT_SECRET: str
    NYCU_REDIRECT_URI: str = "https://ta.userwei.com/api/oauth/nycu/callback"
    NYCU_AUTHORIZE_URL: str = "https://id.nycu.edu.tw/o/authorize/"
    NYCU_TOKEN_URL: str = "https://id.nycu.edu.tw/o/token/"
    NYCU_PROFILE_URL: str = "https://id.nycu.edu.tw/api/profile/"
    
    CSIT_CLIENT_ID: str
    CSIT_CLIENT_SECRET: str
    CSIT_REDIRECT_URI: str = "https://ta.userwei.com/api/oauth/csit/callback"
    CSIT_AUTHORIZE_URL: str = "https://oauth.cs.nycu.edu.tw/oauth/authorize/"
    CSIT_TOKEN_URL: str = "https://oauth.cs.nycu.edu.tw/oauth/token/"
    CSIT_PROFILE_URL: str = "https://oauth.cs.nycu.edu.tw/api/me"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 36000
    
    MYSQL_HOST: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    class Config:
        env_file = ".env"

settings = Settings()
