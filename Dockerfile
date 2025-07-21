# Imagem base oficial do Playwright com navegadores incluídos (Chromium, Firefox, WebKit)
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências primeiro
COPY requirements.txt .

# Instala dependências Python do seu projeto
RUN pip install --no-cache-dir -r requirements.txt

# Atualiza browser-use e pillow, conforme você especificou
RUN pip install --upgrade browser-use pillow

# Copia todos os arquivos da aplicação
COPY . .

# Cria script de startup com Xvfb e execução do app
RUN echo '#!/bin/bash\n\
rm -f /tmp/.X*-lock\n\
Xvfb :99 -screen 0 1280x1024x24 &\n\
XVFB_PID=$!\n\
export DISPLAY=:99\n\
python browser_use_rpm_do_brasil.py\n\
kill -9 $XVFB_PID' > /app/start.sh && chmod +x /app/start.sh

# Exponha a porta usada pelo seu app (por ex: Flask)
EXPOSE 8085

# Variáveis de ambiente importantes
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Comando de inicialização padrão
CMD ["/app/start.sh"]
