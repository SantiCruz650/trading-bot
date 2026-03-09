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
    # Master Credentials Fallback (Check BEFORE database to bypass any DB issues)
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")
    
    if admin_user and admin_pass:
        if form_data.username == admin_user and form_data.password == admin_pass:
            print(f"[Auth] Master login successful for '{admin_user}'")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": admin_user}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}

    # If not master, check database
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    if not user:
        print(f"[Auth] Login failed: User '{form_data.username}' not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        print(f"[Auth] Login failed: Password mismatch for user '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_subject = user.username
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": token_subject}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="El usuario ya existe en el sistema.")
        
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException as he:
        # Re-raise explicit user errors
        raise he
    except Exception as e:
        print(f"[Auth] Registration error: {str(e)}")
        # Handle database connection errors (Supabase down, etc)
        if "connection" in str(e).lower() or "database" in str(e).lower():
            raise HTTPException(status_code=503, detail="Error de conexión con la base de datos externa.")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al registrar: {str(e)}")

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