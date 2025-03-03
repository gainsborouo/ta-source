import os
import time
import glob
import jwt
import httpx
import uuid
import secrets
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import Depends, Cookie, Form, Request
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from app.dependencies import get_db
from app.models import User, Course
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_from_db(username: str, db: Session):
    return db.query(User).filter(User.username == username).first()

def save_user_to_db(username: str, password: str, email: str, local: bool = False, admin: bool = False, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return
    
    hashed_password = hash_password(password)
    new_user = User(
        username=username,
        password=hashed_password,
        email=email,
        local=local,
        admin=admin
    )
    db.add(new_user)
    db.commit()


def get_courses_from_db(db: Session):
    return db.query(Course).all()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_from_db(form_data.username, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.local:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    payload = {
        "sub": user.username,
        "admin": bool(user.admin),
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "iat": int(time.time()),
        "iss": "ta-system",
        "jti": str(uuid.uuid4()), 
    }
    our_jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": our_jwt_token,
        "token_type": "bearer"
    }

@router.get("/oauth/nycu/login")
async def oauth_nycu_login(request: Request):
    csrf_token = secrets.token_urlsafe(32)
    request.session['csrf_token'] = csrf_token
    
    scopes = "profile"
    auth_url = (
        f"{settings.NYCU_AUTHORIZE_URL}"
        f"?client_id={settings.NYCU_CLIENT_ID}"
        f"&response_type=code"
        f"&state={csrf_token}"
        f"&scope={scopes.replace(' ', '%20')}"
        f"&redirect_uri={settings.NYCU_REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/oauth/nycu/callback")
async def oauth_nycu_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    stored_csrf_token = request.session.get('csrf_token')
    if not stored_csrf_token or stored_csrf_token != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSRF token"
        )
    
    request.session.pop('csrf_token', None)
    
    async with httpx.AsyncClient(verify=False) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.NYCU_CLIENT_ID,
            "client_secret": settings.NYCU_CLIENT_SECRET,
            "redirect_uri": settings.NYCU_REDIRECT_URI,
        }
        token_resp = await client.post(settings.NYCU_TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=token_resp.status_code, detail="Token exchange failed")
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received from OAuth provider")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(verify=False) as client:
        profile_resp = await client.get(settings.NYCU_PROFILE_URL, headers=headers)
        
    if profile_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user information")
    profile_data = profile_resp.json()
    
    student_id = profile_data.get("username")
    user_email = profile_data.get("email")
    if not student_id or not user_email:
        raise HTTPException(status_code=400, detail="Incomplete user information")
    
    save_user_to_db(student_id, "", user_email, local=False, admin=False, db=db)
    user_in_db = get_user_from_db(student_id, db)
    
    payload = {
        "sub": user_in_db.username,
        "admin": bool(user_in_db.admin),
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "iat": int(time.time()),
        "iss": "ta-system",
        "jti": str(uuid.uuid4()), 
    }
    our_jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    front_end_redirect_url = f"{settings.FRONTEND_URL}{settings.FRONTEND_REDIRECT_PATH}?token={our_jwt_token}"
    return RedirectResponse(url=front_end_redirect_url)

@router.get("/oauth/csit/login")
async def oauth_csit_login(request: Request):
    csrf_token = secrets.token_urlsafe(32)
    request.session['csrf_token'] = csrf_token
    
    scopes = "csid"
    auth_url = (
        f"{settings.CSIT_AUTHORIZE_URL}"
        f"?client_id={settings.CSIT_CLIENT_ID}"
        f"&response_type=code"
        f"&state={csrf_token}"
        f"&scope={scopes.replace(' ', '%20')}"
        f"&redirect_uri={settings.CSIT_REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/oauth/csit/callback")
async def oauth_csit_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    stored_csrf_token = request.session.get('csrf_token')
    if not stored_csrf_token or stored_csrf_token != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSRF token"
        )
    
    request.session.pop('csrf_token', None)
    
    async with httpx.AsyncClient(verify=False) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.CSIT_CLIENT_ID,
            "client_secret": settings.CSIT_CLIENT_SECRET,
            "redirect_uri": settings.CSIT_REDIRECT_URI,
        }
        token_resp = await client.post(settings.CSIT_TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=token_resp.status_code, detail="Token exchange failed")
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received from OAuth provider")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(verify=False) as client:
        profile_resp = await client.get(settings.CSIT_PROFILE_URL, headers=headers)
        
    if profile_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user information")
    profile_data = profile_resp.json()
    
    student_id = profile_data.get("csid")
    
    if not student_id:
        raise HTTPException(status_code=400, detail="Incomplete user information")
    
    save_user_to_db(student_id, "", "", local=False, admin=False, db=db)
    user_in_db = get_user_from_db(student_id, db)
    
    payload = {
        "sub": user_in_db.username,
        "admin": bool(user_in_db.admin),
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "iat": int(time.time()),
        "iss": "ta-system",
        "jti": str(uuid.uuid4()), 
    }
    our_jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    front_end_redirect_url = f"{settings.FRONTEND_URL}{settings.FRONTEND_REDIRECT_PATH}?token={our_jwt_token}"
    return RedirectResponse(url=front_end_redirect_url)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        student_id = payload.get("sub")
        if student_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        user = get_user_from_db(student_id, db)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found in DB")

        return {
            "username": user.username,
            "admin": user.admin,
            "exp": payload.get("exp"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token decode error")

@router.get("/courses/{course}/logs")
async def list_course_logs(
    course: str,
    student_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    logs_dir = os.path.join("app", "static", "logs", course)
    if not os.path.exists(logs_dir):
        raise HTTPException(status_code=404, detail="Course logs not found")

    is_admin = current_user["admin"]
    current_user_id = current_user["username"]

    if is_admin:
        if student_id:
            pattern = os.path.join(logs_dir, f"*{student_id}*")
        else:
            pattern = os.path.join(logs_dir, "*")
    else:
        pattern = os.path.join(logs_dir, f"*{current_user_id}*")

    files = glob.glob(pattern)
    file_names = sorted([os.path.basename(f) for f in files])
    return file_names

@router.get("/courses/{course}/logs/{filename}")
async def get_course_log(course: str, filename: str, current_user: dict = Depends(get_current_user)):
    student_id = current_user["username"]
    is_admin = current_user["admin"]

    if not is_admin:
        if student_id not in filename:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if '..' in filename or filename.startswith('/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid filename"
        )

    base_path = Path("app/static/logs").resolve()
    file_path = (base_path / course / filename).resolve()

    if not str(file_path).startswith(str(base_path)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"filename": filename, "content": content}

@router.get("/courses")
async def get_courses(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = get_courses_from_db(db)
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found")
    return courses