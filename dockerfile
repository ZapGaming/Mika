# ---- Base Image ----
# Using a specific patch version for Python is often crucial for compatibility on deployment platforms.
# We are changing 'python:3.11-slim' to 'python:3.11.8-slim'.
FROM python:3.11.8-slim 

# ---- Set Working Directory ----
WORKDIR /app

# ---- Install Build Tools and Image Libraries ----
# Ensure these are installed before pip packages to avoid 'subprocess-exited-with-error'.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
    libffi-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy Requirements ----
COPY requirements.txt ./

# ---- Install Dependencies ----
# This command MUST come after the apt-get install lines.
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
COPY . .

# ---- Expose Port ----
EXPOSE 80

# ---- Define Startup Command ----
CMD ["python", "bot.py"]
