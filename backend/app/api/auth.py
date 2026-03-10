import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from ..schemas.schemas import Token, User, UserCreate
from ..models.models import User as UserModel
from ..auth.auth import create_access_token, get_password_hash, verify_password, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from ..db.session import get_db, engine

router = APIRouter()

import json

BACKUP_USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../users_backup.json")

def save_user_fallback(username, hashed_password):
    """Save user to a local JSON file if database is down."""
    try:
        users = {}
        if os.path.exists(BACKUP_USERS_FILE):
            with open(BACKUP_USERS_FILE, "r") as f:
                users = json.load(f)
        
        users[username] = {"hashed_password": hashed_password, "first_login": True}
        
        with open(BACKUP_USERS_FILE, "w") as f:
            json.dump(users, f)
        print(f"[Auth] Fallback: User '{username}' saved to local JSON backup.")
        return True
    except Exception as e:
        print(f"[Auth] Fallback CRITICAL ERROR: Could not save to JSON: {e}")
        return False

def check_user_fallback(username, password):
    """Check if user exists in local JSON backup."""
    try:
        if not os.path.exists(BACKUP_USERS_FILE):
            return None
            
        with open(BACKUP_USERS_FILE, "r") as f:
            users = json.load(f)
            
        if username in users:
            user_data = users[username]
            if verify_password(password, user_data["hashed_password"]):
                # Return a mock user object that matches the schema
                return {"username": username, "id": -1, "first_login": user_data.get("first_login", True)}
    except Exception as e:
        print(f"[Auth] Fallback check error: {e}")
    return None

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"[Auth] Login attempt for user: '{form_data.username}'")
    
    # 1. Master Credentials Fallback
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")
    
    if admin_user and admin_pass:
        if form_data.username == admin_user and form_data.password == admin_pass:
            print(f"[Auth] -> Master login SUCCESS for '{admin_user}'")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": admin_user}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            print(f"[Auth] -> Master check: No match for '{form_data.username}'")

    # 2. Database Lookup
    try:
        user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        if user:
            if verify_password(form_data.password, user.hashed_password):
                print(f"[Auth] -> Database login SUCCESS for '{user.username}'")
                token_subject = user.username
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": token_subject}, expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                print(f"[Auth] -> Database check: WRONG PASSWORD for '{user.username}'")
        else:
            print(f"[Auth] -> Database check: User '{form_data.username}' not found.")
    except Exception as e:
        print(f"[Auth] -> Database CRASH: {e}")

    # 3. Local JSON Fallback (Backup)
    print(f"[Auth] Looking into local JSON fallback for '{form_data.username}'...")
    fallback_user = check_user_fallback(form_data.username, form_data.password)
    if fallback_user:
        print(f"[Auth] -> Local JSON Backup SUCCESS for '{form_data.username}'")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        print(f"[Auth] -> Local JSON: No match for '{form_data.username}'")

    # Final Failure
    print(f"[Auth] ! [401] All authentication vectors failed for '{form_data.username}'")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos",
        headers={"WWW-Authenticate": "Bearer"},
    )

import traceback

@router.post("/register", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print(f"[Auth] Registration attempt for user: '{user.username}'")
    try:
        # Check database
        db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="El usuario ya existe en el sistema.")
        
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"[Auth] User '{user.username}' registered successfully in Database.")
        return db_user
    except HTTPException as he:
        raise he
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[Auth] Registration CRITICAL DB Error:\n{error_trace}")
        
        # Emergency Fallback to Local JSON
        hashed_password = get_password_hash(user.password)
        if save_user_fallback(user.username, hashed_password):
            # Return a mock user object to satisfy the frontend
            return {"id": -1, "username": user.username, "first_login": True}
            
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al registrar: {str(e)}")

@router.get("/diag")
def diag_db(db: Session = Depends(get_db)):
    """Diagnostic endpoint to verify database users."""
    try:
        users = db.query(UserModel).all()
        return {
            "status": "ok",
            "db_engine": str(engine.url.drivername),
            "user_count": len(users),
            "users": [u.username for u in users]
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "trace": traceback.format_exc()}

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