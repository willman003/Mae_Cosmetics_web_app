import os
from flask import Flask

from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

import flask_login as login


app = Flask(__name__)
app.config['SECRET_KEY'] = "Impossible to guess"

#---CONFIG-----
app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config['CSRF_ENABLED'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///du_lieu/ql_mae.db?check_same_thread=False'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.init_app(app)

migrate=Migrate(app,db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

login_manager = login.LoginManager()
login_manager.init_app(app)
import Mae.xu_ly.xu_ly_model
# import Mae.app_Web_ban_hang
import Mae.app_quan_ly
import Mae.app_admin

if __name__ == '__main__':
    manager.run()
    
