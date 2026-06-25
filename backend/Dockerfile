FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies if needed (none are strictly needed for now)
# Copy dependencies list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app codebase
COPY . .

# Expose FastAPI service port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
