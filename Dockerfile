# ─── Stage 1: Build Next.js frontend ─────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline

COPY frontend/ ./
RUN npm run build


# ─── Stage 2: Python backend + serve frontend ────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built Next.js static files into /app/static
COPY --from=frontend-builder /app/frontend/out ./static/

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.app.server:app", "--host", "0.0.0.0", "--port", "7860"]
