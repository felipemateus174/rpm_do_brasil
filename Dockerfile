FROM ubuntu:24.04  # Usar a mesma base que o servidor do Easypanel

# Set working directory
WORKDIR /app

# Atualize e instale dependências básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (to leverage Docker layer caching)
COPY requirements.txt .

# Install Python dependencies first (including playwright)
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for Playwright using playwright install-deps
RUN playwright install-deps

# Instale dependências específicas para Xvfb, Playwright e Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11-xkb-utils \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-scalable \
    xserver-xorg-core \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers (required by browser-use)
RUN python -m playwright install && python -m playwright install chromium

# Copy application code
COPY . .

# Clean up any Xvfb lock files before starting and manage Xvfb process
RUN echo '#!/bin/bash\nrm -f /tmp/.X*-lock\nXvfb :99 -screen 0 1280x1024x24 &\nXVFB_PID=$!\nexport DISPLAY=:99\npython browser_use_rpm_do_brasil.py\nkill -9 $XVFB_PID' > /app/start.sh \
    && chmod +x /app/start.sh

# Expose port for Easypanel
EXPOSE 8085

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Command to start the application
CMD ["/app/start.sh"]
