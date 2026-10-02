from datetime import datetime
from database import db
from flask import Blueprint, jsonify, render_template, request, session

# Création du Blueprint pour les tickets
ticket_bp = Blueprint("ticket", __name__, url_prefix="/tickets")


@ticket_bp.route("/create", methods=["GET", "POST"])
def create_ticket():
  # Simulation d'un utilisateur connecté pour le test
  if "user_id" not in session:
    session["user_id"] = "65e4a1b2c3d4e5f6a7b8c9d0"
    session["username"] = "test_user"

  if request.method == "POST":
    title = request.form.get("title")
    description = request.form.get("description")

    # Critère d'acceptation : Titre et Description obligatoires
    if not title or not description:
      return (
          jsonify({
              "error": (
                  "Le titre et la description sont obligatoires (Critère"
                  " d'acceptation)"
              )
          }),
          400,
      )

    # Structure du ticket avec la date UTC standard
    ticket_data = {
        "issuer": session.get("user_id"),
        "title": title,
        "description": description,
        "created_at": datetime.utcnow(),  # Format UTC standard
        "assigned_technician": None,
        "technician_comment": "",
        "client_validation": False,
        "technician_validation": False,
        "status": "Soumis",  # Statut initial automatique
    }

    # Insertion dans la collection "tickets" de MongoDB
    db.tickets.insert_one(ticket_data)

    # return jsonify({
    #     "success": True,
    #     "message": (
    #         "Ticket créé avec succès avec le statut initial 'Soumis'."
    #     ),
    # })

  # Renvoie le formulaire HTML si on accède en GET
  return render_template("user/create_ticket.html")