from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from routers.auth import validate_csrf_token

router = APIRouter()

@router.get("/api/check-auth")
def check_auth(request: Request, db: Session = Depends(get_db)):
    cookie_username = request.cookies.get("username")
    cookie_token = request.cookies.get("csrf_token")

    if not cookie_username or not cookie_token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    db_user = db.query(models.User).filter(models.User.username == cookie_username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Не авторизован")

    # validate_csrf_token должна быть где-то импортирована
    if not validate_csrf_token(cookie_token):
        raise HTTPException(status_code=403, detail="Invalid or expired CSRF token")

    return JSONResponse(content={"status": "ok", "user": {"username": db_user.username}})
