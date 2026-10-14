# Base Image: Python 3.12 Slim
FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose ports: 8000 for FastAPI REST Backend, 8501 for Streamlit Dashboard
EXPOSE 8000 8501

# Default startup command (runs FastAPI by default)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
