from flask import Flask, request, url_for, redirect, jsonify
from flask_cors import cross_origin

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

@app.route('/')
def home():
  return '''
    <div> Upload Image: <br>
    <form method="POST" action="/classify" enctype="multipart/form-data">
        <label>Image:</label>
        <input type="file" name="image">
        <input type="submit">
  '''

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
    # model.load_state_dict(torch.load("./models/best_metric_model.pth"))
    model.load_state_dict(torch.load("./models/best_metric_model_cpu.pth"))
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