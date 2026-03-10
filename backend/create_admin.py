import os
import sys
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from app.models.models import User, Base
from app.core.config import settings

# Password hashing setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_user(username, password):
    print(f"[*] Syncing database schemas on {settings.DATABASE_URL.split('@')[-1]}...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"[!] User '{username}' already exists. Updating password...")
            existing.hashed_password = get_password_hash(password)
            db.commit()
            print(f"[+] Password updated successfully for '{username}'.")
            return

        # Create new user
        new_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            first_login=True
        )
        db.add(new_user)
        db.commit()
        print(f"[+] User '{username}' created successfully in the database.")
    except Exception as e:
        print(f"[X] Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)
    
    user = sys.argv[1]
    pw = sys.argv[2]
    create_user(user, pw)
