from os import name
import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
import json
from flask import Flask, render_template, url_for, request, redirect , session
from functools import wraps
import datetime
import requests
from requests.exceptions import HTTPError
# from flask_session import Session

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True
app.secret_key ='a very very very long string'

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred,json.load(open('fbConfig.json')))
pyrebase_pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
bucket = storage.bucket()
# storage = pyrebase_pb.storage()

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        try:
            if session['jwt_token']==None:
                session['sign_message']="No Token Provided. Try Logging In."
                return redirect(url_for('login'))
        except:
            session['sign_message']="No Token Provided. Try Logging In."
            return redirect(url_for('login'))
        try:
            session['jwt_token'] = pyrebase_pb.auth().refresh(session['refresh_token'])['idToken']
            user = auth.verify_id_token(session['jwt_token'])
            request.user = user
        except:
            session['sign_message']="Invalid Token Provided. Trying Logging again."
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

@app.route('/api/userinfo')
@check_token
def userinfo():
    return {'data'}, 200

@app.route('/signup/resturant', methods=['POST', 'GET'])
def restaurantsignup():
    email = request.form['email']
    password = request.form['password']
    area = request.form['area']
    name = request.form['name']
    local_file_obj = request.files['local_file_path']
    session['sign_message']="Fail"
    
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('restaurantSignup'))
    try:
        json_data = {
            "name" : name,
            "email" : email,
            "areaId" : "",
            "ratingId": "",
            "restaurantId" : user.uid,
            "restaurantPicSrc" : "",
        }
        db.collection("restaurant").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "restaurant"})
        
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('restaurantSignup'))
    try:
        storage_file_path = "restaurant/"+user.uid+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['sign_message']="Restaurant SignedUp. Please Login"
        return redirect(url_for('login'))
    except Exception as e:
        print(e)
        session['sign_message']="error uploading photo in firebase storage"
        return redirect(url_for('restaurantSignup'))

@app.route('/signup/deliveryAgent', methods=['POST', 'GET'])
def deliveryAgentsignup():
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    local_file_obj = request.files['local_file_path']
    session['sign_message']="Fail"
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('deliveryAgentSignup'))
    try:
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email,
            "gender" : gender,
            "area" : area,
        }
        db.collection("deliveryAgent").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "deliveryAgent"})
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('deliveryAgentSignup'))
    try:
        storage_file_path = "deliveryProfilePics/"+user.uid+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['sign_message']="Delivery Agent SignedUp. Please Login"
        return redirect(url_for('login'))
    except:
        session['sign_message']="error uploading photo in firebase storage"
        return redirect(url_for('deliveryAgentSignup'))



@app.route('/signup/customer', methods=['POST','GET'])
def signup():

    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    local_file_obj = request.files['local_file_path']

    # create user
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('customerSignup'))
    
    # add data in fire-store
    try:
        json_data = {
            "name" : name,
            "dob" : dob,
            "mobile" : mobile,
            "email" : email,
            "gender" : gender,
            "area" : area,
        }
        db.collection("customer").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "customer"})
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('customerSignup'))

    # upload profile picture
    try:
        storage_file_path = "customerProfilePics/"+user.uid+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['sign_message']='Signup was Succesful. Please Login'
        return redirect(url_for('login'))
    except:
        session['sign_message']="error uploading photo in firebase storage"
        return redirect(url_for('customerSignup'))

@app.route("/temp")
def temp():
    # blob = bucket.blob("customerProfilePics/"+"YQ2pF5uHW7ZCvfpIzUD1sTcZL5n2"+".jpg")
    blob = bucket.blob("restaurantProfilePics/"+"oDtSvO2uB8UE6889JHPRFTLvHJY2"+".jpg")

    imagePublicURL = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
    return {"imageLink":imagePublicURL},200

