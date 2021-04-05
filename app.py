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
#addding a comment
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True
app.config['SESSION_TYPE']="filesystem"
app.secret_key ='a very very very long string'

# for bitly short link
bitly_headers = {
    'Authorization': 'Bearer bb812cf74a73b3507a9dd88c44e4ad9cca9dbb0b',
    'Content-Type': 'application/json',
}

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
                session['signMess']="No Token Provided. Try Logging In."
                return redirect(url_for('login'))
        except:
            session['signMess']="No Token Provided. Try Logging In."
            return redirect(url_for('login'))
        try:
            session['jwt_token'] = pyrebase_pb.auth().refresh(session['refresh_token'])['idToken']
            user = auth.verify_id_token(session['jwt_token'])
            request.user = user
            userType=session['sessionUser']['userType']
            session['sessionUser'] = db.collection(session['sessionUser']['userType']).document(session['userId']).get().to_dict()
            session['sessionUser']['userType']=userType
            session.modified=True
        except:
            session['signMess']="Invalid Token Provided. Trying Logging again."
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
    session['signMess']="Fail"
    storage_file_path=""
    if area=='Other':
        session['signMess'] = "We currently don't have service in your area."
        return redirect(url_for('restaurantSignup'))
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "restaurant/"+user.uid+".jpg"
    except:
        session['signMess']="error creating user in firebase"
        return redirect(url_for('restaurantSignup'))
    try:

        rating_reference = db.collection('rating').document()
        rating_json_data= {
            "noOfInputs":0,
            "sum":0.0,
            "rating":0.0,
            "ratingId":rating_reference.id
        }
        rating_reference.set(rating_json_data)

        json_data = {
            "name" : name,
            "areaId" : area,
            "ratingId": rating_reference.id,
            "restaurantId" : user.uid,
            "picSrc" : storage_file_path,
            "pendingOrderId": [],
            "email" : email,
            "isRecommended" : False
        }

        db.collection("restaurant").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "restaurant"})
        
    except:
        session['signMess']="error adding user text data in firestore"
        return redirect(url_for('restaurantSignup'))
    try:
        
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['signMess']="Restaurant SignedUp. Please Login"
        db.collection('area').document(area).update({"restaurantId" : firestore.ArrayUnion([user.uid])})
        return redirect(url_for('login'))
    except Exception as e:
        print(e)
        session['signMess']="error uploading photo in firebase storage"
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
    print(local_file_obj)
    session['signMess']="Fail"
    storage_file_path = ""
    if area=='Other':
        session['signMess'] = "We currently don't deliver in your area."
        return redirect(url_for('deliveryAgentSignup'))

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "deliveryAgent/"+user.uid+".jpg"
    except:
        session['signMess']="error creating user in firebase"
        return redirect(url_for('deliveryAgentSignup'))
    
    try:

        rating_reference = db.collection('rating').document()
        rating_json_data= {
            "noOfInputs":0,
            "sum":0.0,
            "rating":0.0,
            "ratingId":rating_reference.id
        }
        rating_reference.set(rating_json_data)

        json_data = {
            "name" : name,
            "dateOfBirth" : dob,
            "mobileNumber" : mobile,
            "picSrc" : storage_file_path,
            "email" : email,
            "gender" : gender,
            "areaId" : area,
            "deliveryAgentId" : user.uid,
            "ratingId" : rating_reference.id,
            "isAvailable" : True,
            "currentOrderId":""
        }
        db.collection("deliveryAgent").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "deliveryAgent"})
    except:
        session['signMess']="error adding user text data in firestore"
        return redirect(url_for('deliveryAgentSignup'))
    try:
        
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['signMess']="Delivery Agent SignedUp. Please Login"
        return redirect(url_for('login'))
    except:
        session['signMess']="error uploading photo in firebase storage"
        return redirect(url_for('deliveryAgentSignup'))



@app.route('/signup/customer', methods=['POST','GET'])
def customersignup():

    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    area = request.form['area']
    mobile = request.form['mobile']
    dob = request.form['dob']
    name = request.form['name']
    address = request.form['address']
    local_file_obj = request.files['local_file_path']
    storage_file_path = ""
    if area=='Other':
        session['signMess'] = "We currently don't deliver in your area."
        return redirect(url_for('customerSignup'))
    # create user
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "customer/"+user.uid+".jpg"
    except:
        session['signMess']="error creating user in firebase"
        return redirect(url_for('customerSignup'))
    
    # add data in fire-store
    try:

        rating_reference = db.collection('rating').document()
        rating_json_data= {
            "noOfInputs":0,
            "sum":0.0,
            "rating":0.0,
            "ratingId":rating_reference.id
        }
        rating_reference.set(rating_json_data)

        json_data = {
            "name" : name,
            "dateOfBirth" : dob,
            "mobileNumber" : mobile,
            "email" : email,
            "gender" : gender,
            "areaId" : area,
            "customerId":user.uid,
            "ratingId":rating_reference.id,
            "picSrc": storage_file_path,
            "pendingOrderId": [],
            "address" : address
        }
        db.collection("customer").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "customer"})
    except:
        session['signMess']="error adding user text data in firestore"
        return redirect(url_for('customerSignup'))

    # upload profile picture
    try:
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['signMess']='Signup was Succesful. Please Login'
        return redirect(url_for('login'))
    except:
        session['signMess']="error uploading photo in firebase storage"
        return redirect(url_for('customerSignup'))

@check_token
def getImageURL(path):
    blob = bucket.blob(path)

    imagePublicURL = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')

    bitly_data = '{ "long_url": '+'"'+imagePublicURL+'", "domain": "bit.ly", "group_guid": "Bl1p4sQJxCm" }'

    try:
        response = requests.post('https://api-ssl.bitly.com/v4/shorten', headers=bitly_headers, data=bitly_data)
        response=response.json()
    except Exception as e:
        # print(e)
        pass

    shortURL=response['link']

    return shortURL



