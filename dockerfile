# ---- Base Image ----
# Using a specific Python version as confirmed by Render's support for "main release".
# We'll switch from "-slim" to the explicit version tag.
FROM python:3.11.8 

# ---- Set Working Directory ----
WORKDIR /app

# ---- Install Build Tools and Image Libraries ----
# These are crucial for compiling Python packages like Pillow from source.
# Keep these lines as they are to ensure Pillow can be built.
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
# Installs all Python packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
COPY . .

# ---- Expose Port ----
# Standard practice for web services, even if indirectly used by the bot for health checks.
EXPOSE 80

# ---- Define Startup Command ----
# The command to run your bot's main script.
CMD ["python", "bot.py"]
