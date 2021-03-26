from logging import exception
from os import name
import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
import json
import datetime
import requests
from requests.exceptions import HTTPError

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred,json.load(open('fbConfig.json')))
pyrebase_pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
bucket = storage.bucket()


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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"

def testDeliveryAgentsignup(email,password,gender,area,mobile,dob,name,local_file_path):
    storage_file_path = ""
    error_message=[]
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "deliveryProfilePics/"+user.uid+".jpg"
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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"

def testCustomerSignup(email,password,gender,area,mobile,dob,name,local_file_path):

    error_message=[]
    storage_file_path=""

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        storage_file_path = "customerProfilePics/"+user.uid+".jpg"
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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"


def testGetRestaurantProfilePicture(email,password):

    try :
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
        blob = bucket.blob("restaurantProfilePics/"+user["localId"]+".jpg")
        imagePublicURL = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
    except Exception as e:
        return "FAILED\n"

    return {"PASS":"true","imagePublicURL":imagePublicURL}


def delete_user(user_id):

    error_message=[]

    try:
        auth.delete_user(user_id)
    except Exception as e:
        error_message.append(str(e))
    
    try:
        user_type = db.collection('type').document(user_id).get().to_dict()["type"]
        db.collection(user_type).document(user_id).delete()
    except Exception as e:
        error_message.append(str(e))
        
    try:
        db.collection("type").document(user_id).delete()
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"


def testSignIn(email,password):
    try:
        user = pyrebase_pb.auth().sign_in_with_email_and_password(email, password)
    except Exception as e:
        # print(str(e))
        return "FAILED\n"
    return "PASSED\n"


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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"

def foodItemAdder(name,price,local_file_path,restaurantId):
    
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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"


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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"

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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"

def testGetAllDelivery():
    deliveryList=[]
    error_message=[]
    try:
        docs=db.collection('delivery').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['user_id']= doc.id
            deliveryList.append(temp_dict)
    except Exception as e:
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"


def allFoodItem(currentRestaurantMenuId):

    foodItemList=[]

    try:
        docs=db.collection('restaurant').document(currentRestaurantMenuId).collection('foodItem').stream()
        for doc in docs:
            temp_dict=doc.to_dict()
            temp_dict['food_item_id']= doc.id
            foodItemList.append(temp_dict)
    except Exception as e:
        return "FAILED\n"

    return "PASSED\n"

def deleteUserFromDatabase(to_delete):

    error_message=[]

    try:
        auth.delete_user(to_delete)
    except Exception as e:
        error_message.append(str(e))

    try:
        user_type = db.collection('type').document(to_delete).get().to_dict()["type"]
        if(user_type=="restaurant"):
            # If you have larger collections, you may want to delete the documents in smaller batches to avoid out-of-memory errors.
            delete_collection(db.collection("restaurant").document(to_delete).collection("foodItem"),1000)
        db.collection(user_type).document(to_delete).delete()
        db.collection("type").document(to_delete).delete()
    except Exception as e:
        error_message.append(str(e))

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
        error_message.append(str(e))

    if(len(error_message)==0):
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"
    
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

def recommendedRestaurant():
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
        return "PASSED\n"
    else :
        # print(error_message)
        return "FAILED\n"
        
if __name__ == "__main__":
    # cache.init_app(app)
    # TODO call functions
    '''
    '''