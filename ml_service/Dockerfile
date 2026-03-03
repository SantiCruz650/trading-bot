FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application using shell form to expand environment variables
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}