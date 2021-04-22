# SmartEMR Imaging
## Medical Imaging Web-Service

A web-service built using Python for storing, updating, classifying and returning relevant medical images. This is part of a microservice architecture for SmartEMR (Project by Team 2 of UConn Computer Science & Engineering Senior Design Project).

## Features
- Uploading of medical imaging data to new or existing profiles
    - Inputs: Patient ID, Tags and descriptors of image (separated by commas), Date and time of medical image, Medical image file
    - Returns: Success message (uploads data to database)
- Querying of Patient Profile(s)
    - Input: Patient ID
    - Returns: All images with their associated descriptors, time, and date information
- Querying by Patient ID or Tags
    - Input (can leave either field null): Patient ID, Tags
    - Returns: Images which satisfy specified input criteria
- Querying by Natural Language
    - Input: Natural Language Query
    - Returns: Images satifying parameters specified in Natural Language Query
- Medical Image Classification
    - Input: Medical Image
    - Returns: Array of all image tags and descriptors as classified using PyTorch and the MONAI framework

## Running SmartEMR Imaging
### Creating a virtual environment
On macOS and Linux:
```
python3 -m venv env
```
On Windows:
```
py -m venv env
```

### Activating a virtual environment
On macOS and Linux:
```
source env/bin/activate
```
On Windows:
```
.\env\Scripts\activate
```

### Installing dependancies
```
pip3 install -r requirements.txt
```

### Setting up environment variables
Within ```SmartEMR_Imaging/SmartEMR_Imaging```, create a ```.env``` file with the following:
```
SECRET_KEY=<KEY>
MONGO_URI=<URI>
```
```MONGO_URI``` will refer to the URI of a MongoDB instance. ```SECRET_KEY``` is a key that will be used to store cookies for the web-application. A key can be generated in the following script:
```
import secrets
secrets.token_hex(16)
```

### Running the application
Once all of the previous steps have been followed and the environment variables are instantiated, you can execute the following within the root of the directory:
```
python3 app.py
```

For a development server without debug mode:
```
flask run
```

For a production server:
```
gunicorn --bind 0.0.0.0:5054 wsgi:app
```
