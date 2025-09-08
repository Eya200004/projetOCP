import mysql.connector
from config import db_config

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.Database import get_db_connection


class User(UserMixin):
    def __init__(self, id, email, password_hash, role='user'):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def get_id(self):
        # Flask-Login s'attend à une string
        return str(self.id)

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, password_hash, role FROM Users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(row['id'], row['email'], row['password_hash'], row.get('role', 'user'))
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, password_hash, role FROM Users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(row['id'], row['email'], row['password_hash'], row.get('role', 'user'))
        return None

    @staticmethod
    def create(email, password, role='user'):
        """Crée un utilisateur et renvoie son id."""
        conn = get_db_connection()
        cursor = conn.cursor()
        pw_hash = generate_password_hash(password)   # <-- importé ici
        cursor.execute(
            "INSERT INTO Users (email, password_hash, role) VALUES (%s, %s, %s)",
            (email, pw_hash, role)
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return new_id

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)