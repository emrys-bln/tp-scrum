from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    # Optionnel : vérifier si l'utilisateur connecté est bien un admin
    # if session.get('role') != 'admin':
    #     return redirect(url_for('app.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # "user", "technician", ou "admin"

        # Validation basique
        if not username or not email or not password or not role:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('admin.create_user'))

        # Hachage sécurisé du mot de passe
        hashed_password = generate_password_hash(password)

        # Structure du document User définie dans le README
        user_data = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "role": role
        }

        # Insertion dans la collection "users" de MongoDB
        db.users.insert_one(user_data)
        flash(f"Utilisateur {username} ({role}) créé avec succès !", "success")
        return redirect(url_for('admin.create_user'))

    return render_template('admin/create_user.html')