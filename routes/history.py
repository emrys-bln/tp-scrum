"""Historique des tickets (utilisateur et technicien) avec filtres."""
import re
from datetime import datetime, timedelta
from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from database import db
from flask import Blueprint, abort, redirect, render_template, request, session, url_for

history_bp = Blueprint("history", __name__)

STATUSES = ["Soumis", "En cours", "Terminé"]


# Les rôles ne sont pas encore gérés (pas de login). Passer à True quand le login
# posera session["user_id"] et session["role"] : les routes redeviendront protégées.
ENFORCE_ROLES = False

# Utilisateurs de test, utilisés tant qu'il n'y a pas de session.
DEFAULT_USER_ID = "65e4a1b2c3d4e5f6a7b8c9d0"
DEFAULT_USER_USERNAME = "test_user"
DEFAULT_TECH_ID = "65e4a1b2c3d4e5f6a7b8c9d1"
DEFAULT_TECH_USERNAME = "technicien_test"


def role_required(*roles):
  """Contrôle du rôle, actif seulement si ENFORCE_ROLES est True."""

  def decorator(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
      if ENFORCE_ROLES:
        if "user_id" not in session:
          abort(401)  # à remplacer par une redirection vers la page de login
        if session.get("role") not in roles:
          abort(403)
      return view(*args, **kwargs)

    return wrapped

  return decorator


def id_variants(value):
  """Les ids peuvent être stockés en str ou en ObjectId : on accepte les deux."""
  variants = [str(value)]
  try:
    variants.append(ObjectId(str(value)))
  except InvalidId:
    pass
  return variants


def ensure_technician_session():
  """Simule le technicien connecté tant que l'authentification n'existe pas."""
  session.setdefault("technician_id", DEFAULT_TECH_ID)
  session.setdefault("technician_username", DEFAULT_TECH_USERNAME)
  return session["technician_id"]


def ensure_user_session():
  """Simule l'utilisateur connecté tant que l'authentification n'existe pas."""
  session.setdefault("user_id", DEFAULT_USER_ID)
  session.setdefault("username", DEFAULT_USER_USERNAME)
  return session["user_id"]


def ticket_object_id(ticket_id):
  try:
    return ObjectId(ticket_id)
  except InvalidId:
    abort(404)


def parse_filters(args):
  return {
      "q": args.get("q", "").strip(),
      "status": args.get("status", ""),
      "date_from": args.get("date_from", ""),
      "date_to": args.get("date_to", ""),
      "sort": "asc" if args.get("sort") == "asc" else "desc",
  }


def build_query(base, f):
  query = dict(base)
  if f["status"] in STATUSES:
    query["status"] = f["status"]
  if f["q"]:
    regex = {"$regex": re.escape(f["q"]), "$options": "i"}
    query["$or"] = [{"title": regex}, {"description": regex}]
  dates = {}
  try:
    if f["date_from"]:
      dates["$gte"] = datetime.strptime(f["date_from"], "%Y-%m-%d")
    if f["date_to"]:
      dates["$lt"] = datetime.strptime(f["date_to"], "%Y-%m-%d") + timedelta(
          days=1
      )
  except ValueError:
    dates = {}
  if dates:
    query["created_at"] = dates
  return query


def status_counts(base):
  counts = {s: 0 for s in STATUSES}
  for row in db.tickets.aggregate(
      [{"$match": base}, {"$group": {"_id": "$status", "n": {"$sum": 1}}}]
  ):
    if row["_id"] in counts:
      counts[row["_id"]] = row["n"]
  return counts


def attach_usernames(tickets):
  wanted = {str(t["issuer"]) for t in tickets} | {
      str(t["assigned_technician"])
      for t in tickets
      if t.get("assigned_technician")
  }
  oids = []
  for value in wanted:
    try:
      oids.append(ObjectId(value))
    except InvalidId:
      pass
  names = {
      str(u["_id"]): u["username"]
      for u in db.users.find({"_id": {"$in": oids}}, {"username": 1})
  }
  for t in tickets:
    issuer = str(t["issuer"])
    session_user = str(session.get("user_id"))
    fallback_name = (
        session.get("username")
        if issuer == session_user
        else DEFAULT_USER_USERNAME if issuer == DEFAULT_USER_ID else "Inconnu"
    )
    t["issuer_name"] = names.get(issuer, fallback_name)
    tech = t.get("assigned_technician")
    t["technician_name"] = (
      names.get(str(tech), session.get("technician_username", "Technicien"))
      if tech
      else None
    )
  return tickets


def render_history(template, base):
  f = parse_filters(request.args)
  order = 1 if f["sort"] == "asc" else -1
  tickets = list(db.tickets.find(build_query(base, f)).sort("created_at", order))
  return render_template(
      template,
      tickets=attach_usernames(tickets),
      filters=f,
      statuses=STATUSES,
      counts=status_counts(base),
      technician_id=session.get("technician_id", DEFAULT_TECH_ID),
  )


@history_bp.route("/user/history")
@role_required("user")
def user_history():
  user_id = ensure_user_session()
  return render_history(
      "user/history.html", {"issuer": {"$in": id_variants(user_id)}}
  )


@history_bp.route("/technician/history")
@role_required("technician", "admin")
def tech_history():
  return redirect(url_for("history.tech_dashboard"))


@history_bp.route("/technician/dashboard")
@role_required("technician", "admin")
def tech_dashboard():
  ensure_technician_session()
  return render_history("technician/dashboard.html", {})


@history_bp.post("/technician/tickets/<ticket_id>/claim")
@role_required("technician", "admin")
def claim_ticket(ticket_id):
  technician_id = ensure_technician_session()
  db.tickets.update_one(
      {
          "_id": ticket_object_id(ticket_id),
          "status": "Soumis",
          "assigned_technician": None,
      },
      {
          "$set": {
              "assigned_technician": technician_id,
              "status": "En cours",
          }
      },
  )
  return redirect(url_for("history.tech_dashboard"))


@history_bp.post("/technician/tickets/<ticket_id>/finish")
@role_required("technician", "admin")
def finish_ticket(ticket_id):
  technician_id = ensure_technician_session()
  db.tickets.update_one(
      {
          "_id": ticket_object_id(ticket_id),
          "assigned_technician": {"$in": id_variants(technician_id)},
          "status": "En cours",
      },
      {"$set": {"status": "Terminé"}},
  )
  return redirect(url_for("history.tech_dashboard"))