@app.route('/api/token', methods=['POST','GET'])
def token():
    email = request.form['email']
    password = request.form['password']
    try:
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
        try:
            user_type = db.collection('type').document(user["localId"]).get().to_dict()["type"]
        except Exception as e:
            print(e)
        json_data = db.collection(user_type).document(user["localId"]).get().to_dict()
        session['sessionUser']= json_data
        session['sessionUser']['userType']=user_type
        session['jwt_token']=user['idToken']
        session['refresh_token']=user['refreshToken']
        session['userId']=user['localId']
        if user_type=="customer" : 
            return redirect(url_for('customerDashboard'))
        elif user_type == "restaurant" : 
            return redirect(url_for('restaurantDashboard'))
        elif user_type == "deliveryAgent" :
            return redirect(url_for('deliveryAgentDashboard'))
        elif user_type == "admin" :
            return redirect(url_for('adminDashboard'))
    except:
        session['signMess']="Please enter the correct credentials"
        return redirect(url_for('login'))

@app.route('/')
def index():
    session['signMess']="False"
    message=session['signMess']
    return render_template('index.html', message=message)

@app.route('/Signup')
def signUp():
    return render_template('signup.html')



@app.route('/login')
def login():
    message=session['signMess']
    session['signMess']="False"
    return render_template('login.html', message=message)

@app.route('/adminLogin')
def adminLogin():
    return render_template('adminLogin.html')

@app.route('/customerSignup')
def customerSignup():
    message=session['signMess']
    session['signMess']="False"
    doc_refrence = db.collection('area').stream()
    area_dict=[]
    for doc in doc_refrence:
        temp_dict=doc.to_dict()
        area_dict.append(temp_dict)

    return render_template('customerSignup.html', message=message,area_dict=area_dict)

@app.route('/restaurantSignup')
def restaurantSignup():
    message=session['signMess']
    session['signMess']="False"
    doc_reference = db.collection('area').stream()
    area_dict=[]
    for doc in doc_reference:
        temp_dict=doc.to_dict()
        area_dict.append(temp_dict)
    return render_template('restaurantSignup.html', message=message,area_dict=area_dict)

@app.route('/deliveryAgentSignup')
def deliveryAgentSignup():
    message=session['signMess']
    session['signMess']="False"
    doc_reference = db.collection('area').stream()
    area_dict=[]
    for doc in doc_reference:
        temp_dict=doc.to_dict()
        area_dict.append(temp_dict)
    return render_template('deliveryAgentSignup.html', message=message,area_dict=area_dict)

@app.route('/customerDashboard')
@check_token
def customerDashboard():
    user=session['sessionUser']
    if user['userType'] == 'customer':
        return render_template('customerDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/restaurantDashboard')
@check_token
def restaurantDashboard():
    user=session['sessionUser']
    if user['userType'] == 'restaurant':
        return render_template('restaurantDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/deliveryAgentDashboard')
@check_token
def deliveryAgentDashboard():
    user=session['sessionUser']
    if user['userType'] == 'deliveryAgent':
        return render_template('deliveryAgentDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/adminDashboard')
@check_token
def adminDashboard():
    print(type(session))
    user=session['sessionUser']
    if user['userType'] == 'admin':
        return render_template('adminDashboard.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/personalData')
@check_token
def personalData():
    user=session['sessionUser']
    user['areaName']=db.collection('area').document(user['areaId']).get().to_dict()['name']
    user['ratingValue']=db.collection('rating').document(user['ratingId']).get().to_dict()['rating']
    path = user['picSrc']
    user['profilePicture'] = getImageURL(path)
    return render_template('personalData.html', user=user)

@app.route('/logout')
@check_token
def logout():
    session.clear()
    session['signMess']="Successfully Logged Out"
    return redirect(url_for('login'))

@app.route('/createMenu')
@check_token
def createMenu():
    user = session['sessionUser']
    print(user)
    if not user['userType'] == 'restaurant':
        return redirect(url_for('logout'))
    currResMenuId=session['userId']
    foodItemList=[]
    docs=db.collection('restaurant').document(currResMenuId).collection('foodItem').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        # print(temp_dict)
        # temp_dict['foodItemId'] = doc.id
        # temp_dict['food_item_id']= doc.id
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        foodItemList.append(temp_dict)
    try:
        message=session['foodMessage']
        session['foodMessage']="False"
    except: 
        session['foodMessage']="False"
        message="False"
    return render_template('createMenu.html', user=user, menuList=foodItemList, message=message)

@app.route('/addFoodItem')
@check_token
def addFoodItem():
    user = session['sessionUser']
    if user['userType'] == 'restaurant':
        message=session['foodMessage']
        session['foodMessage']="False"
        return render_template('addFoodItem.html', user=user, message=message)
    else:
        return redirect(url_for('logout'))

@app.route('/finishMenu')
@check_token
def finishMenu():
    user = session['sessionUser']
    if user['userType']=='restaurant':
        return render_template('finishMenu.html', user=user)
    else:
        return redirect(url_for('logout'))

@app.route('/addFoodItem/adder', methods=['POST','GET'])
@check_token
def foodItemAdder():
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    name = request.form['name']
    price = request.form['price']
    local_file_obj = request.files['local_file_path']
    
    try:
        foodItem = {
            "name" : name,
            "pricePerItem" : price,
            "isRecommended": False,
            "restaurantId" : session["userId"],
            "picSrc": ""
        }
        doc_reference = db.collection("restaurant").document(session["userId"]).collection("foodItem").document()
        doc_reference.set(foodItem)
        db.collection("restaurant").document(session["userId"]).collection("foodItem").document(doc_reference.id).update({"foodItemId":doc_reference.id})
        
    except:
        session['foodMessage'] = "Error adding food item text data in database"
        return redirect(url_for('addFoodItem'))
    try:
        storage_file_path = "restaurant/"+session["userId"]+"_"+doc_reference.id+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        doc_reference = db.collection("restaurant").document(session["userId"]).collection("foodItem").document(doc_reference.id).update({"picSrc":storage_file_path})
        session['foodMessage']="Food item text and photo successfully added in database."
        return redirect(url_for('createMenu'))
    except Exception as e:
        print(e)
        session['foodMessage']="error uploading photo in firebase storage"
        return redirect(url_for('addFoodItem'))

    
