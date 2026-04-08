FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Instala os browsers do Playwright
RUN playwright install chromium

COPY . .

EXPOSE 8085

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

CMD ["python", "browser_use_rpm_do_brasil.py"]
