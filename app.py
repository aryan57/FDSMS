import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore
import json
from flask import Flask, render_template, url_for, request 
from functools import wraps

# this is a comment

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()

JWT_GLOBAL =""

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('authorization'):
            return {'message': 'No token provided'},400
        try:
            user = auth.verify_id_token(request.headers['authorization'])
            request.user = user
        except:
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap

@app.route('/api/userinfo')
@check_token
def userinfo():
    return {'data': users}, 200

@app.route('/api/signup', methods=['POST','GET'])
def signup():
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    # photo = request.form['photo']
    # confirmPassword = request.form['confirmPassword']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    if email is None or password is None:
        return {'message': 'Error missing email or password'},400
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email
        }
        db.collection("customers").document(user.uid).set(json_data)
        return {'message': f'Successfully created user {user.uid}'},200
    except:
        return {'message': 'Error creating user'},400

@app.route('/api/token')
def token():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        JWT_GLOBAL =jwt = user['idToken']
        return {'token': jwt}, 200
    except:
        return {'message': 'There was an error logging in'},400

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signUp():
    return render_template('signup.html')



@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup')
def customerSignup():
    return render_template('customerSignup.html')

@app.route('/restaurantSignup')
def restaurantSignup():
    return render_template('restaurantSignup.html')

@app.route('/deliveryAgentSignup')
def deliveryAgentSignup():
    return render_template('deliveryAgentSignup.html')

if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)