# app/routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify,render_template
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash

from app import app
from app.Database import get_db_connection
from .Database import User          
from app.ML_model import predire_besoin




@app.route('/')
def accueil():
    return render_template('accueil.html')




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        
        user = User.get_by_email(email)

        if user and user.check_password(password):
            login_user(user)

            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE Users SET last_login=%s WHERE id=%s", (datetime.now(), user.id))
            conn.commit()
            cur.close()
            conn.close()
            
            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('mon_compte'))
        else:
            flash("Email ou mot de passe incorrect")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.")
    return redirect(url_for("login"))



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        if User.get_by_email(email):
            flash("Email déjà utilisé.")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Users (email, password_hash, role) VALUES (%s, %s, %s)",
                    (email, hashed_pw, "user"))
        conn.commit()
        cur.close()
        conn.close()

      
        user = User.get_by_email(email)
        login_user(user)

        flash("Inscription réussie ! Bienvenue !")
        return redirect(url_for("mon_compte"))  

    return render_template("register.html")


#page utilisat

@app.route("/mon_compte")
@login_required
def mon_compte():
    return render_template("mon_compte.html", user=current_user)


# admin dashboard

@app.route("/dashboard")
@login_required
def dashboard():
    # Seul l'admin peut voir le dashboard
    if getattr(current_user, "role", "user") != "admin":
        return "Accès refusé", 403

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, email, role, last_login FROM Users ORDER BY id")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboard.html", users=users)


# equipement(PROTÉGÉ)

@app.route('/equipements', methods=['GET'])
@login_required
def afficher_equipements():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Equipements")
    equipements = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('equipements.html', equipements=equipements)


@app.route('/ajouter_equipement', methods=['GET', 'POST'])
@login_required
def ajouter_equipement():
    if request.method == 'GET':
        return render_template('ajouter_equipement.html')

    
    nom = request.form['nom']
    categorie = request.form['categorie']
    quantite = int(request.form['quantite'])

    conn = get_db_connection()
    cur = conn.cursor()

    #Ajouter l’équipement
    cur.execute("""
        INSERT INTO Equipements (nom, categorie, quantite, date_ajout)
        VALUES (%s, %s, %s, CURDATE())
    """, (nom, categorie, quantite))
    equipement_id = cur.lastrowid

    # Journaliser le mouvement (utilisateur connecté)
    nom_utilisateur = getattr(current_user, "username", "inconnu")
    cur.execute("""
        INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
        VALUES (%s, %s, 'entrée', %s, CURDATE())
    """, (nom_utilisateur, equipement_id, quantite))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('afficher_equipements'))


@app.route('/modifier_equipement/<int:equipement_id>', methods=['GET', 'POST'])
@login_required
def modifier_equipement(equipement_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        nouvelle_quantite = int(request.form['quantite'])

        
        cur.execute("SELECT quantite FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
        row = cur.fetchone()
        ancienne_quantite = row['quantite'] if row else 0

        cur.execute("""
            UPDATE Equipements
            SET nom = %s, categorie = %s, quantite = %s
            WHERE Equipement_id = %s
        """, (nom, categorie, nouvelle_quantite, equipement_id))

       
        difference = nouvelle_quantite - ancienne_quantite
        if difference != 0:
            type_mouvement = 'entrée' if difference > 0 else 'sortie'
            nom_utilisateur = getattr(current_user, "username", "inconnu")
            cur.execute("""
                INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
                VALUES (%s, %s, %s, %s, CURDATE())
            """, (nom_utilisateur, equipement_id, type_mouvement, abs(difference)))

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('afficher_equipements'))

    
    cur.execute("SELECT * FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
    equipement = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('modifier_equipement.html', equipement=equipement)


@app.route('/supprimer_equipement/<int:equipement_id>', methods=['POST'])
@login_required
def supprimer_equipement(equipement_id):
    conn = get_db_connection()
    cur = conn.cursor()

    
    cur.execute("SELECT quantite FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
    result = cur.fetchone()

    if result:
        quantite = result[0]
        nom_utilisateur = getattr(current_user, "username", "inconnu")

        cur.execute("""
            INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
            VALUES (%s, %s, 'sortie', %s, CURDATE())
        """, (nom_utilisateur, equipement_id, quantite))

        cur.execute("DELETE FROM Equipements WHERE Equipement_id = %s", (equipement_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('afficher_equipements'))


#prevision (PROTÉGÉ) 

@app.route('/prevision', methods=['GET'])
@login_required
def page_prevision():
    return render_template('prevision.html')


@app.route('/prevoir_reapprovisionnement', methods=['POST'])
@login_required
def prevoir_reapprovisionnement():
    try:
        data = request.get_json()
        equipement_id = int(data.get('equipement_id'))
        date_future = data.get('date_future')

        result = predire_besoin(equipement_id, date_future)

        if isinstance(result, str):
            return jsonify({'error': result}), 400

        return jsonify({
            'equipement_id': equipement_id,
            'date': date_future,
            'prediction': result
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erreur serveur : {str(e)}'}), 500


# recherche(peut rester public si tu veux)

@app.route("/search_equipement")
def search_equipement():
    query = request.args.get("query", "")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT nom FROM Equipements WHERE nom LIKE %s LIMIT 5", (f"%{query}%",))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([row["nom"] for row in result])
