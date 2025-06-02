# --- Stage 1: Build dependencies ---
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 2: Final image ---
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# ✅ Copy everything you need from local machine
COPY main.py .
COPY my_model.pt .

ENV PATH="/root/.local/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