@app.route("/temp/delete")
# @check_token
def delete_user():
    to_delete="2feA7KRsIHgN3inJdxzcpxhxaGq1"

    try:
        auth.delete_user(to_delete)
    except:
        print("user not found")
    
    try:
        user_type = db.collection('type').document(to_delete).get().to_dict()["type"]
        db.collection(user_type).document(to_delete).delete()
    except :
        print("user not found in collection : type ")
        
    db.collection("type").document(to_delete).delete()

    return {"user_id":to_delete},200

@app.route('/api/token', methods=['POST','GET'])
def token():
    email = request.form['email']
    password = request.form['password']
    try:
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
        # user2 = pyrebase_pb.auth().get_account_info(user['idToken'])
        user_type = db.collection('type').document(user["localId"]).get().to_dict()["type"]
        json_data = db.collection(user_type).document(user["localId"]).get().to_dict()
        session['session_user']= json_data
        session['session_user']['user_type']=user_type
        session['jwt_token']=user['idToken']
        session['refresh_token']=user['refreshToken']
        session['user_id']=user['localId']
        print(session['session_user']['user_type'])
        if user_type=="customer" : 
            return redirect(url_for('customerDashboard'))
        elif user_type == "restaurant" : 
            return redirect(url_for('restaurantDashboard'))
        elif user_type == "deliveryAgent" :
            return redirect(url_for('deliveryAgentDashboard'))
        elif user_type == "admin" :
            return redirect(url_for('adminDashboard'))
    except:
        session['sign_message']="Please enter the correct credentials"
        return redirect(url_for('login'))

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
    session['sign_message']="False"
    return render_template('login.html', message=message)

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup')
def customerSignup():
    message=session['sign_message']
    session['sign_message']="False"
    return render_template('customerSignup.html', message=message)

@app.route('/restaurantSignup')
def restaurantSignup():
    message=session['sign_message']
    session['sign_message']="False"
    return render_template('restaurantSignup.html', message=message)

@app.route('/deliveryAgentSignup')
def deliveryAgentSignup():
    message=session['sign_message']
    session['sign_message']="False"
    return render_template('deliveryAgentSignup.html', message=message)

@app.route('/customerDashboard')
@check_token
def customerDashboard():
    user=session['session_user']
    if user['user_type'] == 'customer':
        return render_template('customerDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/restaurantDashboard')
@check_token
def restaurantDashboard():
    user=session['session_user']
    if user['user_type'] == 'restaurant':
        return render_template('restaurantDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/deliveryAgentDashboard')
@check_token
def deliveryAgentDashboard():
    user=session['session_user']
    if user['user_type'] == 'deliveryAgent':
        return render_template('deliveryAgentDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/adminDashboard')
@check_token
def adminDashboard():
    print(type(session))
    user=session['session_user']
    if user['user_type'] == 'admin':
        return render_template('adminDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/personalData')
@check_token
def personalData():
    user=session['session_user']
    return render_template('personalData.html', user=user)

@app.route('/logout')
@check_token
def logout():
    session.clear()
    session['sign_message']="Successfully Logged Out"
    return redirect(url_for('login'))

@app.route('/createMenu')
@check_token
def createMenu():
    user = session['session_user']
    print(user)
    if user['user_type'] == 'restaurant':
        return render_template('createMenu.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/addFoodItem')
@check_token
def addFoodItem():
    user = session['session_user']
    if user['user_type'] == 'restaurant':
        return render_template('addFoodItem.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/finishMenu')
@check_token
def finishMenu():
    user = session['session_user']
    if user['user_type']=='restaurant':
        return render_template('finishMenu.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/addFoodItem/adder', methods=['POST','GET'])
