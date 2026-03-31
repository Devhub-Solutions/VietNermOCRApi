FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-vie \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
# Note: We will generate requirements.txt later
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org --disable-pip-version-check --no-cache-dir -r requirements.txt


# Copy the rest of the application
COPY . .

# Environment variables
ENV DB_PATH=/app/ocr_app.db
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_PROXY="*"

EXPOSE 8000

CMD ["python", "app.py"]
