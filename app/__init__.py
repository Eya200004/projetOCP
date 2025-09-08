from flask import Flask
from flask_login import LoginManager
from .Database import User  
app = Flask(__name__)
from . import routes

app.secret_key = "change_this_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  



@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)   