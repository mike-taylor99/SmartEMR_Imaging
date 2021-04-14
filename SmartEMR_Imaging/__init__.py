from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from SmartEMR_Imaging.utils.idb_queries import IDB_Connections
import os

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo = PyMongo(app)
query = IDB_Connections(mongo)

from SmartEMR_Imaging import routes