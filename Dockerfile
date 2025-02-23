# Imagem base com Python 3.11
FROM python:3.11-slim

# Instala dependências do sistema, incluindo o xvfb
RUN apt-get update && apt-get install -y xvfb && apt-get clean && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia arquivos essenciais para o container
COPY requirements.txt ./
COPY .env ./

# Instala as dependências Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que sua aplicação utiliza (se necessário, ex: 8085)
EXPOSE 8085

# Comando para iniciar a aplicação com xvfb-run
CMD ["xvfb-run", "python3.11", "teste_server.py"]