@app.route('/allRestaurant')
@check_token
def allRestaurant():
    user=session['sessionUser']
    if not user['userType'] == 'admin' and not user['userType'] == 'customer':
        return redirect(url_for('logout'))
    restaurantList=[]
    
    docs=db.collection('restaurant').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['userId']= doc.id
        temp_dict['areaName']=db.collection('area').document(temp_dict['areaId']).get().to_dict()['name']
        temp_dict['ratingValue']= db.collection('rating').document(temp_dict['ratingId']).get().to_dict()['rating']
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        restaurantList.append(temp_dict)
    session['restaurantList']=restaurantList
    session.modified=True
    return render_template('allRestaurant.html', user=user, restaurantList=restaurantList)

@app.route('/allCustomers')
@check_token
def allCustomers():
    user=session['sessionUser']
    if not user['userType']=="admin":
        return redirect(url_for('logout'))
    session['customerList']=[]
    session.modified = True
    docs=db.collection('customer').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['userId']= doc.id
        temp_dict['areaName']=db.collection('area').document(temp_dict['areaId']).get().to_dict()['name']
        temp_dict['ratingValue']= db.collection('rating').document(temp_dict['ratingId']).get().to_dict()['rating']
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        session['customerList'].append(temp_dict)
    return render_template('allCustomers.html', user=user)

@app.route('/allDeliveryAgents')
@check_token
def allDeliveryAgents():
    user=session['sessionUser']
    if not user['userType']=="admin" and not user['userType']=='restaurant':
        return redirect(url_for('logout'))
    session['deliveryAgentList']=[]
    session.modified = True
    docs=db.collection('deliveryAgent').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['userId']= doc.id
        temp_dict['areaName']=db.collection('area').document(temp_dict['areaId']).get().to_dict()['name']
        temp_dict['ratingValue']= db.collection('rating').document(temp_dict['ratingId']).get().to_dict()['rating']
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        session['deliveryAgentList'].append(temp_dict)
    return render_template('allDeliveryAgents.html', user=user)

@app.route('/allFoodItem11/<restaurantUserId>')
@check_token
def allFoodItem11(restaurantUserId):
    if not session['sessionUser']['userType'] == 'customer' and not session['sessionUser']['userType'] == 'admin':
        return redirect(url_for('logout'))
    session['currResMenuId']=restaurantUserId
    return redirect(url_for('allFoodItem'))


