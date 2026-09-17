# tp-scrum
Repertoire github global du TP méthodes agiles






Structure du document User (Utilisateur)

_id (Type : ObjectId de MongoDB) : Identifiant unique de l'utilisateur (Exemple : ObjectId("65e4a1b2c3d4e5f6a7b8c9d0"))

username (Type : str) : Nom de connexion (Exemple : "jean_dupont")

email (Type : str) : Adresse e-mail (Exemple : "jean.dupont@email.com")

password_hash (Type : str) : Mot de passe sécurisé et haché (Exemple : "$2b$12$eI... (hash bcrypt)")

role (Type : str) : Rôle de l'utilisateur parmi les valeurs autorisées "user", "technician", ou "admin" (Exemple : "user")






Structure mise à jour du Ticket

_id (Type : ObjectId) : Identifiant unique du ticket.

issuer (Type : ObjectId ou str) : ID de l'utilisateur qui a émis le ticket (Exemple : ObjectId("65e4a1b2c3d4e5f6a7b8c9d0")).

created_at (Type : datetime) : Date et heure exactes de création (Exemple : datetime.utcnow()).

assigned_technician (Type : ObjectId, str ou None) : ID du technicien assigné, ou None si le ticket n'est pas encore pris en charge.

description (Type : str) : Description détaillée du problème (Exemple : "Erreur 500 sur la page de paiement").

technician_comment (Type : str) : Commentaire du technicien/admin (Exemple : "Corrigé via le commit #42").

client_validation (Type : bool) : Validation du client (True / False).

technician_validation (Type : bool) : Validation du technicien/admin (True / False).

status (Type : str) : État du ticket parmi "En attente", "En cours", "Terminé".
