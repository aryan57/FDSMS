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
app.secret_key ='a very very very long string'

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred,json.load(open('fbConfig.json')))
pyrebase_pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
bucket = storage.bucket()
# storage = pyrebase_pb.storage()

try:
    json_data=db.collection('restaurant').document('KgAsPjK7aLcDN01kbWnW1lqcy063').get().to_dict()
    print(json_data)
except Exception as e:
    print(e)


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
    storage_file_path=""
    if area=='Other':
        session['sign_message'] = "We currently don't have service in your area."
        return redirect(url_for('restaurantSignup'))
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "restaurant/"+user.uid+".jpg"
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('restaurantSignup'))
    try:
        json_data = {
            "name" : name,
            "areaId" : area,
            "ratingId": "",
            "restaurantId" : user.uid,
            "restaurantPicSrc" : storage_file_path,
            "pendingOrderId": [],
            "completedOrderId": [],
            "email" : email,
            "isRecommended" : False
        }
        db.collection("restaurant").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "restaurant"})
        
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('restaurantSignup'))
    try:
        
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
    storage_file_path = ""
    if area=='Other':
        session['sign_message'] = "We currently don't deliver in your area."
        return redirect(url_for('deliveryAgentSignup'))

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "deliveryAgent/"+user.uid+".jpg"
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('deliveryAgentSignup'))
    
    try:
        json_data = {
            "name" : name,
            "dateOfBirth" : dob,
            "mobileNumber" : mobile,
            "picSrc" : storage_file_path,
            "email" : email,
            "gender" : gender,
            "areaId" : area,
            "deliveryAgentId" : user.uid,
            "ratingId" : "",
            "isAvailable" : True
        }
        db.collection("deliveryAgent").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "deliveryAgent"})
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('deliveryAgentSignup'))
    try:
        
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['sign_message']="Delivery Agent SignedUp. Please Login"
        return redirect(url_for('login'))
    except:
        session['sign_message']="error uploading photo in firebase storage"
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
    local_file_obj = request.files['local_file_path']
    storage_file_path = ""
    if area=='Other':
        session['sign_message'] = "We currently don't deliver in your area."
        return redirect(url_for('customerSignup'))
    # create user
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "customer/"+user.uid+".jpg"
    except:
        session['sign_message']="error creating user in firebase"
        return redirect(url_for('customerSignup'))
    
    # add data in fire-store
    try:
        json_data = {
            "name" : name,
            "dateOfBirth" : dob,
            "mobileNumber" : mobile,
            "email" : email,
            "gender" : gender,
            "areaId" : area,
            "customerId":user.uid,
            "ratingId":"",
            "picSrc": storage_file_path
        }
        db.collection("customer").document(user.uid).set(json_data)
        db.collection("type").document(user.uid).set({"type" : "customer"})
    except:
        session['sign_message']="error adding user text data in firestore"
        return redirect(url_for('customerSignup'))

    # upload profile picture
    try:
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        session['sign_message']='Signup was Succesful. Please Login'
        return redirect(url_for('login'))
    except:
        session['sign_message']="error uploading photo in firebase storage"
        return redirect(url_for('customerSignup'))

@app.route("/temp")
def temp():
    # blob = bucket.blob("customer/"+"YQ2pF5uHW7ZCvfpIzUD1sTcZL5n2"+".jpg")
    blob = bucket.blob("restaurant/"+"oDtSvO2uB8UE6889JHPRFTLvHJY2"+".jpg")

    imagePublicURL = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
    return {"imageLink":imagePublicURL},200



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
    if not user['user_type'] == 'restaurant':
        return redirect(url_for('logout'))
    currentRestaurantMenuId=session['user_id']
    foodItemList=[]
    docs=db.collection('restaurant').document(currentRestaurantMenuId).collection('foodItem').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        print(temp_dict)
        temp_dict['food_item_id']= doc.id
        foodItemList.append(temp_dict)
    try:
        message=session['food_item_addition_msg']
        session['food_item_addition_msg']="False"
    except: 
        session['food_item_addition_msg']="False"
        message="False"
    return render_template('createMenu.html', user=user, menuList=foodItemList, message=message)

@app.route('/addFoodItem')
@check_token
def addFoodItem():
    user = session['session_user']
    if user['user_type'] == 'restaurant':
        message=session['food_item_addition_msg']
        session['food_item_addition_msg']="False"
        return render_template('addFoodItem.html', user=user, message=message)
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
            "ratingId": "",
            "restaurantId" : session["user_id"],
            "picSrc": ""
        }
        doc_reference = db.collection("restaurant").document(session["user_id"]).collection("foodItem").document()
        doc_reference.set(foodItem)
        doc_reference1 = db.collection("restaurant").document(session["user_id"]).collection("foodItem").document(doc_reference.id).update({"foodItemId":doc_reference.id})
        # return {"ok":"True"},200
        
    except:
        session['food_item_addition_msg'] = "Error adding food item text data in database"
        return redirect(url_for('addFoodItem'))
    try:
        storage_file_path = "restaurant/"+session["user_id"]+"_"+doc_reference.id+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_file(local_file_obj,content_type="image/jpeg")
        doc_reference = db.collection("restaurant").document(session["user_id"]).collection("foodItem").document(doc_reference.id).update({"picSrc":storage_file_path})
        session['food_item_addition_msg']="Food item text and photo successfully added in database."
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
    session['restaurantList']=[]
    
    docs=db.collection('restaurant').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['user_id']= doc.id
        session['restaurantList'].append(temp_dict)
    restaurantList=session['restaurantList']
    return render_template('allRestaurant.html', user=user, restaurantList=restaurantList)

