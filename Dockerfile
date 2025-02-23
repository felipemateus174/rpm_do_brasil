# Usa Python 3.11 slim para manter a imagem leve
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Atualiza o sistema e instala dependências do sistema necessárias para Xvfb e Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
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

# Copia o arquivo de dependências Python
COPY requirements.txt .

# Instala as dependências Python do requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Instala o pacote browser-use (assumindo que é necessário separadamente)
RUN pip install --no-cache-dir browser-use

# Instala o Playwright e o navegador Chromium
RUN python -m playwright install chromium

# Define variáveis de ambiente para Playwright e execução
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Copia o restante do código-fonte para o contêiner
COPY . .

# Expõe a porta para conexão externa
EXPOSE 8085

# Comando de inicialização com Xvfb e Gunicorn para rodar a aplicação
CMD ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "gunicorn", "-w", "2", "-b", "0.0.0.0:8085", "browser_use_rpm_do_brasil:app"]
