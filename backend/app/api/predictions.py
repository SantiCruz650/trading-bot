from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

from ..schemas.schemas import Prediction, EmailNotification
from ..models.models import Prediction as PredictionModel, User as UserModel
from ..db.session import get_db
from ..auth.auth import get_current_user
from ..core.config import settings
from ..services.websocket_manager import manager

router = APIRouter()

async def run_backtest_background(ticker: str, days: int):
    """Background task to trigger backtest on ML service"""
    try:
        from ..services.ml_service import ml_service
        # Sanitize ticker (e.g., 'ETH/USDT' -> 'ETH')
        clean_ticker = ticker.split("/")[0].upper()
        async with httpx.AsyncClient(timeout=300.0) as client:
            url = f"{ml_service.base_url}/backtest/{clean_ticker}"
            response = await client.get(url, params={"days": days})
            
            if response.status_code == 200:
                result = response.json()
                # Broadcast result via WebSocket
                await manager.broadcast({
                    "type": "backtest_complete",
                    "ticker": ticker,
                    "data": result
                })
            else:
                print(f"Backtest failed with status {response.status_code}")
                await manager.broadcast({
                    "type": "backtest_error",
                    "ticker": ticker,
                    "error": f"ML Service returned {response.status_code}"
                })
                
    except Exception as e:
        print(f"Backtest failed: {e}")
        await manager.broadcast({
            "type": "backtest_error",
            "ticker": ticker,
            "error": str(e)
        })

async def retrain_model_background(ticker: str):
    """Background task to trigger retraining on ML service"""
    try:
        from ..services.ml_service import ml_service
        # Sanitize ticker
        clean_ticker = ticker.split("/")[0].upper()
        async with httpx.AsyncClient(timeout=300.0) as client:
            url = f"{ml_service.base_url}/retrain/{clean_ticker}"
            await client.post(url)
    except Exception as e:
        print(f"Retraining failed: {e}")

@router.post("/predict/{ticker}", response_model=Prediction)
async def create_prediction(ticker: str, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        from ..services.ml_service import ml_service
        data = await ml_service.get_prediction_async(ticker)
        
        if data.get("status") == "offline_fallback":
             logger_warn = f"Prediction for {ticker} using fallback data (ML offline)."
             print(logger_warn)
        
        if "error" in data:
            raise HTTPException(status_code=503, detail=f"Prediction failed: {data['error']}")

        # Store prediction in database
        db_prediction = PredictionModel(
            ticker=ticker,
            last_close=float(data.get("last_close", 0)),
            predicted_close=data.get("signal", "HOLD"),
            signal=data.get("signal", "HOLD"),
            created_at=datetime.utcnow(),
            owner_id=current_user.id
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        # Broadcast update via WebSocket
        await manager.broadcast({
            "type": "new_prediction",
            "ticker": ticker,
            "signal": db_prediction.signal,
            "price": db_prediction.last_close,
            "timestamp": db_prediction.created_at.isoformat()
        })
        
        return db_prediction

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get prediction: {str(e)}")

@router.post("/trigger-retrain/{ticker}")
async def trigger_retrain(ticker: str, background_tasks: BackgroundTasks, current_user: UserModel = Depends(get_current_user)):
    """Trigger model retraining asynchronously via BackgroundTasks"""
    background_tasks.add_task(retrain_model_background, ticker)
    return {"message": "Retraining started in background"}

@router.post("/trigger-backtest/{ticker}")
async def trigger_backtest(ticker: str, background_tasks: BackgroundTasks, days: int = 100, current_user: UserModel = Depends(get_current_user)):
    """Trigger backtest asynchronously via BackgroundTasks"""
    background_tasks.add_task(run_backtest_background, ticker, days)
    return {"message": "Backtest started in background"}

@router.get("/history", response_model=list[Prediction])
async def get_prediction_history(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    predictions = db.query(PredictionModel).filter(
        PredictionModel.owner_id == current_user.id
    ).order_by(PredictionModel.created_at.desc()).limit(10).all()
    return predictions

@router.get("/my-predictions", response_model=list[Prediction])
async def read_my_predictions(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    predictions = db.query(PredictionModel).filter(
        PredictionModel.owner_id == current_user.id
    ).order_by(PredictionModel.created_at.desc()).limit(20).all()
    return predictions

@router.post("/send-notification")
async def send_notification(notification: EmailNotification, current_user: UserModel = Depends(get_current_user)):
    """
    Send email notification for signal changes.
    Requires SMTP configuration via environment variables:
    - SMTP_HOST (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - SMTP_USER (your email)
    - SMTP_PASSWORD (your app password)
    """
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_user or not smtp_password:
            raise HTTPException(
                status_code=400,
                detail="Email notifications not configured. Set SMTP_USER and SMTP_PASSWORD environment variables."
            )
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = notification.email
        msg['Subject'] = f"MCrypto Alert: {notification.signal} signal for {notification.ticker}"
        
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #6366f1;">🚨 MCrypto Trading Signal</h2>
            <p><strong>Ticker:</strong> {notification.ticker}</p>
            <p><strong>Signal:</strong> <span style="color: {'#10b981' if notification.signal == 'BUY' else '#ef4444' if notification.signal == 'SELL' else '#f59e0b'}; font-size: 20px;">{notification.signal}</span></p>
            <p><strong>Current Price:</strong> ${notification.price:,.2f}</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
            <hr>
            <p style="color: #6b7280; font-size: 12px;">This is an automated notification from your MCrypto Trading Bot.</p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {"message": "Notification sent successfully", "email": notification.email}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.get("/market-data/{ticker}")
async def get_market_data(ticker: str, days: int = 365, current_user: UserModel = Depends(get_current_user)):
    """Get historical market data for charting"""
    try:
        from ..services.ml_service import ml_service
        # For history, we don't have a specific mock in MLService yet, but we can call it directly
        # or add it. I'll add a generic request method to MLService if needed.
        # Given the instruction to audit/fix, I'll just use a try/except here too.
        ml_service_url = f"{settings.ML_SERVICE_URL}/history/{ticker}?days={days}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ml_service_url)
            if response.status_code != 200:
                print(f"Failed to fetch market data: {response.status_code}. Returning empty.")
                return []
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")