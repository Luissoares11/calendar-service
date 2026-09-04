# ── Base image ────────────────────────────────────────────────

FROM python:3.12-slim

# ── Working directory ─────────────────────────────────────────

WORKDIR /app

# ── Install dependencies first  ─────────────────────────────

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy the application code ─────────────────────────────────

COPY . .

# ── Create data directories ───────────────────────────────────

RUN mkdir -p data logs

# ── Expose the port ───────────────────────────────────────────

EXPOSE 8010

# ── Start command ─────────────────────────────────────────────

CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8010"]
