# ---- Base Image ----
# Use an official Python runtime as the base image.
# Using a slim version is efficient. Pinning to a specific version ensures reproducibility.
# We'll use Python 3.11 as it's recent and well-supported.
FROM python:3.11-slim-bullseye

# ---- Set Working Directory ----
# Set the working directory inside the container to /app.
# All commands that follow will be executed from this directory.
WORKDIR /app

# ---- Copy Requirements ----
# Copy the requirements.txt file into the container at /app/requirements.txt.
# This is done before copying the rest of the code to leverage Docker's layer caching:
# if requirements.txt doesn't change, this layer won't need to be rebuilt.
COPY requirements.txt ./

# ---- Install Dependencies ----
# Install Python packages from requirements.txt.
# --no-cache-dir reduces the image size by not storing downloaded package caches.
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
# Copy the rest of the application's source code into the container at /app.
# The '.' signifies copying all files in the current directory (which is /app after WORKDIR).
COPY . .

# ---- Expose Port (Best Practice, though not directly used by bot) ----
# Expose port 80. While Discord bots don't listen on HTTP ports for Discord communication,
# web hosting platforms often expect a port to be exposed for health checks or typical web server structure.
EXPOSE 80

# ---- Define Startup Command ----
# This is the command that will be executed when the container starts.
# It tells the container to run your bot's main script.
CMD ["python", "bot.py"]
