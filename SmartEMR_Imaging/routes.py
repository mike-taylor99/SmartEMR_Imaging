from flask import request, url_for, redirect, jsonify, render_template, flash, request
from flask_cors import cross_origin
from flask_login import login_user, current_user, logout_user, login_required
from SmartEMR_Imaging import app, bcrypt, mongo, query
from SmartEMR_Imaging.forms import RegistrationForm, LoginForm
from SmartEMR_Imaging.model import User
import SmartEMR_Imaging.utils.monai_classifier as clf

@app.route('/')
def home():
  return render_template('home.html')

@app.route("/query")
def about():
    return render_template('query.html', title='Query')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password, verified=False).save()
        flash(f'Account created for {form.username.data}! An admin will verify elgibility', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')

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
    patient = user['pid']
    data = []
    for image in user['image_names']:
        tags_coll = mongo.db.tags.find_one_or_404( {'image_name' : image} )
        entry = {
            'date': tags_coll['date'], 
            'tags': tags_coll['tags'],
            'image_src': url_for('file', filename=image )
        }
        data.append(entry)

    return render_template('patientImages.html', patient=patient, data=data)

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