@app.route('/allFoodItem')
@check_token
def allFoodItem():

    user=session['sessionUser']
    if not user['userType']=='customer' and not user['userType']=='admin':
        return redirect(url_for('logout'))

    foodItemList=[]
    docs=db.collection('restaurant').document(session['currResMenuId']).collection('foodItem').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        foodItemList.append(temp_dict)
    session['currentMenu']=foodItemList
    session.modified=True
    return render_template('allFoodItem.html', user=user,foodItemList=foodItemList)

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
    if not session['sessionUser']['userType'] == "admin":
        return redirect(url_for('logout'))
    to_delete = int(delete_id)
    to_delete=to_delete-1
    if user_type == "restaurant":
        user_deleted=session['restaurantList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['userId'])
        return redirect(url_for('allRestaurant'))
    elif user_type == "customer":
        user_deleted = session['customerList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['userId'])
        return redirect(url_for('allCustomers'))
    elif user_type == 'deliveryAgent':
        user_deleted = session['deliveryAgentList'].pop(to_delete)
        session.modified = True
        deleteUserFromDatabase(user_deleted['userId'])
        return redirect(url_for('allDeliveryAgents'))
    
    
@app.route('/order', methods=['POST','GET'])
@check_token
def order():
    foodItemList = session['currentMenu']
    
    cost = 0
    orderList = []
    for i in range(len(foodItemList)):
        if not int(request.form[str(i+1)]) == 0:
            # print(foodItemList[i]['name'])
            foodItemList[i]['frequency'] = int(request.form[str(i+1)])
            foodItemList[i]['pricePerItem'] = int(foodItemList[i]['pricePerItem'])
            orderList.append(foodItemList[i])
            cost += int(foodItemList[i]['pricePerItem']) * int(foodItemList[i]['frequency'])
            
    session['currentOrderCreating'] = {
            'orderList': orderList, 
            'isPending': True,
            'customerId': session['userId'],
            'restaurantId': foodItemList[0]['restaurantId'],
            'offerId': None,
            'orderValue': cost, 
            'discountValue':0,
            'paidValue': 0,
            'deliveryCharge': 50,
            'orderDateTime': "",
            'deliveryAgentId' : "",
            'updateLevel' :0,
            'updateMessage' : "Accept/Reject",
            'orderUpdates' : [],
            'orderId': ''
    }
    return redirect(url_for('orderDetails'))

@app.route('/orderDetails')
@check_token
def orderDetails():
    currentOrder=session['currentOrderCreating']
    customerName = db.collection('customer').document(currentOrder['customerId']).get().to_dict()['name']
    restaurantName = db.collection('restaurant').document(currentOrder['restaurantId']).get().to_dict()['name']
    orderList=currentOrder['orderList']
    discount=currentOrder['discountValue']
    if currentOrder['offerId'] == None:
        offerUsed=None
        discount=0
    else: 
        offerUsed=db.collection('customer').document(currentOrder['customerId']).collection('promotionalOfferId').document(currentOrder['offerId']).get().to_dict()
        discount=min(int(int(currentOrder['orderValue'])*int(offerUsed['discount'])/100), int(offerUsed['upperLimit']))

    final=max(currentOrder['orderValue']+ currentOrder['deliveryCharge']- discount,0)
    currentOrder['paidValue']=final
    currentOrder['discountValue']=discount

    return render_template('orderDetails.html', orderList=orderList, customerName=customerName, restaurantName=restaurantName, offerUsed=offerUsed, cost=currentOrder['orderValue'], deliveryCharge=currentOrder['deliveryCharge'], discount=discount, final=final)

@app.route('/placeOrder')
@check_token
def placeOrder():
    currentOrder=session['currentOrderCreating']
    doc_reference = db.collection('order').document()
    doc_reference.set(currentOrder)
    db.collection('order').document(doc_reference.id).update({ 'orderId' : doc_reference.id})
    orderId=doc_reference.id
    session['currentOrderCreating']["orderId"] = orderId
    session.modified = True
    # add restaurant array
    restaurantId=currentOrder['restaurantId']
    restaurantDocReference = db.collection('restaurant').document(restaurantId)
    restaurantDocReference.update({'pendingOrderId': firestore.ArrayUnion([orderId])})
    # customer array main add karna hai
    customerId=currentOrder['customerId']
    customerDocReference = db.collection('customer').document(customerId)
    customerDocReference.update({'pendingOrderId': firestore.ArrayUnion([orderId])})
    
    # offerId !=None
    if not currentOrder['offerId'] == None:
        db.collection('order').document(orderId).update({'offerId': db.collection('customer').document(customerId).collection('promotionalOfferId').document(currentOrder['offerId']).get().to_dict()})
        db.collection('customer').document(customerId).collection('promotionalOfferId').document(currentOrder['offerId']).delete()
    return redirect(url_for('recentOrderCustomer'))

@app.route('/recentOrderCustomer')
@check_token
def recentOrderCustomer():
    user = session['sessionUser']
    customerId=user['customerId']
    listOrderId = db.collection('customer').document(customerId).get().to_dict()['pendingOrderId']
    docs = db.collection('order').stream()
    recentOrderList=[]
    for doc in docs:
        if doc.id in listOrderId:
            temp=doc.to_dict()
            temp['restaurantName']=db.collection('restaurant').document(temp['restaurantId']).get().to_dict()['name']
            recentOrderList.append(temp)
    session['presentOrderCustomer']=recentOrderList
    session.modified = True
    return render_template('recentOrderCustomer.html', recentOrderList=recentOrderList)

@app.route('/recentOrderRestaurant')
@check_token
def recentOrderRestaurant():
    user=session['sessionUser']
    restaurantId = user['restaurantId']
    listOrderId = db.collection('restaurant').document(restaurantId).get().to_dict()['pendingOrderId']
    docs = db.collection('order').stream()
    recentOrderList = []
    
    for doc in docs:
        if doc.id in listOrderId:
            temp = doc.to_dict()
            print(temp['customerId'])
            temp['customerName']=db.collection('customer').document(temp['customerId']).get().to_dict()['name']
            recentOrderList.append(temp)
    session['presentOrderRestaurant'] = recentOrderList
    session.modified = True
        
    return render_template('recentOrderRestaurant.html', recentOrderList=recentOrderList)

@app.route('/orderDetailRestaurant<orderId>')
@check_token
def orderDetailRestaurant(orderId):
    orderId=int(orderId)
    if orderId > len(session['presentOrderRestaurant']):
        return redirect(url_for('recentOrderRestaurant'))
    orderId=orderId-1
    currentOrder=session['presentOrderRestaurant'][orderId]['orderId']
    currentOrder=db.collection('order').document(currentOrder).get().to_dict()
    customerName = db.collection('customer').document(currentOrder['customerId']).get().to_dict()['name']
    restaurantName = db.collection('restaurant').document(currentOrder['restaurantId']).get().to_dict()['name']
    orderList=currentOrder['orderList']
    discount=currentOrder['discountValue']
    session['currentOrderUpdating']=currentOrder
    session.modified = True
    final=max(currentOrder['orderValue']+ currentOrder['deliveryCharge']- discount,0)
    return render_template('orderDetailsRestaurant.html', currentOrder = currentOrder, orderList=orderList, customerName=customerName, restaurantName=restaurantName, cost=currentOrder['orderValue'], deliveryCharge=currentOrder['deliveryCharge'], discount=discount, final=final, updateLevel=currentOrder['updateLevel'])


@app.route('/updateStatus0<val>')
@check_token
def updateStatus0(val):
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    if val == "Reject":
        updateOrderDic = {'heading': "Rejected"}
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'orderUpdates' : firestore.ArrayUnion([updateOrderDic])})
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'isPending': False})
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateMessage': "Rejected"})
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateLevel': 1})
        db.collection('customer').document(session['currentOrderUpdating']['customerId']).update({'pendingOrderId' : firestore.ArrayRemove([session['currentOrderUpdating']['orderId']])})
        db.collection('restaurant').document(session['currentOrderUpdating']['restaurantId']).update({'pendingOrderId' : firestore.ArrayRemove([session['currentOrderUpdating']['orderId']])})
        return redirect('recentOrderRestaurant')
    else :
        return render_template('getEstimatedTime.html')

@app.route('/getEstimatedTime', methods=['POST','GET'])
@check_token
def getEstimatedTime():
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    try:
        estimatedTime = request.form['time']
        updateOrderDic = {
            'heading': "Accepted",
            'time' : str(estimatedTime)+" min"
            
            }
        # print(estimatedTime)
    except Exception as e:
        print(str(e))

    try:
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateMessage': "Accepted. Preparing Food"})
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateLevel': 1})
        db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'orderUpdates' : firestore.ArrayUnion([updateOrderDic])})
    except Exception as e:
        print(str(e))

    return redirect(url_for('recentOrderRestaurant'))
    # return {"ok":"ok"},200

@app.route('/updateStatus1')
@check_token
def updateStatus1():
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    return render_template('foodPrepared.html')

@app.route('/updateStatus3')
@check_token
def updateStatus3():
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    currentOrder = session['currentOrderUpdating']
    db.collection('order').document(currentOrder['orderId']).update({'updateMessage': "Out for Delivery"})
    db.collection('order').document(currentOrder['orderId']).update({'updateLevel': 4})
    return redirect(url_for('recentOrderRestaurant'))
    


