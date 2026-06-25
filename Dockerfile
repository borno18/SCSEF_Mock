FROM python:3.11-slim

WORKDIR /workspace

# Copy requirements from backend directory
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code folder
COPY backend/ ./backend/

# Expose backend port
EXPOSE 8000

# Set PYTHONPATH to include workspace root for package imports
ENV PYTHONPATH=/workspace

# Run uvicorn pointing to the main app module
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
