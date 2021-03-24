import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore
import json
from flask import Flask, render_template, url_for, request, redirect 
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

@app.route('/signup/api', methods=['POST','GET'])
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
        message="Success"
        return redirect(url_for('login', message=message))
    except:
        message="Fail"
        return redirect(url_for('customerSignup', message=message))

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
    message="None"
    return render_template('index.html', message=message)

@app.route('/Signup<message>')
def signUp(message):
    return render_template('signup.html', message=message)



@app.route('/login<message>')
def login(message):
    if message==None:
        print("No Message Recieved")
    else:
        print(message)
    # message=request.args['message']
    return render_template('login.html', message=message)

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup<message>')
def customerSignup(message):
    return render_template('customerSignup.html', message=message)

@app.route('/restaurantSignup')
def restaurantSignup():
    return render_template('restaurantSignup.html')

@app.route('/deliveryAgentSignup')
def deliveryAgentSignup():
    return render_template('deliveryAgentSignup.html')

if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)