@app.route('/addPendingOrderId')
@check_token
def addPendingOrderId():

    if session['sessionUser']['userType']!='restaurant':
        return redirect(url_for('logout'))

    pendingOrderId=session['currentOrderUpdating']['orderId'] #get from front end
    areaId=session['sessionUser']['areaId']

    db.collection('area').document(areaId).update({'availableOrderIdForPickup':firestore.ArrayUnion([pendingOrderId])})
    db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateMessage': "Food is Prepared"})
    db.collection('order').document(session['currentOrderUpdating']['orderId']).update({'updateLevel': 2})
    return redirect(url_for('recentOrderRestaurant'))


@app.route('/moreDetailsOrder<orderId>')
@check_token
def moreDetailsOrder(orderId):
    if session['sessionUser']['userType'] != 'customer':
        return redirect(url_for('logout'))
    orderId=int(orderId)
    if orderId > len(session['presentOrderCustomer']):
        return redirect(url_for('recentOrderCustomer'))
    orderId=orderId-1
    currentOrder=session['presentOrderCustomer'][orderId]['orderId']
    currentOrder=db.collection('order').document(currentOrder).get().to_dict()
    customerName = db.collection('customer').document(currentOrder['customerId']).get().to_dict()['name']
    restaurantName = db.collection('restaurant').document(currentOrder['restaurantId']).get().to_dict()['name']
    session['customerCurrentOrderChanging']=currentOrder
    orderList=currentOrder['orderList']
    discount=currentOrder['discountValue']
    print(currentOrder['offerId'])
    if currentOrder['offerId'] == None:
        offerUsed=None
    else: 
        offerUsed=currentOrder['offerId']
        discount=min(int(int(currentOrder['orderValue'])*int(offerUsed['discount'])/100), int(offerUsed['upperLimit']))
    currentOrder['discountValue']=discount
    final=max(currentOrder['orderValue']+ currentOrder['deliveryCharge']- discount,0)
    deliveryAgentName=""
    if currentOrder['deliveryAgentId'] != "":
        deliveryAgentName=db.collection('deliveryAgent').document(currentOrder['deliveryAgentId']).get().to_dict()['name']
    return render_template('moreDetailsOrder.html',  orderList=orderList, customerName=customerName, restaurantName=restaurantName, offerUsed=offerUsed, cost=currentOrder['orderValue'], deliveryCharge=currentOrder['deliveryCharge'], discount=discount, final=final, updateLevel=currentOrder['updateLevel'], orderUpdate = currentOrder['orderUpdates'],restaurantId=currentOrder['restaurantId'],customerId= currentOrder['customerId'], deliveryAgentName=deliveryAgentName)

@app.route('/useOffer<toUse>')
@check_token
def useOffer(toUse):
    if session['sessionUser']['userType'] != 'customer':
        return redirect(url_for('logout'))
    user=session['userId']
    toUse=int(toUse)
    toUse=toUse-1
    session['currentOrderCreating']['offerId']=session['offerList'][toUse]['offerId']
    session.modified = True
    return redirect(url_for('orderDetails'))

@app.route('/removeOfferFromOrder')
@check_token
def removeOfferFromOrder():
    if session['sessionUser']['userType'] != 'customer':
        return redirect(url_for('logout'))
    session['currentOrderCreating']['offerId']=None
    session.modified = True
    return redirect(url_for('orderDetails'))

@app.route('/redirectDashboard')
@check_token
def redirectDashboard():
    if session['sessionUser']['userType']=='customer':
        return redirect(url_for('customerDashboard'))
    elif session['sessionUser']['userType']=='restaurant':
        return redirect(url_for('restaurantDashboard'))
    elif session['sessionUser']['userType']=='deliveryAgent':
        return redirect(url_for('deliveryAgentDashboard'))
    elif session['sessionUser']['userType']=='admin':
        return redirect(url_for('adminDashboard'))
    
@app.route('/deleteFoodItem<foodItemId>')
@check_token
def deleteFoodItem(foodItemId):
    if session['sessionUser']['userType'] != 'restaurant':
        return redirect(url_for('logout'))
    restaurantId=session['userId']

    #command_to delete the id
    try:
        db.collection("restaurant").document(restaurantId).collection('foodItem').document(foodItemId).delete()
        session['foodMessage']="food item deletion from databse is successful"
    except Exception as e:
        # print(e)
        session['foodMessage']="Error deleting food item from databse"

    return redirect(url_for('createMenu'))

@app.route('/changeRecommendRestaurant<id_to_change>')
@check_token
def changeRecommendRestaurant(id_to_change):
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    id=int(id_to_change)
    id=id-1

    restaurantId=session['restaurantList'][id]['restaurantId']

    if session['restaurantList'][id]['isRecommended'] == False:
        session['restaurantList'][id]['isRecommended'] = True
        session.modified = True
        
    else :
        session['restaurantList'][id]['isRecommended'] = False
        session.modified = True

    #change in database
    isRecommended=""
    try:
        isRecommended = db.collection("restaurant").document(restaurantId).get().to_dict()['isRecommended']
    except Exception as e:
        # print(str(e))
        # error retriving isRecommended from database
        pass
    
    try:
        db.collection("restaurant").document(restaurantId).update({'isRecommended':not isRecommended})
    except Exception as e:
        # print(str(e))
        # error changing isRecommended from database
        pass

    return redirect(url_for('allRestaurant'))

@app.route('/changeRecommendFoodItem<id_to_change>')
@check_token
def changeRecommendFoodItem(id_to_change):
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    id=int(id_to_change)
    id=id-1
    if session['currentMenu'][id]['isRecommended'] == False:
        session['currentMenu'][id]['isRecommended'] = True
        session.modified = True
    else :
        session['currentMenu'][id]['isRecommended'] = False
        session.modified = True

    foodItemId=session['currentMenu'][id]['foodItemId']
    restaurantId=session['currentMenu'][id]['restaurantId']

    isRecommended=""
    try:
        isRecommended = db.collection("restaurant").document(restaurantId).collection("foodItem").document(foodItemId).get().to_dict()['isRecommended']
    except Exception as e:
        # print(str(e))
        # error retriving isRecommended from database
        pass
    
    try:
        db.collection("restaurant").document(restaurantId).collection("foodItem").document(foodItemId).update({'isRecommended':not isRecommended})
    except Exception as e:
        # print(str(e))
        # error changing isRecommended from database
        pass

    return redirect(url_for('allFoodItem11', restaurantUserId = restaurantId ))

