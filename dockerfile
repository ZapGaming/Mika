# ---- Base Image ----
FROM python:3.11-slim-bullseye 

# ---- Set Working Directory ----
WORKDIR /app

# ---- Install Build Tools and Image Libraries ----
# Add these lines to install necessary packages for compiling Python dependencies like Pillow.
# RUN apt-get update installs the package lists.
# RUN apt-get install -y build-essential ... installs compilers and libraries.
# ... && rm -rf /var/lib/apt/lists/* cleans up the apt cache to reduce image size.
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
# Now that build tools are installed, pip should be able to install Pillow and other packages without errors.
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
COPY . .

# ---- Expose Port ----
EXPOSE 80

# ---- Define Startup Command ----
CMD ["python", "bot.py"]
