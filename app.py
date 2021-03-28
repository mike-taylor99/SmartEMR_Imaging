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

app = Flask(__name__)
app.config['MONGO_URI'] = os.environ['MONGO_URI']
mongo = PyMongo(app)

@app.route('/')
def home():
  return '''
    <div>Upload Patient Images and Tags: <br>
    <form method="POST" action="/create" enctype="multipart/form-data">
        <label>Patiient ID:</label>
        <input typr="text" name="pid">
        <label>Tags:</label>
        <input typr="text" name="tags">
        <label>Date:</label>
        <input typr="text" name="date">
        <input type="file" name="image">
        <input type="submit">
    </form>
    </div>
    
    <div>Find Patient Images: <br>
    <form method="POST" action="/findprofile" enctype="multipart/form-data">
        <label>Patient ID:</label>
        <input typr="text" name="pid">
        <input type="submit">
    </form>
    </div>

    <div>Find Images by Tag(s): <br>
    <form method="POST" action="/findtags" enctype="multipart/form-data">
        <label>Tags:</label>
        <input typr="text" name="tags">
        <input type="submit">
    </form>
    </div>

    <div>Web Service Connection Test: <br>
    <form method="POST" action="/findimages" enctype="multipart/form-data">
        <label>Patient ID:</label>
        <input typr="text" name="pid">
        <label>Tags:</label>
        <input typr="text" name="tags">
        <input type="submit">
    </form>
    </div>

    <div>NL Query Test: <br>
    <form method="POST" action="/processquery" enctype="multipart/form-data">
        <label>Query:</label>
        <input typr="text" name="query">
        <input type="submit">
    </form>
    </div>

    <div> Upload Image (Classification): <br>
    <form method="POST" action="/classify" enctype="multipart/form-data">
        <label>Image:</label>
        <input type="file" name="image">
        <input type="submit">
    </form>
    </div>
  '''

# add profile and image data from index page form
@app.route('/create', methods=['POST'])
@cross_origin()
def create():
    if not request.form.get('pid') or not request.form.get('tags') or not request.form.get('date'):
        return 'Missing input values!'

    if 'image' in request.files:
        user = mongo.db.users.find_one({'pid' : request.form.get('pid')})
        image = request.files['image']
        mongo.save_file(image.filename, image)

        tags = [x.strip() for x in request.form.get('tags').split(',')]
        mongo.db.tags.insert( {'image_name': image.filename, 'tags': tags, 'date': request.form.get('date')} )
        
        if user:
            user['image_names'].append(image.filename)
            user = mongo.db.users.save(user)

        else:
            mongo.db.users.insert({'pid' : request.form.get('pid'), 'image_names': [image.filename]})

        return 'Done!'
    
    else:
        return 'Did not upload image!'

# return corresponding file/image
@app.route('/file/<filename>')
@cross_origin()
def file(filename):
    return mongo.send_file(filename)

# POST method for NL query
@app.route('/processquery', methods=['POST'])
@cross_origin()
def processquery():
    req_data = request.get_json()
    query = ''

    if req_data:
        query = req_data['query']
    else:
        query = request.form.get('query')
    
    PIDs = set([user['pid'] for user in mongo.db.users.find({})])
    tags = set()
    for image in mongo.db.tags.find({}):
        for tag in image['tags']:
            tags.add(tag)
    
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in query.split()]

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
        user_images += mongo.db.users.find_one( {'pid' : user} )['image_names']
    if query_tags:
        tag_images = [image['image_name'] for image in mongo.db.tags.find({'tags': {'$all': query_tags}})]

    if user_images and tag_images:
        images = list(set(user_images).intersection(set(tag_images)))
    elif user_images:
        images = user_images
    elif tag_images:
        images = tag_images
    else:
        images = []
        
    return jsonify(images)
    

# POST method for Angular
@app.route('/findimages', methods=['POST'])
@cross_origin()
def findimages():
    req_data = request.get_json()
    user = None

    if req_data:
        if req_data['pid']:
            user = mongo.db.users.find_one( {'pid' : req_data['pid']} )
        text = req_data['tags']
    else:
        if request.form.get('pid'):
            user = mongo.db.users.find_one( {'pid' : request.form.get('pid')} )
        text = request.form.get('tags')
    
    tags = [x.strip() for x in text.split(',')]

    user_images = None
    tag_images = None

    if user:
        user_images = user['image_names']
    if text:
        tag_images = mongo.db.tags.find({'tags': {'$all': tags}})
    
    images = []
    if user and text:
        for image in tag_images:
            if image['image_name'] in user_images:
                images.append(image['image_name'])
    elif user:
        images = user_images
    elif text:
        for image in tag_images:
            images.append(image['image_name'])

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