from datetime import datetime
from pydantic import BaseModel, EmailStr

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- User ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# --- Prediction ---
class PredictionBase(BaseModel):
    ticker: str
    last_close: float
    predicted_close: str
    signal: str

class PredictionCreate(PredictionBase):
    pass

class Prediction(PredictionBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Email ---
class EmailNotification(BaseModel):
    email: EmailStr
    signal: str
    ticker: str
    price: float