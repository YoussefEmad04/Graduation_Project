# Use full Python 3.11 image (includes common build tools and libraries)
# This prevents missing dependency errors common with 'slim' images for data science packages
FROM python:3.11

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (extra safety for PDF/Image libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and install dependencies
# We split this to ensure pip is up to date before tackling heavy packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Default command
CMD ["uvicorn", "advisor_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