@app.route('/recommendedRestaurant')
@check_token
def recommendedRestaurant():
    user=session['sessionUser']
    if not user['userType'] == 'customer':
        return redirect(url_for('logout'))
    restaurantList=[]
    tempRestaurantList=[]
    docs=db.collection('restaurant').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['userId']= doc.id
        temp_dict['pic'] = getImageURL(temp_dict['picSrc'])
        tempRestaurantList.append(temp_dict)
    for restaurant in tempRestaurantList:
        if restaurant['isRecommended']:
            restaurantList.append(restaurant)
    session['restaurantList']=restaurantList
    session.modified = True
    
    return render_template('recommendedRestaurant.html', restaurantList=restaurantList, user=user)
        

@app.route('/createOffer')
@check_token
def createOffer():
    user = session['sessionUser']
    if not user['userType'] == 'admin':
        return redirect(url_for('logout'))
    currentAdminId=session['userId']
    offerList=[]
    # Add statement for getting a docs for the offers
    docs=db.collection('offer').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['offerId']= doc.id
        offerList.append(temp_dict)
    try:
        message=session['offerAdditionMessage']
        session['offerAdditionMessage']="False"
    except: 
        session['offerAdditionMessage']="False"
        message="False"
    return render_template('createOffer.html', user=user, offerList=offerList, message=message)

@app.route('/addOffer')
@check_token
def addOffer():
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    user = session['sessionUser']
    if user['userType'] == 'admin':
        message=session['offerAdditionMessage']
        session['offerAdditionMessage']="False"
        return render_template('addOffer.html', user=user, message=message)
    else:
        return redirect(url_for('logout'))

@app.route('/addOffer/adder', methods=['POST','GET'])
@check_token
def offerAdder():
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    name = request.form['name']
    discount = request.form['discount']
    price = request.form['price']
    
    try:
        json_data = {
            "name" : name,
            "discount" : discount,
            "upperLimit": price,
            "offerId":""
        }
        
        doc_reference = db.collection("offer").document()
        doc_reference.set(json_data)
        db.collection("offer").document(doc_reference.id).update({"offerId":doc_reference.id})

        session['offerAdditionMessage']="Offer added successfully."
        return redirect(url_for('createOffer'))
        
    except Exception as e:
        print(str(e))
        session['offerAdditionMessage'] = "Error adding offer in database"
        return redirect(url_for('addOffer'))

@app.route('/allOffer<customer_id>')
@check_token
def allOffer(customer_id):
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    customer_id=int(customer_id)
    customer_id=customer_id-1
    session['customerGettingOffer']=session['customerList'][customer_id]['customerId']
    offerList=[]
    docs = db.collection('offer').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['offerId']= doc.id
        offerList.append(temp_dict)
    session['offerList'] = offerList
    session.modified = True
    print(offerList)
    return render_template('allOfferAdmin.html', offerList=offerList)


@app.route('/giveOffer<toGive>')
@check_token
def giveOffer(toGive):
    if session['sessionUser']['userType'] != 'admin':
        return redirect(url_for('logout'))
    
    toGive=int(toGive)
    toGive=toGive-1

    customerGettingOffer=session['customerGettingOffer']
    offerId=session['offerList'][toGive]['offerId']
    
    try:
        offer_json_data = db.collection('offer').document(offerId).get().to_dict()
        doc_reference = db.collection("customer").document(customerGettingOffer).collection("promotionalOfferId").document()
        offer_json_data['offerId']=doc_reference.id
        doc_reference.set(offer_json_data)
        # doc_reference1 = db.collection("customer").document(customerGettingOffer).collection("foodItem").document(doc_reference.id).update({"foodItemId":doc_reference.id})
        # return {"ok":"True"},200
        
    except:
        # Error creating offer for customer in database
        # return redirect(url_for('allOffer'))
        pass
    
    return redirect(url_for('allCustomers'))

@app.route('/offerListCustomer')
@check_token
def offerListCustomer():
    if session['sessionUser']['userType'] != 'customer':
        return redirect(url_for('logout'))
    user=session['userId']
    offerList=[]
    docs = db.collection('customer').document(user).collection('promotionalOfferId').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['offerId']= doc.id
        
        offerList.append(temp_dict)
    session['offerList']=offerList
    session.modified = True
    # print(offerList)
    return render_template('allOfferCustomer.html', offerList=offerList)

@app.route('/pastOrder')
@check_token
def pastOrder():
    if not session['sessionUser']['userType'] == 'restaurant' and not session['sessionUser']['userType'] == 'customer':
        return redirect(url_for('logout'))
    userId=session['userId']
    userType=session['sessionUser']['userType']

    pastOrderList=[]

    docs = db.collection('order').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        if not temp_dict['isPending'] :
            if userType=='customer' and userId==temp_dict['customerId']:
                temp_dict['restaurantName']=db.collection('restaurant').document(temp_dict['restaurantId']).get().to_dict()['name']
                pastOrderList.append(temp_dict)
            elif userType=='restaurant' and userId==temp_dict['restaurantId']:
                temp_dict['customerName']=db.collection('customer').document(temp_dict['customerId']).get().to_dict()['name']
                pastOrderList.append(temp_dict)

    if(userType=="customer"):
        session['presentOrderCustomer']= pastOrderList
        session.modified = True
        return render_template('pastOrderCustomer.html',pastOrderList=pastOrderList)
    if(userType=="restaurant"):
        session['presentOrderRestaurant']= pastOrderList
        session.modified = True
        return render_template('pastOrderRestaurant.html',pastOrderList=pastOrderList)

