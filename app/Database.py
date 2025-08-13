import mysql.connector
from config import db_config

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn
