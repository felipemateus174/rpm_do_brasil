FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file first
COPY requirements.txt .

# Instala dependências do sistema, incluindo Node.js (necessário para Playwright)
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs \
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
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Instala pacotes Python (incluindo Playwright e browser-use)
RUN pip install --no-cache-dir -r requirements.txt

# Instala navegadores necessários para Playwright
RUN python -m playwright install --with-deps
RUN python -m playwright install chromium

# Instala atualizações específicas (opcional, mas você usou)
RUN pip install --upgrade browser-use
RUN pip install --upgrade pillow

# Copia o restante do código da aplicação
COPY . .

# Cria script de startup com Xvfb e execução do script Python
RUN echo '#!/bin/bash\n\
rm -f /tmp/.X*-lock\n\
Xvfb :99 -screen 0 1280x1024x24 &\n\
XVFB_PID=$!\n\
export DISPLAY=:99\n\
python browser_use_rpm_do_brasil.py\n\
kill -9 $XVFB_PID' > /app/start.sh && \
chmod +x /app/start.sh

# Exponha a porta da aplicação (se usar HTTP por ex. Flask)
EXPOSE 8085

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Comando padrão de entrada
CMD ["/app/start.sh"]
