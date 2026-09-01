from flask import Flask, jsonify, request

app = Flask(__name__)

DESTINATIONS = [
    {"nom":"Casablanca","prix":"599 000 FCFA"},
    {"nom":"Paris","prix":"À partir de 450 000 FCFA"},
    {"nom":"Bali","prix":"850 000 FCFA"},
    {"nom":"Johannesburg","prix":"720 000 FCFA"},
    {"nom":"Zanzibar","prix":"599 000 FCFA"}
]

@app.route('/')
def index():
    return jsonify({"agence":"Miva Tours","ville":"Abidjan, Cocody","contact":"+225 07 08 10 40 40","services":["Billeterie","Hôtellerie","Tourisme","MICE","Location voitures","Assurances","Assistance aéroport","Transfert argent"]})

@app.route('/destinations')
def destinations():
    return jsonify(DESTINATIONS)

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify({"status":"reçu","message":"Votre demande est en cours. Un conseiller vous répond sous 24h.","donnees":data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
