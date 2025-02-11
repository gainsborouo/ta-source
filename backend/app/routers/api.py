import os
import time
import glob
import jwt
import httpx
import mysql.connector
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_db_connection():
    connection = mysql.connector.connect(
        host=settings.MYSQL_HOST,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
    )
    return connection

def get_user_from_db(username: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

def save_user_to_db(username: str, password: str, email: str, local: bool):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()
        return
    
    hashed_password = hash_password(password)
    
    cursor.execute(
        "INSERT INTO users (username, password, email, local) VALUES (%s, %s, %s, %s)",
        (username, hashed_password, email, local),
    )
    connection.commit()
    cursor.close()
    connection.close()


def get_courses_from_db():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.close()
    connection.close()
    return courses

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_from_db(form_data.username)
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user['local']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Local login not allowed"
        )
    
    if not verify_password(form_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    payload = {
        "sub": form_data.username,
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    our_jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": our_jwt_token,
        "token_type": "bearer"
    }

@router.get("/oauth/login")
async def oauth_login():
    scopes = "profile"
    auth_url = (
        f"{settings.AUTHORIZE_URL}"
        f"?client_id={settings.CLIENT_ID}"
        f"&response_type=code"
        f"&scope={scopes.replace(' ', '%20')}"
        f"&redirect_uri={settings.REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/oauth/callback")
async def oauth_callback(code: str):
    async with httpx.AsyncClient(verify=False) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "redirect_uri": settings.REDIRECT_URI,
        }
        token_resp = await client.post(settings.TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=token_resp.status_code, detail="Token exchange failed")
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received from OAuth provider")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(verify=False) as client:
        profile_resp = await client.get(settings.PROFILE_URL, headers=headers)
        
    if profile_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user information")
    profile_data = profile_resp.json()
    
    student_id = profile_data.get("username")
    user_email = profile_data.get("email")
    if not student_id or not user_email:
        raise HTTPException(status_code=400, detail="Incomplete user information")
    
    save_user_to_db(student_id, "", user_email, local=False)
    
    payload = {
        "sub": student_id,
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    our_jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    front_end_redirect_url = f"{settings.FRONTEND_URL}{settings.FRONTEND_REDIRECT_PATH}?token={our_jwt_token}"
    return RedirectResponse(url=front_end_redirect_url)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        student_id = payload.get("sub")
        if student_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token decode error")

@router.get("/courses/{course}/logs")
async def list_course_logs(course: str, current_user: dict = Depends(get_current_user)):
    student_id = current_user.get("sub")
    logs_dir = os.path.join("app", "static", "logs", course)
    if not os.path.exists(logs_dir):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course logs not found")
    pattern = os.path.join(logs_dir, f"*{student_id}*")
    files = glob.glob(pattern)
    file_names = [os.path.basename(f) for f in files]
    return file_names

@router.get("/courses/{course}/logs/{filename}")
async def get_course_log(course: str, filename: str, current_user: dict = Depends(get_current_user)):
    student_id = current_user.get("sub")
    if student_id not in filename:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    filepath = os.path.join("app", "static", "logs", course, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"filename": filename, "content": content}

@router.get("/courses")
async def get_courses(current_user: dict = Depends(get_current_user)):
    courses = get_courses_from_db()
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found")
    return courses