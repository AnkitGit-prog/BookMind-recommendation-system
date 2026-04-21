# ─────────────────────────────────────────────
#  Stage 1: Build
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────
#  Stage 2: Production Image
# ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app.py .
COPY generate_model.py .
COPY templates/ templates/
COPY static/ static/
COPY model/ model/

# Environment variables
ENV FLASK_ENV=production
ENV SECRET_KEY=bookmind-secret-change-in-prod

# Expose port
EXPOSE 5000

# Run with Gunicorn (production WSGI server) - 1 worker + preload to save memory
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--preload", "--timeout", "120", "app:app"]
