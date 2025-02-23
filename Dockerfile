# Usa Python 3.11 slim para manter a imagem leve
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala curl e outras dependências básicas necessárias para baixar e executar o script do uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala o uv usando o script oficial da Astral
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Adiciona o diretório do uv ao PATH
ENV PATH="/root/.local/bin:${PATH}"

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

# Instala as dependências do requirements.txt usando uv com a flag --system
RUN uv pip install --system --no-cache -r requirements.txt

# Instala o browser-use usando uv com a flag --system
RUN uv pip install --system --no-cache browser-use

# Instala o Playwright e o Chromium
RUN python -m playwright install chromium

# Define variáveis de ambiente para Playwright e execução
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Copia o restante do código-fonte para o contêiner
COPY . .

# Expõe a porta para conexão externa (se necessário)
EXPOSE 8085

# Comando de inicialização com Xvfb para rodar o script Python
CMD ["uv" "venv" "--python 3.11"]
CMD ["source" ".venv/bin/activate"]
CMD ["xvfb-run", "python3.11", "browser_use_rpm_do_brasil.py"]
