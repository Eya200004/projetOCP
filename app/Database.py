import mysql.connector
from config import db_config
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

class User(UserMixin):
    def __init__(self, id, email, password_hash, role='user', last_login=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.last_login = last_login

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, password_hash, role, last_login FROM Users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(
                row['id'], row['email'], row['password_hash'],
                row.get('role', 'user'), row.get('last_login')
            )
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, password_hash, role, last_login FROM Users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(
                row['id'], row['email'], row['password_hash'],
                row.get('role', 'user'), row.get('last_login')
            )
        return None

    
    @staticmethod
    def create(email, password, role='user'):
        """Crée un utilisateur et renvoie l'objet User."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        pw_hash = generate_password_hash(password)
        now = datetime.now(timezone.utc)

        cursor.execute(
        "INSERT INTO Users (email, password_hash, role, last_login) VALUES (%s, %s, %s, %s)",
        (email, pw_hash, role, now)
        )
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT id, email, password_hash, role, last_login FROM Users WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(row['id'], row['email'], row['password_hash'], row['role'], row['last_login'])


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Met à jour la date de dernière connexion de l'utilisateur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc)
        cursor.execute(
            "UPDATE Users SET last_login = %s WHERE id = %s",
            (now, self.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        self.last_login = now
    
    @staticmethod
    def delete(user_id):
        """Supprimer un utilisateur par son ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()


