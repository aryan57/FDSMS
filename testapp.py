from logging import exception
from os import name
import os
import firebase_admin
from flask.helpers import url_for
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
import json
import datetime
import requests
from requests.exceptions import HTTPError
from PIL import Image

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred,json.load(open('fbConfig.json')))
pyrebase_pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
bucket = storage.bucket()

DEBUG=True

# ################# utility functions#################
def testRestaurantsignup(email,password,area,name,local_file_path):
    storage_file_path=""
    error_message=[]
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "restaurant/"+user.uid+".jpg"
    except Exception as e:
        error_message.append(str(e))
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
        
    except Exception as e:
        error_message.append(str(e))
    try:
        
        blob = bucket.blob(storage_file_path)
        blob.upload_from_filename(local_file_path,content_type="image/jpeg")
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("testRestaurantsignup")
            print(error_message)
        return "FAILED"

def testDeliveryAgentsignup(email,password,gender,area,mobile,dob,name,local_file_path):
    storage_file_path = ""
    error_message=[]
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "deliveryAgent/"+user.uid+".jpg"
    except Exception as e:
        error_message.append(str(e))
    
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
    except Exception as e:
        error_message.append(str(e))
    try:
        
        blob = bucket.blob(storage_file_path)
        blob.upload_from_filename(local_file_path,content_type="image/jpeg")
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("testDeliveryAgentsignup")
            print(error_message)
        return "FAILED"

def testCustomerSignup(email,password,gender,area,mobile,dob,name,local_file_path):

    error_message=[]
    storage_file_path=""

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "customer/"+user.uid+".jpg"
    except Exception as e:
        error_message.append(str(e))
    
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
    except Exception as e:
        error_message.append(str(e))

    # upload profile picture
    try:
        blob = bucket.blob(storage_file_path)
        blob.upload_from_filename(local_file_path,content_type="image/jpeg")
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("testCustomerSignup")
            print(error_message)
        return "FAILED"

def testGetProfilePicture(email,password,type):

    try :
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
        blob = bucket.blob(type+"/"+user["localId"]+".jpg")
        imagePublicURL = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
    except Exception as e:
        return "FAILED"

    return "PASSED\nURL : "+imagePublicURL

def testdelete_user(user_id):

    error_message=[]

    user_type=""

    try:
        auth.delete_user(user_id)
    except Exception as e:
        error_message.append(str(e))

    try:
        user_type = db.collection('type').document(user_id).get().to_dict()["type"]
        if(user_type=="restaurant"):
            # If you have larger collections, you may want to delete the documents in smaller batches to avoid out-of-memory errors.
            delete_collection(db.collection("restaurant").document(user_id).collection("foodItem"),1000)
        db.collection(user_type).document(user_id).delete()
        db.collection("type").document(user_id).delete()
    except Exception as e:
        error_message.append(str(e))

    try:
        # deleting profile pictures
        bucket.delete_blob(user_type+"/"+user_id+".jpg")
        
        # deleting food item images
        if user_type=="restaurant":
            blob_objects=bucket.list_blobs(prefix="restaurant/"+user_id+"_")
            blob_object_names=[]
            for blob in blob_objects:
                blob_object_names.append(blob.name)
            bucket.delete_blobs(blob_object_names)
    
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("delete_user")
            print(error_message)
        return "FAILED"

# helper function for function 'deleteUserFromDatabase'
def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

def testSignIn(email,password):
    try:
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
    except Exception as e:
        if DEBUG:
            print("testSignIn")
            print(str(e))
        return "FAILED"
    return "PASSED"

