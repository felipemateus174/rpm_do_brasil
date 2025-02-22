# Usa Python 3.11 slim para manter a imagem leve
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala o browser-use e Playwright
RUN pip install --no-cache-dir browser-use && python -m playwright install

# Define variáveis de ambiente para Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Instala dependências do sistema para Playwright e Xvfb
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
    wget \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# Instala Playwright e os navegadores necessários
RUN python -m playwright install chromium

# Copia o código-fonte para o contêiner
COPY . .

# Expõe a porta para conexão externa
EXPOSE 8085

# Configura variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Comando de inicialização usando Gunicorn para melhor performance
CMD ["xvfb-run", "--server-args='-screen 0 1920x1080x24'", "gunicorn", "-w", "2", "-b", "0.0.0.0:8085", "browser_use_rpm_do_brasil:app"]
