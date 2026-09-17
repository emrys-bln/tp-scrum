from pymongo import MongoClient

# URI de connexion MongoDB (local ou conteneurisé)
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)

# Instance de la base de données
db = client["tp_scrum_db"]