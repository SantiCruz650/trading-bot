# MCrypto Trading Bot

Modern, agentic trading intelligence system built with FastAPI (Backend) and Vanilla JS (Frontend).

## 🏗 Repository Structure

- `backend/`: Core trading engine, FastAPI REST API, and Risk Governance.
- `frontend/`: Reactive dashboard optimized for Netlify deployment.

## 🚀 Deployment

### Backend (Render)
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: 3.11.9 (specified in `runtime.txt`)

### Frontend (Netlify)
- **Build Command**: (Static site, no build needed)
- **Publish Directory**: `frontend`
- **Environment Variable**: `VITE_API_URL` (pointing to your Render backend URL)

## 🛡 Security & Safety
- **Strict Mock Mode**: The systems starts by default with `MOCK_EXCHANGE=True`.
- **Risk Governor**: Multi-level safety blocks including Kill Switch and Drawdown Protection.

---
*Created by Antigravity*