def testfoodItemAdder(name,price,local_file_path,restaurantId):
    
    error_message=[]

    try:
        foodItem = {
            "name" : name,
            "pricePerItem" : price,
            "isRecommended": False,
            "ratingId": "",
            "restaurantId" : restaurantId,
            "picSrc": ""
        }
        doc_reference = db.collection("restaurant").document(restaurantId).collection("foodItem").document()
    except Exception as e:
        error_message.append(str(e))
    
    try:
        doc_reference.set(foodItem)
    except Exception as e:
        error_message.append(str(e))
    try:
        db.collection("restaurant").document(restaurantId).collection("foodItem").document(doc_reference.id).update({"foodItemId":doc_reference.id})
    except Exception as e:
        error_message.append(str(e))

    try:
        storage_file_path = "restaurant/"+restaurantId+"_"+doc_reference.id+".jpg"
        blob = bucket.blob(storage_file_path)
        blob.upload_from_filename(local_file_path,content_type="image/jpeg")
        doc_reference = db.collection("restaurant").document(restaurantId).collection("foodItem").document(doc_reference.id).update({"picSrc":storage_file_path})
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("foodItemAdder")
            print(error_message)
        return "FAILED"

def testGetMenu(currentRestaurantMenuId):

    error_message=[]
    foodItemList=[]

    try:
        docs=db.collection('restaurant').document(currentRestaurantMenuId).collection('foodItem').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['food_item_id']= doc.id
            foodItemList.append(temp_dict)

    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED - fetch "+str(len(foodItemList))+" items"
    else :
        if DEBUG:
            print("testGetMenu")
            print(error_message)
        return "FAILED"

def testGetAllRestaurant():
    restaurantList=[]
    error_message=[]
    try:
        docs=db.collection('restaurant').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            restaurantList.append(temp_dict)
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED - fetch "+str(len(restaurantList))+" restaurants"
    else :
        if DEBUG:
            print("testGetAllRestaurant")
            print(error_message)
        return "FAILED"

def testGetAllCustomer():
    customerList=[]
    error_message=[]
    try:
        docs=db.collection('customer').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            customerList.append(temp_dict)
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED - fetch "+str(len(customerList))+" customers"
    else :
        if DEBUG:
            print("testGetAllCustomer")
            print(error_message)
        return "FAILED"

def testGetAllDelivery():
    deliveryList=[]
    error_message=[]
    try:
        docs=db.collection('deliveryAgent').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            deliveryList.append(temp_dict)
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED - fetch "+str(len(deliveryList))+" delivery agents"
    else :
        if DEBUG:
            print("testGetAllDelivery")
            print(error_message)
        return "FAILED"

def testchangeRecommendFoodItem(foodItemId,restaurantId):
    error_message=[]
    isRecommended=""
    try:
        isRecommended = db.collection("restaurant").document(restaurantId).collection("foodItem").document(foodItemId).get().to_dict()['isRecommended']
    except Exception as e:
        error_message.append(str(e))
    
    try:
        db.collection("restaurant").document(restaurantId).collection("foodItem").document(foodItemId).update({'isRecommended':not isRecommended})
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("testchangeRecommendFoodItem")
            print(error_message)
        return "FAILED"

def testchangeRecommendedRestaurant(restaurantId):
    error_message=[]
    isRecommended=""
    try:
        isRecommended = db.collection("restaurant").document(restaurantId).get().to_dict()['isRecommended']
    except Exception as e:
        error_message.append(str(e))
    
    try:
        db.collection("restaurant").document(restaurantId).update({'isRecommended':not isRecommended})
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED"
    else :
        if DEBUG:
            print("testchangeRecommendedRestaurant")
            print(error_message)
        return "FAILED"

def testgetRecommendedRestaurant():
    error_message=[]

    restaurantList=[]
    recommendedRestaurantList=[]

    try:
        docs=db.collection('restaurant').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            restaurantList.append(temp_dict)
    except Exception as e:
        error_message.append(str(e))
    
    try:
        for restaurant in restaurantList:
            if restaurant['isRecommended']:
                recommendedRestaurantList.append(restaurant)
    except Exception as e:
        error_message.append(str(e))
    
    if(len(error_message)==0):
        return "PASSED - fetch "+str(len(recommendedRestaurantList))+" recommended restaurants"
    else :
        if DEBUG:
            print("testgetRecommendedRestaurant")
            print(error_message)
        return "FAILED"

# ################# caller functions#################

