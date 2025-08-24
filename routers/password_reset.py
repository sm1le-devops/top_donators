# password_reset.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import models
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi_limiter.depends import RateLimiter
import time
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Pydantic модели ---
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# --- Конфиг для почты ---
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USER"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

# --- Хэширование пароля ---
def hash_password(password: str):
    return pwd_context.hash(password)

# --- HTML формы ---
@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_form(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

from typing import Optional

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request, token: Optional[str] = None):
    if not token:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Токен отсутствует"}
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Токен устарел"}
        )
    except JWTError:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Токен недействителен"}
        )

    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


# --- API ---
@router.post(
    "/forgot-password",
    dependencies=[Depends(RateLimiter(times=5, seconds=3600))]  # до 5 запросов в час с одного IP
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    email = request_data.email.strip().lower()
    now = int(time.time())

    user = db.query(models.User).filter(models.User.email == email).first()

    # Даже если пользователя нет — не раскрываем
    if not user:
        return {"message": "Если такой email зарегистрирован, на него отправлена ссылка для восстановления"}

    # Антиспам: не чаще 10 минут
    if getattr(user, "last_reset_request", None) and now - int(user.last_reset_request) < 600:
        raise HTTPException(status_code=429, detail="Слишком частые запросы. Попробуйте позже.")

    # Генерация токена
    token = jwt.encode(
        {"sub": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    reset_link = f"{os.getenv('YOUR_DOMAIN', 'https://top-donators1.onrender.com')}/auth/reset-password?token={token}"

    message = MessageSchema(
        subject="Восстановление пароля",
        recipients=[user.email],
        body=f"Для сброса пароля перейдите по ссылке:\n{reset_link}",
        subtype="plain"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    # Сохраняем время последнего запроса
    user.last_reset_request = now
    db.commit()

    return {"message": "Если такой email зарегистрирован, на него отправлена ссылка для восстановления"}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Токен устарел")
    except JWTError:
        raise HTTPException(status_code=400, detail="Токен недействителен")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Пароль успешно изменен"}
