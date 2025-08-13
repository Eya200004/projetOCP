from flask import request, render_template, redirect, url_for
from .Database import get_db_connection
from . import app
from flask import jsonify, request
from app.ML_model import predire_besoin
from datetime import datetime



UTILISATEUR_PAR_DEFAUT = "admin"

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/equipements', methods=['GET'])
def afficher_equipements():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Equipements")
    equipements = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('equipements.html', equipements=equipements)

@app.route('/ajouter_equipement', methods=['GET'])
def formulaire_ajout():
    return render_template('ajouter_equipement.html')

@app.route('/ajouter_equipement', methods=['POST'])
def ajouter_equipement():
    nom = request.form['nom']
    categorie = request.form['categorie']
    quantite = int(request.form['quantite'])

    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute("""
        INSERT INTO Equipements (nom, categorie, quantite, date_ajout)
        VALUES (%s, %s, %s, CURDATE())
    """, (nom, categorie, quantite))

    equipement_id = cursor.lastrowid  

    
    cursor.execute("""
        INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
        VALUES (%s, %s, 'entrée', %s, CURDATE())
    """, (UTILISATEUR_PAR_DEFAUT, equipement_id, quantite))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('afficher_equipements'))

@app.route('/modifier_equipement/<int:equipement_id>', methods=['GET', 'POST'])
def modifier_equipement(equipement_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        nouvelle_quantite = int(request.form['quantite'])

        
        cursor.execute("SELECT quantite FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
        ancienne = cursor.fetchone()
        ancienne_quantite = ancienne['quantite'] if ancienne else 0

        
        cursor.execute("""
            UPDATE Equipements
            SET nom = %s, categorie = %s, quantite = %s
            WHERE Equipement_id = %s
        """, (nom, categorie, nouvelle_quantite, equipement_id))

        #
        difference = nouvelle_quantite - ancienne_quantite
        if difference != 0:
            type_mouvement = 'entrée' if difference > 0 else 'sortie'
            cursor.execute("""
                INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
                VALUES (%s, %s, %s, %s, CURDATE())
            """, (UTILISATEUR_PAR_DEFAUT, equipement_id, type_mouvement, abs(difference)))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('afficher_equipements'))

    else:  
        cursor.execute("SELECT * FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
        equipement = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('modifier_equipement.html', equipement=equipement)

@app.route('/supprimer_equipement/<int:equipement_id>', methods=['GET'])
def supprimer_equipement(equipement_id):
    conn = get_db_connection()
    cursor = conn.cursor()

   
    cursor.execute("SELECT quantite FROM Equipements WHERE Equipement_id = %s", (equipement_id,))
    result = cursor.fetchone()

    if result:
        quantite = result[0]  

        
        cursor.execute("""
            INSERT INTO Mouvements (nom_utilisateur, Equipement_id, type_mouvement, quantite, date_mouvement)
            VALUES (%s, %s, 'sortie', %s, CURDATE())
        """, (UTILISATEUR_PAR_DEFAUT, equipement_id, quantite))

        
        cursor.execute("DELETE FROM Equipements WHERE Equipement_id = %s", (equipement_id,))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('afficher_equipements'))


@app.route('/prevoir_reapprovisionnement', methods=['POST'])
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

    
@app.route('/prevision', methods=['GET'])
def page_prevision():
    return render_template('prevision.html')


