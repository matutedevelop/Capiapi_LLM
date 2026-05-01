# FROM python:3.11-slim AS builder
#
# # Dependencias del sistema
# RUN apt-get update && apt-get install -y \
#     curl \
#     libgl1 \
#     libglib2.0-0 \
#     tesseract-ocr \
#     poppler-utils \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*
#
# # Instalar Rust y compilar el binario
# RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
# ENV PATH="/root/.cargo/bin:${PATH}"
# RUN cargo install canvas-downloader
#
# # ── Imagen final ──────────────────────────────────────────────
# FROM python:3.11-slim
#
# RUN apt-get update && apt-get install -y \
#     curl \
#     libgl1 \
#     libglib2.0-0 \
#     tesseract-ocr \
#     poppler-utils \
#     && rm -rf /var/lib/apt/lists/*
#
# WORKDIR /app
#
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir docling
#
# COPY . .
# COPY --from=builder /root/.cargo/bin/canvas-downloader \
#      ETL/EXTRACT/extract-tools/canvas-downloader
#
# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#
#
#
#
#
#
#




FROM python:3.11-slim

WORKDIR /app




# RUST
# Dependencies for fast-api Docling
RUN apt-get update && apt-get install -y \
curl \
libgl1 \
libglib2.0-0 \
tesseract-ocr \
poppler-utils \
gcc \
&& rm -rf /var/lib/apt/lists/*

# instalar Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir docling

COPY . .


RUN cargo install canvas-downloader \
&& cp /root/.cargo/bin/canvas-downloader /app/ETL/EXTRACT/extract-tools/canvas-downloader


CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

