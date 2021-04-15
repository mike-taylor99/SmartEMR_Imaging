# UConn Computer Science & Engineering Senior Design Project: Team 2
## Medical Imaging Web-Service

A Flask-based web-service for storing, updating, classifying and returning relevant medical images, part of SmartEMR (Project by Team 2 UConn CSE Senior Design Project).

### Features
- uploading of medical imaging data to new or existing profiles;
- querying of images using natural language inputs
- classification of medical image data to extract relevant descriptors using PyTorch and the MONAI framework

### Installation
To install the current release, download and navigate to the following repository and simply run (make a virtual environment if necessary):
```
pip3 install -r requirements.txt
```

Your will need to create a ```.env``` file within the root of the repository with the connection URI:
```
MONGO_URI=<URI>
```

### Links
- SmartEMR website: <>
- UConn CSE Senior Design Project: Team 2 Page: <>
- MONAI: <>