def calltestRestaurantsignup():
    email="demo.restaurant@gmail.com"
    password="password123"
    area="Delhi"
    name="Demo Restaurant"
    local_file_path=os.path.abspath('static/test_images/restaurant.jpg')
    result=testRestaurantsignup(email,password,area,name,local_file_path)
    print("testRestaurantsignup - "+result)

def calltestDeliveryAgentsignup():
    email="demo.deliveryagent@gmail.com"
    password="password123"
    gender="Male"
    area="Delhi"
    mobile="+919876543210"
    dob="29/04/2001"
    name="Demo Delivery Agent"
    local_file_path=os.path.abspath('static/test_images/deliveryAgent.jpg')
    result=testDeliveryAgentsignup(email,password,gender,area,mobile,dob,name,local_file_path)
    print("testDeliveryAgentsignup - "+result)

def calltestCustomerSignup():
    email="demo.customer@gmail.com"
    password="password123"
    gender="Male"
    area="Delhi"
    mobile="+919876454562"
    dob="30/09/2004"
    name="Demo Customer"
    local_file_path=os.path.abspath('static/test_images/customer.jpg')
    result=testCustomerSignup(email,password,gender,area,mobile,dob,name,local_file_path)
    print("testCustomerSignup - "+result)

def calltestGetProfilePicture():

    email="demo.restaurant@gmail.com"
    password="password123"
    type="restaurant"
    result=testGetProfilePicture(email,password,type)
    print("testGetProfilePicture - restaurant - "+result)

    email="demo.deliveryagent@gmail.com"
    password="password123"
    type="deliveryAgent"
    result=testGetProfilePicture(email,password,type)
    print("testGetProfilePicture - deliveryagent - "+result)

    email="demo.customer@gmail.com"
    password="password123"
    type="customer"
    result=testGetProfilePicture(email,password,type)
    print("testGetProfilePicture - customer - "+result)

def calltestdelete_user():
    user_id=""
    result=testdelete_user(user_id)
    print('calltestdelete_user - '+result)

def calltestGetMenu():
    currentRestaurantMenuId=""
    result=testGetMenu(currentRestaurantMenuId)
    print('calltestGetMenu - '+result)

def calltestfoodItemAdder():
    name="Burger"
    price="80"
    local_file_path=os.path.abspath('static/test_images/burger.jpg')
    restaurantId=""
    result=testfoodItemAdder(name,price,local_file_path,restaurantId)
    print('calltestfoodItemAdder - '+result)

def calltestSignIn():
    email="demo.customer@gmail.com"
    password="password123"
    result=testSignIn(email,password)
    print('calltestSignIn - '+result)

def calltestGetAllRestaurant():
    result=testGetAllRestaurant()
    print('calltestGetAllRestaurant - '+result)
def calltestGetAllCustomer():
    result=testGetAllCustomer()
    print('calltestGetAllCustomer - '+result)
def calltestGetAllDelivery():
    result=testGetAllDelivery()
    print('calltestGetAllDelivery - '+result)

def calltestchangeRecommendFoodItem():
    foodItemId=""
    restaurantId=""
    result=testchangeRecommendFoodItem(foodItemId,restaurantId)
    print('calltestchangeRecommendFoodItem - '+result)

def calltestchangeRecommendedRestaurant():
    restaurantId=""
    result=testchangeRecommendedRestaurant(restaurantId)
    print('calltestchangeRecommendedRestaurant - '+result)

def calltestgetRecommendedRestaurant():
    result=testgetRecommendedRestaurant()
    print('calltestgetRecommendedRestaurant - '+result)

if __name__ == "__main__":

    '''
    these are the caller functions
    '''

    # calltestRestaurantsignup()
    # calltestDeliveryAgentsignup()
    # calltestCustomerSignup()
    # calltestGetProfilePicture()
    # calltestdelete_user()
    # calltestfoodItemAdder()
    # calltestGetMenu()
    # calltestSignIn()
    # calltestGetAllRestaurant()
    # calltestGetAllCustomer()
    # calltestGetAllDelivery()
    # calltestchangeRecommendFoodItem()
    # calltestchangeRecommendedRestaurant()
    # calltestgetRecommendedRestaurant()