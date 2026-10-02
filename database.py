import os
from pymongo import MongoClient

# Récupère l'URI depuis les variables d'environnement, ou utilise localhost par défaut
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)

# Nom de la base de données
db = client["tp_scrum_db"]