@app.route('/allCustomers')
@check_token
def allCustomers():
    user=session['session_user']
    if not user['user_type']=="admin":
        return redirect(url_for('logout'))
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
    session['deliveryAgentList']=[]
    docs=db.collection('deliveryAgent').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['user_id']= doc.id
        session['deliveryAgentList'].append(temp_dict)
    return render_template('allDeliveryAgents.html', user=user)

@app.route('/allFoodItem11/<restaurantUserId>')
@check_token
def allFoodItem11(restaurantUserId):
    session['currentRestaurantMenuId']=restaurantUserId
    return redirect(url_for('allFoodItem'))


@app.route('/allFoodItem')
@check_token
def allFoodItem():

    user=session['session_user']
    if not user['user_type']=='customer' and not user['user_type']=='admin':
        return redirect(url_for('logout'))

    foodItemList=[]
    docs=db.collection('restaurant').document(session['currentRestaurantMenuId']).collection('foodItem').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        # print(temp_dict)
        temp_dict['food_item_id']= doc.id
        foodItemList.append(temp_dict)
    session['current_menu_viewed']=foodItemList
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
    
    
@app.route('/order', methods=['POST','GET'])
@check_token
def order():
    foodItemList = session['current_menu_viewed']
    
    cost = 0
    orderList = []
    for i in range(len(foodItemList)):
        if(request.form[str(i+1)]):
            foodItemList[i]['frequency'] = request.form[str(i+1)]
            orderList.append(foodItemList[i])
            cost += int(foodItemList[i]['pricePerItem']) * int(foodItemList[i]['frequency'])
            
    session['currentOrderCreating'] = {'cost': cost, 
            'orderList': orderList, 
            'deliveryChange': 50,
            'isPending': True,
            'customerId': session['user_id'],
            'restaurantId': foodItemList[0]['restaurantId'],
            'offerId': None
    }
    return render_template('orderDetails.html')

@app.route('/redirectDashboard')
@check_token
def redirectDashboard():
    if session['session_user']['user_type']=='customer':
        return redirect(url_for('customerDashboard'))
    elif session['session_user']['user_type']=='restaurant':
        return redirect(url_for('restaurantDashboard'))
    elif session['session_user']['user_type']=='deliveryAgent':
        return redirect(url_for('deliverAgentDashboard'))
    elif session['session_user']['user_type']=='admin':
        return redirect(url_for('adminDashboard'))
    
@app.route('/deleteFoodItem<foodItemId>')
@check_token
def deleteFoodItem(foodItemId):
    restaurantId=session['user_id']

    #command_to delete the id
    try:
        db.collection("restaurant").document(restaurantId).collection('foodItem').document(foodItemId).delete()
        session['food_item_addition_msg']="food item deletion from databse is successful"
    except Exception as e:
        # print(e)
        session['food_item_addition_msg']="Error deleting food item from databse"

    return redirect(url_for('createMenu'))

@app.route('/changeRecommendRestaurant<id_to_change>')
@check_token
def changeRecommendRestaurant(id_to_change):
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
    id=int(id_to_change)
    id=id-1
    if session['current_menu_viewed'][id]['isRecommended'] == False:
        session['restaurantList'][id]['isRecommended'] = True
        session.modified = True
    else :
        session['current_menu_viewed'][id]['isRecommended'] = False
        session.modified = True

    foodItemId=session['current_menu_viewed'][id]['foodItemId']
    restaurantId=session['current_menu_viewed'][id]['restaurantId']

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
    user=session['session_user']
    if not user['user_type'] == 'customer':
        return redirect(url_for('logout'))
    session['restaurantList']=[]
    docs=db.collection('restaurant').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['user_id']= doc.id
        session['restaurantList'].append(temp_dict)
    restaurantList=[]
    for restaurant in session['restaurantList']:
        if restaurant['isRecommended']:
            restaurantList.append(restaurant)
    
    return render_template('recommendedRestaurant.html', restaurantList=restaurantList, user=user)
        

@app.route('/createOffer')
@check_token
def createOffer():
    user = session['session_user']
    if not user['user_type'] == 'admin':
        return redirect(url_for('logout'))
    currentAdminId=session['user_id']
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
    user = session['session_user']
    if user['user_type'] == 'admin':
        message=session['offerAdditionMessage']
        session['offerAdditionMessage']="False"
        return render_template('addOffer.html', user=user, message=message)
    else:
        return redirect(url_for('logout'))

@app.route('/addOffer/adder', methods=['POST','GET'])
@check_token
def offerAdder():
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
    customer_id=int(customer_id)
    customer_id=customer_id-1
    session['customerGettingOffer']=session['customerList'][customer_id]['customerId']
    
    session['offerList']=[]
    docs=db.collection('offer').stream()
    for doc in docs:
        temp_dict=doc.to_dict()
        temp_dict['offerId']= doc.id
        session['offerList'].append(temp_dict)
    offerList=session['offerList']
    return render_template(url_for('allOfferAdmin.html', offerList=offerList))


@app.route('/giveOffer<toGive>')
@check_token
def giveOffer(toGive):
    toGive=int(toGive)
    toGive=toGive-1

    customerGettingOffer=session['customerGettingOffer']
    offerId=session['offerList'][toGive]['offerId']
    
    # push that id in the list by creating a copy of that offer
    
    return redirect(url_for('allCustomers'))



if __name__ == "__main__":
    # cache.init_app(app)
    app.run(debug=True)