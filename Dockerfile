# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system-level build tools
RUN apt-get update && apt-get install -y gcc

# Install pip build tools
RUN pip install --upgrade pip wheel setuptools

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code (excluding .env via .dockerignore)
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the app with Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
