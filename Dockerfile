FROM python:3.11-slim

# Install Redis and system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    gcc \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start_docker.sh .

# Make start script executable
RUN chmod +x start_docker.sh

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV DATABASE_URL=sqlite:////app/tradingbot.db
ENV REDIS_URL=redis://localhost:6379/0

# Run the start script
CMD ["./start_docker.sh"]
