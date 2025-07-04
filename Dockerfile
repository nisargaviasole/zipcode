# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy necessary files
COPY requirements.txt ./
COPY server/ ./server/
COPY utils/ ./utils/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8000

# Run FastAPI using Uvicorn with Gunicorn
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker","--timeout", "600","--max-requests", "100", "--max-requests-jitter", "20", "-b", "0.0.0.0:8000", "server.server:app"]
