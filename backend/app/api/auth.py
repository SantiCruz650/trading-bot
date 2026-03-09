import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from ..schemas.schemas import Token, User, UserCreate
from ..models.models import User as UserModel
from ..auth.auth import create_access_token, get_password_hash, verify_password, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from ..db.session import get_db

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    # Master Credentials Fallback (Persistent across restarts)
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")
    
    is_master = False
    if admin_user and admin_pass:
        if form_data.username == admin_user and form_data.password == admin_pass:
            is_master = True
            print(f"[Auth] Master login successful for '{admin_user}'")

    if not user and not is_master:
        print(f"[Auth] Login failed: User '{form_data.username}' not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not is_master and not verify_password(form_data.password, user.hashed_password):
        print(f"[Auth] Login failed: Password mismatch for user '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If it's a master login but no user object exists in DB, we use the username from env
    token_subject = user.username if user else admin_user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": token_subject}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.get("/verify", response_model=User)
async def verify_token(current_user: UserModel = Depends(get_current_user)):
    """Validate current session token and return user profile."""
    return current_user

@router.post("/accept-manual")
async def accept_manual(
    current_user: UserModel = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    current_user.first_login = False
    db.add(current_user)
    db.commit()
    return {"message": "Manual accepted successfully", "first_login": False}