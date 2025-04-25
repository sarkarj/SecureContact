FROM python:3.11

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    build-essential libssl-dev libffi-dev python3-dev cargo pkg-config \
    libjpeg-dev zlib1g-dev sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables (use .env for secrets)
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
ENV RATELIMIT_STORAGE_URL="memory://"
ENV RATELIMIT_DEFAULT="5 per second"

# Expose app port
EXPOSE 8080

# Gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "3", "--threads", "2"]
