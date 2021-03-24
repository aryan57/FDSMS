import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
import json
from flask import Flask, render_template, url_for, request, redirect , session
from functools import wraps
from flask_session import Session

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True
app.secret_key ='a very very very long string'

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred,json.load(open('fbConfig.json')))
pyrebase_pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
bucket = storage.bucket()
storage = pyrebase_pb.storage()


# blob = bucket.blob('mearyan.jpg')
# outfile='/home/aryan/Documents/Academic pdfs/Semester Coursework/Sem 4/se lab/FDSMS/pictures/a.jpg'
# blob.upload_from_filename(outfile)

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

@app.route('/signup/resturant', methods=['POST', 'GET'])
def restaurantsignup():
    message="Testing Restaurant"
    return redirect(url_for('signUp', message=message))

@app.route('/signup/delivery-agent', methods=['POST', 'GET'])
def deliveryAgentsignup():
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    local_file_path = request.form['local_file_path']
    message="Fail"
    print(name)
    if email is None or password is None:
        message="email or password is not provided"
        return redirect(url_for('deliveryAgentSignup', message=message))

    if mobile is None:
        mobile = ""
    if dob is None:
        dob = ""
    if name is None:
        name = ""
    if gender is None:
        gender = ""
    if area is None:
        area = ""

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        message="error creating user in firebase"
        return redirect(url_for('deliveryAgentSignup', message=message))
    try:
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email
        }
        print(name,dob,email,mobile)
        db.collection("customers").document(user.uid).set(json_data)
    except:
        message="error adding user text data in firestore"
        return redirect(url_for('deliveryAgentSignup'))
    try:

        # local_file_path = "/home/aryan/Documents/Academic pdfs/Semester Coursework/Sem 4/se lab/FDSMS/pictures/1.jpg"
        # storage_file_path = "customerProfilePics/"+user.uid+"jpg"
        # fbupload = storage.child(storage_file_path).put(local_file_path,user.uid)
        # print(fbupload)
        message="Success"
        return redirect(url_for('login'))
    except:
        message="error uploading photo in firebase storage"
        return redirect(url_for('deliveryAgentSignup'))

    

@app.route('/signup/api', methods=['POST','GET'])
def signup():

    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    local_file_path = request.form['local_file_path']
    message="Fail"

    if email is None or password is None:
        session['sign_message']="email or password is not provided"
        return redirect(url_for('customerSignup'))

    if mobile is None:
        mobile = ""
    if dob is None:
        dob = ""
    if name is None:
        name = ""
    if gender is None:
        gender = ""
    if area is None:
        area = ""

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('customerSignup'))
    try:
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email
        }
        print(name,dob,email,mobile)
        db.collection("customers").document(user.uid).set(json_data)
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('customerSignup'))
    try:

        # local_file_path = "/home/aryan/Documents/Academic pdfs/Semester Coursework/Sem 4/se lab/FDSMS/pictures/1.jpg"
        # storage_file_path = "customerProfilePics/"+user.uid+"jpg"
        # fbupload = storage.child(storage_file_path).put(local_file_path,user.uid)
        # print(fbupload)
        session['sign_message']="Success"
        return redirect(url_for('login'))
    except:
        session['sign_message']="error uploading photo in firebase storage"
        return redirect(url_for('customerSignup'))

@app.route('/api/token')
def token():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
        JWT_GLOBAL =jwt = user['idToken']
        return {'token': jwt}, 200
    except:
        return {'message': 'There was an error logging in'},400

@app.route('/')
def index():
    session['sign_message']="False"
    message=session['sign_message']
    return render_template('index.html', message=message)

@app.route('/Signup')
def signUp():
    return render_template('signup.html')



@app.route('/login')
def login():
    message=session['sign_message']
    return render_template('login.html', message=message)

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup')
def customerSignup():
    message=session['sign_message']
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