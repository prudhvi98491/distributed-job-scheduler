FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY README.md .

# Expose port
EXPOSE 8000

# Set environment variables
ENV DATABASE_URL=sqlite+aiosqlite:///./jobs.db
ENV SECRET_KEY=super-secret-distributed-job-scheduler-key

# Command to run uvicorn server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
