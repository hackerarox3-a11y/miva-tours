from flask import Flask, jsonify, request, send_from_directory
import re
import sqlite3
from datetime import date, datetime

app = Flask(__name__)
DB_PATH = "reservations.db"

DESTINATIONS = [
    {"nom": "Casablanca", "prix": "599 000 FCFA", "image": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&q=80", "description": "La perle du Maroc : mosquée Hassan II, médina et cuisine raffinée."},
    {"nom": "Paris", "prix": "À partir de 450 000 FCFA", "image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80", "description": "La ville lumière : Tour Eiffel, musées et shopping."},
    {"nom": "Bali", "prix": "850 000 FCFA", "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&q=80", "description": "Plages paradisiaques, temples et rizières en terrasses."},
    {"nom": "Johannesburg", "prix": "720 000 FCFA", "image": "https://images.unsplash.com/photo-1568067894394-ef388958a1e2?w=800&q=80", "description": "Safari, culture sud-africaine et histoire vibrante."},
    {"nom": "Zanzibar", "prix": "599 000 FCFA", "image": "https://images.unsplash.com/photo-1505881502353-a1986add3762?w=800&q=80", "description": "Île aux épices : sable blanc, lagons turquoise et Stone Town."},
    {"nom": "Seychelles", "prix": "Sur demande", "image": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?w=800&q=80", "description": "L'archipel de rêve de l'océan Indien, plages préservées."},
    {"nom": "Dubaï", "prix": "Sur demande", "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&q=80", "description": "Gratte-ciels, désert, tourisme médical et luxe."}
]

SERVICES = ["Billeterie", "Hôtellerie", "Tourisme", "MICE", "Location voitures",
            "Assurances", "Assistance aéroport", "Transfert argent"]

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@app.route('/reservation', methods=['POST'])
def reservation():
    data = request.get_json(force=True, silent=True) or {}
    nom = (data.get('nom') or '').strip()
    email = (data.get('email') or '').strip()
    telephone = (data.get('telephone') or '').strip()
    destination = (data.get('destination') or '').strip()
    depart = (data.get('depart') or '').strip()
    retour = (data.get('retour') or '').strip()
    message = (data.get('message') or '').strip()
    voyageurs = data.get('voyageurs', 1)

    erreurs = []
    if not nom:
        erreurs.append("Le nom est requis.")
    if not EMAIL_RE.match(email):
        erreurs.append("L'adresse email est invalide.")
    if not destination:
        erreurs.append("La destination est requise.")
    elif destination not in [d["nom"] for d in DESTINATIONS]:
        erreurs.append("Destination inconnue.")
    try:
        depart_dt = datetime.strptime(depart, "%Y-%m-%d").date()
        if depart_dt < date.today():
            erreurs.append("La date de départ ne peut pas être dans le passé.")
    except ValueError:
        depart_dt = None
        erreurs.append("La date de départ est invalide.")
    if retour:
        try:
            retour_dt = datetime.strptime(retour, "%Y-%m-%d").date()
            if depart_dt and retour_dt <= depart_dt:
                erreurs.append("Le retour doit être après le départ.")
        except ValueError:
            erreurs.append("La date de retour est invalide.")
    try:
        voyageurs = int(voyageurs)
        if not 1 <= voyageurs <= 30:
            erreurs.append("Le nombre de voyageurs doit être entre 1 et 30.")
    except (TypeError, ValueError):
        erreurs.append("Le nombre de voyageurs est invalide.")

    if erreurs:
        return jsonify({"status": "erreur", "erreurs": erreurs}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO reservations (nom, email, telephone, destination, depart, retour, voyageurs, message, cree_le) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (nom, email, telephone, destination, depart, retour or None, voyageurs, message,
         datetime.now().isoformat(timespec='seconds'))
    )
    conn.commit()
    reference = f"MV-{cur.lastrowid:05d}"
    conn.close()

    return jsonify({
        "status": "reçu",
        "reference": reference,
        "message": f"Réservation {reference} enregistrée. Un conseiller vous rappelle sous 24h."
    }), 201


@app.route('/reservations', methods=['GET'])
def reservations():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, nom, email, telephone, destination, depart, retour, voyageurs, message, statut, cree_le "
        "FROM reservations ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT NOT NULL,
            telephone TEXT,
            destination TEXT NOT NULL,
            depart TEXT NOT NULL,
            retour TEXT,
            voyageurs INTEGER NOT NULL DEFAULT 1,
            message TEXT,
            statut TEXT NOT NULL DEFAULT 'en attente',
            cree_le TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    return send_from_directory(app.root_path, 'index.html')


@app.route('/logo.png')
def logo_png():
    return send_from_directory(app.root_path, 'logo.png')


@app.route('/logo.jpg')
def logo_jpg():
    return send_from_directory(app.root_path, 'logo.jpg')


@app.route('/api/info')
def info():
    return jsonify({
        "agence": "Miva Tours",
        "ville": "Abidjan, Cocody",
        "contact": "+225 07 08 10 40 40",
        "email": "contact@mivatours.ci",
        "services": SERVICES
    })


@app.route('/destinations')
def destinations():
    return jsonify(DESTINATIONS)


@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json(force=True, silent=True) or {}
    nom = (data.get('nom') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    erreurs = []
    if not nom:
        erreurs.append("Le nom est requis.")
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        erreurs.append("L'adresse email est invalide.")
    if not message:
        erreurs.append("Le message est requis.")

    if erreurs:
        return jsonify({"status": "erreur", "erreurs": erreurs}), 400

    CONTACTS.append({"nom": nom, "email": email, "message": message})
    return jsonify({
        "status": "reçu",
        "message": "Votre demande est en cours. Un conseiller vous répond sous 24h."
    }), 201


@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "erreur", "message": "Page introuvable"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

