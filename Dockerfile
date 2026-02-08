# Multi-stage build (pattern from trip: single-container deployment)
# Stage 1: Nothing to build for vanilla JS frontend, just copy files
# Stage 2: Python runtime with FastAPI serving both API and static files

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/app ./app

# Copy frontend into static directory (served by FastAPI)
COPY frontend ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
