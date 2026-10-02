FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Définition d'une variable d'environnement par défaut pour MongoDB
ENV MONGO_URI="mongodb://localhost:27017/"

EXPOSE 5000

CMD ["python", "app.py"]