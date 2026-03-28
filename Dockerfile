# ─── Backend only (frontend is on Vercel) ────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.app.server:app", "--host", "0.0.0.0", "--port", "7860"]
