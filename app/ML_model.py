import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from config import charger_donnees_mouvements
import numpy as np


def entrainer_modele():
    df = charger_donnees_mouvements()

    if df.empty:
        return None, "Pas assez de données pour entraîner le modèle."

    try:
        df['timestamp'] = pd.to_datetime(df['date'], errors='coerce')  
        df = df.dropna(subset=['timestamp', 'Equipement_id', 'sorties'])  

        df['timestamp'] = df['timestamp'].astype('int64') // 10**9  

        X = df[['timestamp', 'Equipement_id']]
        y = df['sorties']

        model = LinearRegression()
        model.fit(X, y)

        return model, None  
    except Exception as e:
        return None, f"Erreur lors de l'entraînement : {str(e)}"

def predire_besoin(equipement_id, date_future):
    model, erreur = entrainer_modele()
    if erreur:
        return erreur

    try:
        timestamp = pd.to_datetime(date_future).value // 10**9
    except Exception:
        return {"error": "Format de date invalide"}

    X_pred = np.array([[timestamp, equipement_id]])
    y_pred = model.predict(X_pred)
    prediction = max(0, round(y_pred[0]))

    return {"prediction": prediction}