@app.route('/nearbyDeliveryAgents')
@check_token
def nearbyDeliveryAgents():

    if session['sessionUser']['userType']!='restaurant':
        return redirect(url_for('logout'))

    areaId=session['sessionUser']['areaId']

    nearbyDeliveryAgentsList=[]

    doc_reference = db.collection('deliveryAgent').stream()

    for doc in doc_reference:
        temp_dict=doc.to_dict()
        if temp_dict['areaId']==areaId:
            temp_dict['areaName'] = db.collection('area').document(temp_dict['areaId']).get().to_dict()['name']
            temp_dict['ratingValue']= db.collection('rating').document(temp_dict['ratingId']).get().to_dict()['rating']
            nearbyDeliveryAgentsList.append(temp_dict)
    # print(nearbyDeliveryAgentsList)

    return render_template('nearbyDeliveryAgent.html', nearbyDeliveryAgentsList = nearbyDeliveryAgentsList)

@app.route('/updateArea', methods=['POST', 'GET'])
@check_token
def updateArea():

    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))

    deliveryAgentId=session['userId']
    newAreaId=request.form['area']
    print(newAreaId)
    db.collection('deliveryAgent').document(deliveryAgentId).update({'areaId':newAreaId})

    return redirect(url_for('deliveryAgentDashboard'))


@app.route('/seeDeliveryRequest')
@check_token
def seeDeliveryRequest():

    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))

    areaId=session['sessionUser']['areaId']

    orderIdForADeliveryAgent=db.collection('area').document(areaId).get().to_dict()['availableOrderIdForPickup']
    deliveryRequestList=[]

    for orderId in orderIdForADeliveryAgent:
        temp_dict=db.collection('order').document(orderId).get().to_dict()

        if temp_dict['isPending']==True: # it will be true , just doing it to be on the safe side
            temp_dict['restaurant']=db.collection('restaurant').document(temp_dict['restaurantId']).get().to_dict()
            temp_dict['customer']=db.collection('customer').document(temp_dict['customerId']).get().to_dict()
            temp_dict['area']=db.collection('area').document(areaId).get().to_dict()
            deliveryRequestList.append(temp_dict)
    session['currentDeliveryRequest'] = deliveryRequestList
    session.modified = True
    return render_template("seeDeliveryRequest.html", deliveryRequestList = deliveryRequestList)

@app.route('/acceptDeliveryRequest', methods=['POST', 'GET'])
@check_token
def acceptDeliveryRequest():
    
    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))
    
    timeToReachRestaurant = request.form['timeToRestaurant']
    timeToReachCustomer = request.form['timeToCustomer']
    updateOrderDic = {
        "timePickUp" : timeToReachRestaurant,
        "deliveryTime" : timeToReachCustomer
    }
    db.collection('order').document(session['currentOrderDeliveryAgent']['orderId']).update({'deliveryAgentId': session['userId']})
    db.collection('order').document(session['currentOrderDeliveryAgent']['orderId']).update({'updateMessage': "Order Accepted by Delivery Agent"})
    db.collection('order').document(session['currentOrderDeliveryAgent']['orderId']).update({'updateLevel': 3})
    db.collection('order').document(session['currentOrderDeliveryAgent']['orderId']).update({'orderUpdates' : firestore.ArrayUnion([updateOrderDic])})
    # print(session['currentOrderDeliveryAgent']['orderId'])
    db.collection('area').document(session['sessionUser']['areaId']).update({'availableOrderIdForPickup' : firestore.ArrayRemove([session['currentOrderDeliveryAgent']['orderId']])})
    db.collection('deliveryAgent').document(session['userId']).update({"isAvailable" : not session['sessionUser']['isAvailable']})
    db.collection('deliveryAgent').document(session['userId']).update({"currentOrderId" : session['currentOrderDeliveryAgent']['orderId']})

    return redirect(url_for('moreDetailsDeliveryRequest', status = "Details"))

@app.route('/moreDetailsDeliveryRequest<status>')
@check_token
def moreDetailsDeliveryRequest(status):

    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))
    print(status)
    if status != "NoOrder":
        session['currentOrderDeliveryAgent'] = db.collection('order').document(session['currentOrderDeliveryAgent']['orderId']).get().to_dict()
        session.modified = True
    showButton=3
    if status == "NoOrder":
        printTable = False
    else: 
        printTable = True
        if status == "Accept":
            showButton = 1
        elif status == "Details" and session['currentOrderDeliveryAgent']['updateLevel'] == 4 :
            showButton = 2
        elif status == "Details" and session['currentOrderDeliveryAgent']['updateLevel']==2:
            showButton = 0
        else:
            showButton = 3
            
    currentOrder = None
    customerName = None
    restaurantName = None
    address = None
    orderList = None
    cost = None
    discount = None
    deliveryCharge = None
    final = None
    if status != "NoOrder":
        currentOrder = session['currentOrderDeliveryAgent']
        customerName = db.collection('customer').document(currentOrder['customerId']).get().to_dict()['name']
        restaurantName = db.collection('restaurant').document(currentOrder['restaurantId']).get().to_dict()['name']
        address = db.collection('customer').document(currentOrder['customerId']).get().to_dict()['address']
        orderList = currentOrder['orderList']
        cost = currentOrder['orderValue']
        discount = int(currentOrder['discountValue'])
    # print(discount)
        deliveryCharge = currentOrder['deliveryCharge']
        final = currentOrder['paidValue']

    return render_template('moreDetailsDeliveryAgent.html', customerName=customerName, restaurantName=restaurantName, address = address, orderList=orderList, cost= cost, discount=discount, deliveryCharge=deliveryCharge, final= final, showButton = showButton, printTable = printTable)

@app.route('/markLocation')
@check_token
def markLocation():
    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))
    doc_reference = db.collection('area').stream()
    area_dict=[]
    for doc in doc_reference:
        temp_dict=doc.to_dict()
        area_dict.append(temp_dict)
        
    currentArea = db.collection('area').document(session['sessionUser']['areaId']).get().to_dict()
    return render_template("markLocation.html", area_dict = area_dict, currentArea = currentArea)

@app.route('/orderDetailDeliveryAgent<orderId>')
@check_token
def orderDetailDeliveryAgent(orderId):
    if session['sessionUser']['userType'] != 'deliveryAgent':
        return redirect(url_for('logout'))
    orderId=int(orderId)
    orderId = orderId-1
    session['currentOrderDeliveryAgent']=session['currentDeliveryRequest'][orderId]
    session.modified = True
    return redirect(url_for('moreDetailsDeliveryRequest', status = "Details"))

