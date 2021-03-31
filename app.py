from flask import Flask, request, url_for, redirect, jsonify
from flask_cors import cross_origin
from flask_pymongo import PyMongo
from utils.idb_queries import IDB_Connections
import utils.html_strings as hts
import utils.monai_classifier as clf
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.environ['MONGO_URI']
mongo = PyMongo(app)
query = IDB_Connections(mongo)

@app.route('/')
def home():
  return hts.upload_images() + hts.find_patient_img() + hts.find_tagged_img() + hts.ui_test() + hts.nl_test() + hts.classifier_test()

# add profile and image data from index page form
@app.route('/create', methods=['POST'])
@cross_origin()
def create():
    if not request.form.get('pid') or not request.form.get('tags') or not request.form.get('date'):
        return 'Missing input values!'

    if 'image' in request.files:
        pid = request.form.get('pid')
        image = request.files['image']
        tags = [x.strip() for x in request.form.get('tags').split(',')]
        date = request.form.get('date')
        
        query.add_image_record(pid, image, tags, date)

        return 'Done!'
    
    else:
        return 'Did not upload image!'

# return corresponding file/image
@app.route('/file/<filename>')
@cross_origin()
def file(filename):
    return query.get_image(filename)

# POST method for NL query
@app.route('/processquery', methods=['POST'])
@cross_origin()
def processquery():
    req_data = request.get_json()
    nl_query = ''

    if req_data:
        nl_query = req_data['query']
    else:
        nl_query = request.form.get('query')

    return jsonify(query.process_nlq(nl_query))

# POST method for regular querying on UI
@app.route('/findimages', methods=['POST'])
@cross_origin()
def findimages():
    req_data = request.get_json()

    if req_data:
        pid = req_data['pid']
        text = req_data['tags']
    else:
        pid = request.form.get('pid')
        text = request.form.get('tags')
    
    tags = [x.strip() for x in text.split(',')]

    return jsonify(query.regq(pid, tags))

# GET method to find profile
@app.route('/profile/<pid>')
def profile(pid):
    user = mongo.db.users.find_one_or_404( {'pid' : pid} )
    res = f'''
        <h1>Patient ID: {user['pid']}</h1>
    '''
    
    for image in user['image_names']:
        tags_coll = mongo.db.tags.find_one_or_404( {'image_name' : image} )
        res += f'''Tags: { tags_coll['tags'] } Date: { tags_coll['date'] }<br>'''
        res += f''' <img src="{url_for('file', filename=image )}"> <br>'''

    return res

# POST method to find profile from index page form
@app.route('/findprofile', methods=['POST'])
def findprofile():
    user = mongo.db.users.find_one_or_404( {'pid' : request.form.get('pid')} )
    res = f'''
        <h1>Patient ID: {user['pid']}</h1>
    '''
    
    for image in user['image_names']:
        tags_coll = mongo.db.tags.find_one_or_404( {'image_name' : image} )
        res += f'''Tags: { tags_coll['tags'] } Date: { tags_coll['date'] }<br>'''
        res += f''' <img src="{url_for('file', filename=image )}"> <br>'''

    return res

# POST method to find images by tags from index page form
@app.route('/findtags', methods=['POST'])
def findtags():
    tags = [x.strip() for x in request.form.get('tags').split(',')]
    res = f'''
        <h1>Tags: {tags}</h1>
    '''

    for image in mongo.db.tags.find({'tags': {'$all': tags}}):
        res += f''' <img src="{url_for('file', filename=image['image_name'] )}"> '''
    
    return res

@app.route('/classify', methods=['POST'])
@cross_origin()
def classify():
    image = request.files['image']
    return jsonify(clf.classify_image(image))