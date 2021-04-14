from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mongoengine import MongoEngine, Document
from flask_login import LoginManager
from dotenv import load_dotenv
from SmartEMR_Imaging.utils.idb_queries import IDB_Connections
import os

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGODB_SETTINGS'] = {
    'host': os.getenv('MONGO_URI')
}
db = MongoEngine(app)
mongo = PyMongo(app)
query = IDB_Connections(mongo)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from SmartEMR_Imaging import routes