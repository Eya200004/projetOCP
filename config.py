import pymysql
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

db_config = {

'host' : 'localhost',
'user' :'root',
'password' :'Aya/Karfi*0000', 
'database' : 'gestion_stock_ia'
}


def charger_donnees_mouvements():
    connection = pymysql.connect(**db_config)
    query = """
        SELECT 
            DATE(date_mouvement) as date, 
            Equipement_id,
            SUM(CASE WHEN type_mouvement = 'sortie' THEN quantite ELSE 0 END) AS sorties
        FROM Mouvements
        GROUP BY Equipement_id, DATE(date_mouvement)
        ORDER BY date ASC;
    """
    df = pd.read_sql(query, connection)
    connection.close()
    return df