@app.route('/acceptOrderForDelivery')
@check_token
def acceptOrderForDelivery():
    if session['sessionUser']['userType'] != 'deliveryAgent':
        return redirect(url_for('logout'))
    return redirect(url_for('moreDetailsDeliveryRequest', status = "Accept"))
    
@app.route('/updateStatus4')
@check_token
def updateStatus4():
    if session['sessionUser']['userType'] != 'deliveryAgent':
        return redirect(url_for('logout'))
    currentOrder = session['currentOrderDeliveryAgent']
    db.collection('order').document(currentOrder['orderId']).update({'updateMessage': "Order Delivered"})
    db.collection('order').document(currentOrder['orderId']).update({'updateLevel': 5})
    db.collection('order').document(currentOrder['orderId']).update({'isPending': False})
    db.collection('customer').document(currentOrder['customerId']).update({'pendingOrderId' : firestore.ArrayRemove([currentOrder['orderId']])})
    db.collection('restaurant').document(currentOrder['restaurantId']).update({'pendingOrderId' : firestore.ArrayRemove([currentOrder['orderId']])})
    db.collection('deliveryAgent').document(currentOrder['deliveryAgentId']).update({'currentOrderId' : None})
    session['currentOrderDeliveryAgent']=None
    session.modified=True
    return redirect(url_for('deliveryAgentDashboard'))

@app.route('/currentOrderDeliveryAgent')
@check_token
def currentOrderDeliveryAgent():
    if session['sessionUser']['userType'] != 'deliveryAgent':
        return redirect(url_for('logout'))
    user=session['sessionUser']
    currentOrderId = db.collection(user['userType']).document(session['userId']).get().to_dict()['currentOrderId']
    if currentOrderId == "":
        return redirect(url_for('moreDetailsDeliveryRequest', status = "NoOrder"))
    else: 
        session['currentOrderDeliveryAgent'] = db.collection('order').document(currentOrderId).get().to_dict()
        session.modified = True
        return redirect(url_for('moreDetailsDeliveryRequest', status = "Details")) 
    
@app.route('/ratingDeliveryAgent', methods=['POST', 'GET'])
@check_token
def ratingDeliveryAgent():
    
    if session['sessionUser']['userType']!='deliveryAgent':
        return redirect(url_for('logout'))

    customerId=session['currentOrderDeliveryAgent']['customerId']
    rating=request.form['customerRating']
    rating=int(rating)

    ratingId=db.collection('customer').document(customerId).get().to_dict()['ratingId']
    ratingObject=db.collection('rating').document(ratingId).get().to_dict()

    ratingObject['noOfInputs'] = ratingObject['noOfInputs'] + 1
    ratingObject['sum'] = ratingObject['sum'] + rating
    ratingObject['rating'] = ratingObject['sum']/ratingObject['noOfInputs']

    db.collection('rating').document(ratingId).set(ratingObject)
    
    currentOrder = session['currentOrderDeliveryAgent']
    db.collection('order').document(currentOrder['orderId']).update({'updateMessage': "OrderDelivered"})
    db.collection('order').document(currentOrder['orderId']).update({'updateLevel': 5})
    db.collection('order').document(currentOrder['orderId']).update({'isPending': False})
    db.collection('customer').document(currentOrder['customerId']).update({'pendingOrderId' : firestore.ArrayRemove([currentOrder['orderId']])})
    db.collection('restaurant').document(currentOrder['restaurantId']).update({'pendingOrderId' : firestore.ArrayRemove([currentOrder['orderId']])})
    db.collection('deliveryAgent').document(currentOrder['deliveryAgentId']).update({'isAvailable' : True})
    db.collection('deliveryAgent').document(currentOrder['deliveryAgentId']).update({'currentOrderId': None})
    session['currentOrderDeliveryAgent']=None
    session.modified=True
    return redirect(url_for('deliveryAgentDashboard'))
    

@app.route('/ratingCustomer', methods=['POST', 'GET'])
@check_token
def ratingCustomer():
    
    if session['sessionUser']['userType']!='customer':
        return redirect(url_for('logout'))


    orderId=session['customerCurrentOrderChanging']['orderId']
    db.collection('order').document(orderId).update({'updateLevel': 6})
    deliveryAgentId = db.collection("order").document(orderId).get().to_dict()['deliveryAgentId']
    deliveryAgentRating=request.form['deliveryAgentRating']
    deliveryAgentRating=int(deliveryAgentRating)

    deliveryAgentRatingId=db.collection('deliveryAgent').document(deliveryAgentId).get().to_dict()['ratingId']
    deliveryAgentRatingObject=db.collection('rating').document(deliveryAgentRatingId).get().to_dict()
    
    
    
    deliveryAgentRatingObject['noOfInputs'] = deliveryAgentRatingObject['noOfInputs'] + 1
    deliveryAgentRatingObject['sum'] = deliveryAgentRatingObject['sum'] + deliveryAgentRating
    deliveryAgentRatingObject['rating'] = deliveryAgentRatingObject['sum']/deliveryAgentRatingObject['noOfInputs']

    db.collection('rating').document(deliveryAgentRatingId).set(deliveryAgentRatingObject)


    restaurantId = db.collection("order").document(orderId).get().to_dict()['restaurantId']
    restaurantRating=request.form['restaurantRating']
    restaurantRating=int(restaurantRating)

    restaurantRatingId=db.collection('restaurant').document(restaurantId).get().to_dict()['ratingId']
    restaurantRatingObject=db.collection('rating').document(restaurantRatingId).get().to_dict()

    restaurantRatingObject['noOfInputs'] = restaurantRatingObject['noOfInputs'] + 1
    restaurantRatingObject['sum'] = restaurantRatingObject['sum'] + restaurantRating
    restaurantRatingObject['rating'] = restaurantRatingObject['sum']/restaurantRatingObject['noOfInputs']

    db.collection('rating').document(restaurantRatingId).set(restaurantRatingObject)

    return redirect(url_for('pastOrder'))

if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)