# FROM python:3.10-slim

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     libgl1 \
#     libglib2.0-0 \
#     tesseract-ocr \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# COPY requirements.txt .

# RUN pip install --upgrade pip setuptools wheel

# # 1. Install numpy first (critical for torch & whisper)
# RUN pip install numpy --no-cache-dir

# # 2. Install torch CPU-only from official index (NOT from requirements.txt)
# RUN pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

# # 3. Install all other requirements
# RUN pip install --no-cache-dir -r requirements.txt

# # 4. MAKE SURE numpy stays installed (final override)
# RUN pip install --force-reinstall numpy --no-cache-dir

# COPY ./app ./app

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM python:3.10-slim

# ----- System dependencies -----
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ----- Install ONLY dependencies (cached layer) -----
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

RUN pip install numpy --no-cache-dir

RUN pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --force-reinstall numpy --no-cache-dir

# ----- Do NOT copy code here (bind-mounted by docker-compose) -----

# ----- Uvicorn server -----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
