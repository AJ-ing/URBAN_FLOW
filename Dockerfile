FROM python:3.12-slim

# Install system dependencies for pygame, display framebuffers, and testing
RUN apt-get update && apt-get install -y \
    xvfb \
    freeglut3-dev \
    python3-sdl2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

# Set dummy SDL video driver by default
ENV SDL_VIDEODRIVER=dummy
ENV SDL_AUDIODRIVER=dummy

# Default to running verification tests
CMD ["python", "-m", "pytest"]
