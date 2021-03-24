import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
import json
from flask import Flask, render_template, url_for, request 
from functools import wraps

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True

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

@app.route('/api/signup', methods=['POST','GET'])
def signup():

    email = request.form['email']
    password = request.form['password']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    local_file_path = request.form['local_file_path']

    if email is None or password is None:
        return {'message': 'Error missing email or password'},400

    if mobile is None:
        mobile = ""
    if dob is None:
        dob = ""
    if name is None:
        name = ""
    if local_file_path is None:
        local_file_path = ""

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        return {'message': 'Error creating user'},400
    try:
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email
        }
        print(name,dob,email,mobile)
        db.collection("customers").document(user.uid).add(json_data)
    except:
        return {'message': 'Error adding user text data'},400
    try:

        local_file_path = "/home/aryan/Documents/Academic pdfs/Semester Coursework/Sem 4/se lab/FDSMS/pictures/1.jpg"
        storage_file_path = "customerProfilePics/"+user.uid+"jpg"
        fbupload = storage.child(storage_file_path).put(local_file_path,user.uid)
        print(fbupload)

        return {'message': f'Successfully created user {user.uid}'},200
    except:
        return {'message': 'Error uploading user profile picture'},400
    

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