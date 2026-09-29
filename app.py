from database import db
from flask import Flask, jsonify
from routes.ticket import ticket_bp  # Import du blueprint des tickets

app = Flask(__name__)
app.secret_key = (
    "cle_secrete_temporaire"  # Nécessaire pour la gestion des sessions
)

# Enregistrement du Blueprint des tickets
app.register_blueprint(ticket_bp)


@app.route("/")
def home():
  return jsonify({
      "message": "Bienvenue sur l'API du gestionnaire de tickets (TP Scrum)",
      "status": "online",
  })


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)