from flask import Flask, request, url_for, redirect, jsonify
from flask_cors import cross_origin
from flask_pymongo import PyMongo
import string

import os
import torch
from monai.networks.nets import densenet121
from monai.transforms import (
    AddChannel,
    Compose,
    LoadImage,
    ScaleIntensity,
    ToTensor,
)

import makeModel
from makeModel import MedNISTDataset
from PIL import Image

import utils.html_strings as hts
from utils.idb_queries import IDB_Connections

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
        user = query.get_user(request.form.get('pid'))
        image = request.files['image']
        query.save_image(image.filename, image)

        tags = [x.strip() for x in request.form.get('tags').split(',')]
        query.add_img_tags(image.filename, tags, request.form.get('date'))
        
        if user:
            query.add_image_to_user(user, image.filename)

        else:
            query.create_user_record(request.form.get('pid'), image.filename)

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
    
    PIDs, tags = query.get_pids(), query.get_tags()
    
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in nl_query.split()]

    query_PIDs = []
    query_tags = []
    for word in stripped:
        if word in PIDs:
            query_PIDs.append(word)
        elif word in tags:
            query_tags.append(word)
        else:
            continue
    
    user_images = []
    tag_images = []

    for user in query_PIDs:
        user_images += query.get_user(user)['image_names']
    if query_tags:
        tag_images = [record['image_name'] for record in query.images_by_tags(query_tags)]

    if user_images and tag_images:
        images = list(set(user_images).intersection(set(tag_images)))
    elif user_images:
        images = user_images
    elif tag_images:
        images = tag_images
    else:
        images = []
        
    return jsonify(images)
    

# POST method for regular querying on UI
@app.route('/findimages', methods=['POST'])
@cross_origin()
def findimages():
    req_data = request.get_json()
    user = None

    if req_data:
        if req_data['pid']:
            user = query.get_user(req_data['pid'])
        text = req_data['tags']
    else:
        if request.form.get('pid'):
            user = query.get_user(request.form.get('pid'))
        text = request.form.get('tags')
    
    tags = [x.strip() for x in text.split(',')]

    user_images = None
    tag_images = None

    if user:
        user_images = user['image_names']
    if text:
        tag_images = [record['image_name'] for record in query.images_by_tags(tags)]
    
    images = []
    if user and text:
        for image in tag_images:
            if image in user_images:
                images.append(image)
    elif user:
        images = user_images
    elif text:
        images = tag_images

    return jsonify(images)

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
    # load image and make proper conversions
    image = request.files['image']
    im = Image.open(image)
    im = im.convert(mode='L')
    im = im.resize((64, 64))
    im.save('conversion.jpeg', 'JPEG')

    # define label attributes
    # class_names = ['AbdomenCT', 'BreastMRI', 'CXR', 'ChestCT', 'Hand', 'HeadCT']
    class_names = [['Abdomen CT Scan', 'CT Scan', 'Abdomen', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography', 'Abdominal'],
                    ['Breast MRI', 'Breast', 'MRI', 'Magnetic Resonance Imaging', 'Upper Ventral'], 
                    ['Chest X-Ray', 'Chest', 'X-Ray'], 
                    ['Chest CT Scan', 'CT Scan', 'Chest', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography'], 
                    ['Hand X-Ray', 'Hand', 'X-Ray'], 
                    ['Head CT Scan', 'Head', 'Brain', 'Brain Scan', 'CT Scan', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography']]
    num_class = len(class_names)

    # Define MONAI transforms, Dataset and Dataloader to process image
    val_transforms = Compose([LoadImage(image_only=True), AddChannel(), ScaleIntensity(), ToTensor()])
    test_ds = MedNISTDataset(['conversion.jpeg'], [0], val_transforms)
    test_loader = torch.utils.data.DataLoader(test_ds)

    # Define Network
    # device = torch.device("cuda:0")
    device = torch.device("cpu")
    model = densenet121(spatial_dims=2, in_channels=1, out_channels=num_class).to(device)

    # Make prediction
    # model.load_state_dict(torch.load("./MONAI_DATA_DIRECTORY/best_metric_model.pth"))
    model.load_state_dict(torch.load("./MONAI_DATA_DIRECTORY/best_metric_model_cpu.pth"))
    model.eval()
    y_true = list()
    y_pred = list()
    with torch.no_grad():
        for test_data in test_loader:
            test_images, test_labels = (
                test_data[0].to(device),
                test_data[1].to(device),
                )
            pred = model(test_images).argmax(dim=1)
            for i in range(len(pred)):
                y_true.append(test_labels[i].item())
                y_pred.append(pred[i].item())
    
    # clean up
    os.remove('conversion.jpeg')

    # print(class_names[y_pred[0]])
    return jsonify(class_names[y_pred[0]])