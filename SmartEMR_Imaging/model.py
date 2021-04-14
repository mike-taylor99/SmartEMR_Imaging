from flask_login import UserMixin
from SmartEMR_Imaging import login_manager, db

class User(UserMixin, db.Document):
    meta = {'collection': 'accounts'}
    email = db.StringField(max_length=30)
    password = db.StringField()
    verified = db.BooleanField()

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()
