"""Historique des tickets (utilisateur et technicien) avec filtres."""
import re
from datetime import datetime, timedelta
from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from database import db
from flask import Blueprint, abort, render_template, request, session

history_bp = Blueprint("history", __name__)

STATUSES = ["Soumis", "En cours", "Terminé"]


# Les rôles ne sont pas encore gérés (pas de login). Passer à True quand le login
# posera session["user_id"] et session["role"] : les routes redeviendront protégées.
ENFORCE_ROLES = False

# Utilisateurs de test, utilisés tant qu'il n'y a pas de session (même id que create_ticket)
# DEFAULT_USER_ID = "65e4a1b2c3d4e5f6a7b8c9d0"
# DEFAULT_TECH_ID = "65e4a1b2c3d4e5f6a7b8c9d1"


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
    t["issuer_name"] = names.get(str(t["issuer"]), "Inconnu")
    tech = t.get("assigned_technician")
    t["technician_name"] = names.get(str(tech)) if tech else None
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
  )


@history_bp.route("/user/history")
@role_required("user")
def user_history():
  # user_id = session.get("user_id", DEFAULT_USER_ID)
  user_id = session.get("user_id")
  return render_history(
      "user/history.html", {"issuer": {"$in": id_variants(user_id)}}
  )


@history_bp.route("/technician/history")
@role_required("technician", "admin")
def tech_history():
  # user_id = session.get("user_id", DEFAULT_TECH_ID)
  user_id = session.get("user_id")
  return render_history(
      "technician/history.html",
      {"assigned_technician": {"$in": id_variants(user_id)}},
  )