@check_token
def foodItemAdder():
    name = request.form['name']
    price = request.form['price']
    local_file_obj = request.files['local_file_path']
    
    try:
        foodItem = {
            "name" : name,
            "pricePerItem" : price,
            "isRecommended": False,
            "restaurantId" : session["user_id"],
            "picSrc": ""
        }
        doc_reference = db.collection("restaurant").document(session["user_id"]).collection("foodItem").document()
        doc_reference.set(foodItem)
        # return {"ok":"True"},200
        
    except:
        session['food_item_addition_msg'] = "Error adding food item text data in database"
        return redirect(url_for('addFoodItem'))
    try:
        storage_file_path = "restaurant/"+session["user_id"]+"_"+doc_reference.id+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        doc_reference = db.collection("restaurant").document(session["user_id"]).collection("foodItem").document(doc_reference.id).update({"picSrc":storage_file_path})
        session['food_item_addition_msg']="Food item text and photo successfully added in database"
        return redirect(url_for('createMenu'))
    except Exception as e:
        print(e)
        session['food_item_addition_msg']="error uploading photo in firebase storage"
        return redirect(url_for('addFoodItem'))

    
@app.route('/allRestaurant')
@check_token
def allRestaurant():
    user=session['session_user']
    if not user['user_type'] == 'admin' and not user['user_type'] == 'customer':
        return redirect(url_for('logout'))
    if session.get('restaurantList') == None:
        session['restaurantList']=[]
        docs=db.collection('restaurant').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            session['restaurantList'].append(temp_dict)
    return render_template('allRestaurant.html', user=user)

@app.route('/allCustomers')
@check_token
def allCustomers():
    user=session['session_user']
    if not user['user_type']=="admin":
        return redirect(url_for('logout'))
    if not "customerList" in session:
        session['customerList']=[]
        docs=db.collection('customer').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            session['customerList'].append(temp_dict)
    return render_template('allCustomers.html', user=user)

@app.route('/allDeliveryAgents')
@check_token
def allDeliveryAgents():
    user=session['session_user']
    if not user['user_type']=="admin" and not user['user_type']=='restaurant':
        return redirect(url_for('logout'))
    if session.get('deliveryAgentList')==None or not session['deliveryAgentList']:
        session['deliveryAgentList']=[]
        docs=db.collection('deliveryAgent').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            session['deliveryAgentList'].append(temp_dict)
    return render_template('allDeliveryAgents.html', user=user)

def deleteUserFromDatabase(to_delete):

    user_type=""

    try:
        auth.delete_user(to_delete)
    except:
        print("Error deleting user from authentication")

    try:
        user_type = db.collection('type').document(to_delete).get().to_dict()["type"]
        if(user_type=="restaurant"):
            # If you have larger collections, you may want to delete the documents in smaller batches to avoid out-of-memory errors.
            delete_collection(db.collection("restaurant").document(to_delete).collection("foodItem"),1000)
        db.collection(user_type).document(to_delete).delete()
        db.collection("type").document(to_delete).delete()
    except :
        print("error deleting user from firestore")

    try:
        # deleting profile pictures
        bucket.delete_blob(user_type+"/"+to_delete+".jpg")
        
        # deleting food item images
        if user_type=="restaurant":
            blob_objects=bucket.list_blobs(prefix="restaurant/"+to_delete+"_")
            blob_object_names=[]
            for blob in blob_objects:
                blob_object_names.append(blob.name)
            bucket.delete_blobs(blob_object_names)
    
    except Exception as e:
        print(e)
    

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

@app.route('/delete/<user_type>/<delete_id>')
@check_token
def deleteUser(user_type, delete_id):
    # print(request.args.get(user_type))
    if not session['session_user']['user_type'] == "admin":
        return redirect(url_for('logout'))
    to_delete = int(delete_id)
    to_delete=to_delete-1
    if user_type == "restaurant":
        user_deleted=session['restaurantList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['user_id'])
        return redirect(url_for('allRestaurant'))
    elif user_type == "customer":
        user_deleted = session['customerList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['user_id'])
        return redirect(url_for('allCustomers'))
    elif user_type == 'deliveryAgent':
        user_deleted = session['deliveryAgentList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['user_id'])
        return redirect(url_for('allDeliveryAgents'))

if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)