# Use official Python 3.13 slim image to reduce size
FROM python:3.13-slim

# Install system dependencies (if needed for heavy libraries like torch)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Create directory for data (if needed for images, but better to mount volume)
RUN mkdir -p /app/data

# Expose port for API (uvicorn default 8000)
EXPOSE 8000

# By default, start API via uvicorn
# To run bot or parser, you can override CMD when starting the container
CMD ["uvicorn", "apps.api:app", "--host", "0.0.0.0", "--port", "8000"]