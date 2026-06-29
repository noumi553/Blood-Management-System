from flask import Flask, render_template,request,jsonify,redirect,make_response,send_from_directory,session
import os
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import jwt
import smtplib
import random
import time
import threading
from email.mime.text import MIMEText
from functools import wraps
from bson.objectid import ObjectId

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017")
try:
    client.server_info()
    print("Connected to MongoDB ✅")
except Exception as e:
    print("MongoDB connection error ❌:", e)

db = client["testdb"]
print(type(db))
print(db)
collection = db["mycollection"]
adminCollection = db["adminCollection"]
recepCollection = db['recepCollection']
#=======================================================================================
@app.route("/signin")
def signin():
    return render_template("signin.html")
#=======================================================================================
otpEmail = {}
#=======================================================================================
@app.route("/signup")
def signup():
    return render_template("signup.html")
#=======================================================================================
@app.route('/registerUser', methods=['POST'])
def registerUser():
    personalDetail = request.get_json()
    if personalDetail is None:
        return jsonify({"msg": "No data received"}), 400
    fields = ['name','fname','email','password','confirmPassword','verification_code','number','optionValue','gSelect']
    for field in fields:
        if not personalDetail.get(field):
            return jsonify({"msg":"Please fill the form"})
    email = personalDetail.get('email')
    userOtp = personalDetail.get('verification_code')
    print(personalDetail)
    if email in otpEmail and otpEmail[email] == userOtp:
        print("✅ OTP Verified!")
        collection.insert_one(personalDetail)
        return jsonify({"msg": "✅ OTP Verified! and Successfully Submit"})
    else:
        print("❌ Invalid OTP")
        return jsonify({"msg": "❌ Invalid OTP"}), 400
#===============================================a========================================
SECERET_KEY = 'kdyehylkdhsnxhdy37};kdjhsjdsjhsj'
def set_the_user(user):
    return jwt.encode({'_id':str(user['_id']),"email":user['email']},SECERET_KEY,algorithm='HS256')
#=======================================================================================
def get_the_user(token):
    if not token:
        return None
    try:
        return jwt.decode(token,SECERET_KEY,algorithms='HS256')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
#=======================================================================================
@app.route("/loginUser",methods=['POST'])
def loginUser():
    data = request.get_json()
    print(data)
    requiredField = ['email','password']
    
    if not all(field in data for field in requiredField):
        return jsonify({"msg":"Please fill the form"})
    
    user = collection.find_one({'email':data['email'],'password':data['password']})
    if not user:
        return jsonify({"msg":"invild password or email"})
    
    token = set_the_user(user)
    response = make_response(jsonify({"msg":"login successfully"}))
    response.set_cookie('uid',token)
    print("token",token)
    
    return response
#=======================================================================================
def auth_middleware(func):
    def wrapper(*args,**kwargs):
        token = request.cookies.get('uid')
        if not token:
            return render_template("signin.html"),401
        
        try:
            user = get_the_user(token)
            if not user:
                return jsonify({"msg":"invalid token"}),401
        except Exception as e:
            return jsonify({"msg":"invalid token"}),401
        return func(*args,**kwargs)
    return wrapper
#=======================================================================================
@app.route("/")
def home():
    return render_template("index.html")
#=======================================================================================
EMAIL_ADDRESS = "noumanaziz383@gmail.com"
EMAIL_PASSWORD = "kqhe flmv hxnt wkxl"

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route('/otp', methods=['POST'])
def send_otp():
    userOtp = request.get_json()
    email = userOtp['email']

    otp = generate_otp()
    otpEmail[email] = otp
    print('otpEmail ::',otpEmail[email])

    msg = MIMEText(f"Your OTP is: {otp}")
    msg['Subject'] = "Email Verification OTP"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("OTP sent successfully!")
    except Exception as e:
        print("Error:", e)
        return jsonify({'msg': 'Failed to send OTP'})

    return jsonify({'msg': 'OTP sent to email'})
#=======================================================================================
@app.route('/userData',methods=['GET'])
def userData():
    data = collection.find()
    docs = []
    for doc in data:
        id=doc['_id']
        docs.append({
            "id":str(doc["_id"]),
            "name": doc.get("name"),
            "fname": doc.get("fname"),
            "email":doc.get("email"),
            "BloodGroup": doc.get("gSelect"),
            "number":doc.get("number"),
            "optionValue":doc.get("optionValue"),
            "dob":doc.get("dob"),
            "location":doc.get("location"),
            "donate":doc.get("donate"),
            "file":doc.get("file"),
            "health":doc.get("health:")
        })
    return jsonify(docs)
#=======================================================================================
#ADMIN
@app.route("/adminSigninPage",methods=['GET'])
def adminSinginPage():
    return render_template("adminSignin.html")

@app.route("/adminSignin",methods=['POST'])
def adminSigin():
    data = request.get_json()
    email = data.get('email')
    password = data.get("password")
    if not email:
        return jsonify({"msg":'Please enter your email'})
    elif not password:
        return jsonify({"msg":"Please enter your password"})
    
    admin =adminCollection.find_one({'email':data['email'],'password':data['password']})
    if not admin:
        return jsonify({"msg":"Invilid email or password"})
    
    token = set_the_user(admin)
    response = make_response(jsonify({"msg":"login successfully"}))
    response.set_cookie('aid',token)
    return response
#=======================================================================================
def admin_midleware(func):
    @wraps(func)
    def adminWraper(*args,**kwargs):
        token = request.cookies.get("aid")
        if not token:
            return render_template("adminSignin.html"),401
        try:
            user = get_the_user(token)
            if not user:
                return jsonify({"msg":"invalid token"}),401
        except Exception as e:
            return jsonify({"msg":"invalid token"}),401
        return func(*args,**kwargs)
    return adminWraper
#=======================================================================================

@app.route("/admin",methods=['GET'])
@admin_midleware
def admin():
    return render_template('admin.html')
#=======================================================================================
@app.route("/donar",methods=['GET'])
@admin_midleware
def donar():
    return render_template('donar.html')
#=======================================================================================
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
userId=[]
@app.route('/upload',methods=['POST'])
def upload():
    user_id= request.form.get('id')
    print(user_id)
    
    if 'photo' not in request.files:
        return jsonify({"msg:":"photo field missing"})
    file = request.files['photo']
    filename = secure_filename(file.filename)
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
    
    filePath= os.path.join('uploads',filename)
    
    collection.update_one({'email':user_id},{'$push':{'file':filePath}})
    
    print(filePath)
    
    return jsonify({"msg":"successfully upload photo"})

@app.route('/getid',methods=['POST'])
def getid():
    body = request.get_json()
    print(body)

@app.route('/uploads/<path:path>')
def send_file(path):
    return send_from_directory('uploads',path)
#=======================================================================================
@app.route('/updateDonate',methods=['POST'])
def updateDonate():
    id = request.json['id']
    result = collection.update_one({'_id':ObjectId(id)},{'$set':{'donate':'✅'}})
    if result.modified_count == 1:
        return jsonify({'msg':'Successfully Update'})
    else:
        return jsonify({"msg":"Successfully Update"})

@app.route('/receptdelete',methods=['POST'])
def receptdelete():
    id = request.json['id']
    result = collection.update_one(
        {'_id': ObjectId(id)},
        {'$unset': {'share_contact': ""}}
    )
    return jsonify({"msg":"Your not able to donate the recep data is deleted"})

thread_running = False

def updateAutometically():
    global thread_running
    while True:
        t = 10*60
        time.sleep(t)
        result = collection.update_many({'donate':'✅'},{'$set':{'donate':'❌'}})
        if result.modified_count > 0:
            print(f"updated {result.modified_count} documents")
        time.sleep(t)

def start_thread():
    global thread_running
    if not thread_running:
        thread_running = True
        thread = threading.Thread(target=updateAutometically)
        thread.daemon = True
        thread.start()

start_thread()

#=======================================================================================
@app.route('/myData',methods=['GET'])
def myData():
    token = request.cookies.get('uid')
    if not token:
        return render_template('signin.html')
    decode = jwt.decode(token,SECERET_KEY,algorithms=["HS256"])
    user = decode['_id']
    personalDetail = collection.find({'_id':ObjectId(user)})
    userArray = []
    for doc in personalDetail:
        userArray.append({
            "id":str(doc["_id"]),
            "name": doc.get("name"),
            "fname": doc.get("fname"),
            "email":doc.get("email"),
            "BloodGroup": doc.get("gSelect"),
            "number":doc.get("number"),
            "optionValue":doc.get("optionValue"),
            "dob":doc.get("dob"),
            "location":doc.get("location"),
            "donate":doc.get("donate"),
            "file":doc.get("file"),
            "recepShareData":doc.get("share_contact"),
            "count":doc.get("count")
        })
    return jsonify(userArray)
#=======================================================================================
@app.route('/profile',methods=['GET'])
@auth_middleware
def profile():
    return render_template('profile.html')
#=======================================================================================
@app.route('/health',methods=['POST'])
def health():
    body = request.get_json()
    email = body.get('val')[0]
    heal = body.get('selected')
    print(heal)
    hel =collection.update_one({'email':email},{'$set':{'health:':heal}})
    if not hel:
        return jsonify({'msg':'can not update one'})
    return jsonify({'msg':'update one'})
#=======================================================================================
from flask import make_response
@app.route('/logout',methods=['POST'])
def logout():
    resp = make_response(jsonify({"status":"success","msg":"LogOut Success"}))
    resp.delete_cookie('uid')
    return resp
#=======================================================================================
@app.route('/updatePassword',methods=['POST'])
def updateUserPassword():
    updatePassword = request.get_json()
    oldPassword = updatePassword.get('pass')
    oldPass = oldPassword.get('oldPassword')
    newPass = oldPassword.get('updatePasswordOne')
    email = updatePassword.get('val')
    if isinstance(email, list):
        email = email[0]
    getPass = collection.find({'email':email})
    docs = []
    for doc in getPass:
        docs.append({
            "password":doc.get("password")
        })
    userPass = docs[0].get('password')
    if userPass == oldPass:
        updatedPass = collection.update_one({'email':email},{'$set':{'password':newPass}})
        if updatedPass.modified_count == 0:
            return jsonify({"msg":"Password already same not change"})
    else:
        return jsonify({"msg":"Can not match with old Password"})
    return jsonify({"msg":"Successfully update the password"})
#=======================================================================================
@app.route('/updateNumber',methods=['POST'])
def updateNumber():
    updateUserNumber = request.get_json()
    updateNumberVal = updateUserNumber.get('updateNumber')
    email = updateUserNumber.get('val')
    if not updateNumberVal:
        return jsonify({"msg":"Please fill the input"})
    if isinstance(email,list):
        email = email[0]
    
    updatedNumber = collection.update_one({'email':email},{'$set':{'number':updateNumberVal}})
    if updatedNumber.modified_count == 0:
        return jsonify({"msg":"Already number same"})
    print(type(updateUserNumber))
    return jsonify({"msg":"Successfully update Number"})
#=======================================================================================
@app.route('/updateLocation',methods=['POST'])
def updateLocation():
    updateUserLocation = request.get_json()
    if not updateUserLocation.get('updateLocation'):
        return jsonify({"msg":"Please fill the input"})
    print(updateUserLocation)
    updateLocationVal = updateUserLocation.get('updateLocation')
    email = updateUserLocation.get('val')
    if isinstance(email,list):
        email = email[0]
    updatedLocation = collection.update_one({'email':email},{'$set':{'location':updateLocationVal}})
    if updatedLocation.modified_count == 0:
        return jsonify({"msg":"Already same"})
    return jsonify({"msg":"Successfully update location"})
#=======================================================================================
@app.route('/reception',methods=['GET'])
def reception():
    return render_template('reception.html')
#=======================================================================================
@app.route('/recepDetail',methods=['POST'])
def recepDetail():
    body = request.get_json()
    print(body)
    field = ['patientName','gurdianName','gurdianEmail','gurdianNumber','dob'
            ,'hospital']
    for lab in field:
            if body.get(lab) == '':
                return jsonify({"msg":"Please fill the form"})
    recep = recepCollection.insert_one(body)
    if not recep:
        return jsonify({"msg":"Can not Submit Recep please try agian"})
    return jsonify({
        "msg":"Your Recep is Successfully Submmit we will be send the detail of donor via Email"
        })
#=======================================================================================
@app.route('/recepRequest',methods=['GET'])
def recepRequest():
    return render_template('recepRequest.html')

@app.route('/recepData',methods=['GET'])
def recepData():
    data = recepCollection.find()
    dataArray = []
    for doc in data:
        print(doc)
        dataArray.append({
            "_id": str(doc['_id']),
            "petiantName":doc['patientName'],
            "gurdianName":doc['gurdianName'],
            "gurdianEmail":doc['gurdianEmail'],
            "gurdianNumber":doc['gurdianNumber'],
            "dob":doc['dob'],
            "hospital":doc['hospital'],
            "bloodGroup":doc['bloodGroup'],
            "hospitalLocation":doc['hospitalLocation'],
            "gender":doc['gender'],
            "status":doc['status']
        })
    return dataArray
#=======================================================================================
@app.route('/userPush',methods=['POST'])
def userPush():
    body = request.get_json()
    donar_id = body.get("donar_id")
    request_id = body.get("request_id")
    print(donar_id,request_id)
    recepUser = recepCollection.find_one({'_id':ObjectId(request_id)})
    if not recepUser:
        return jsonify({"msg":"User request not Found"})
    
    recepUserData = {
        "_id": str(recepUser.get("_id")),
        "name":recepUser.get("patientName"),
        "gurdianName":recepUser.get("gurdianName"),
        "gurdianNumber":recepUser.get("gurdianNumber"),
        "hospitalLocation":recepUser.get("hospitalLocation"),
        "hospital":recepUser.get("hospital"),
        "gender":recepUser.get("gender"),
        "gurdianEmail":recepUser.get("gurdianEmail")
    }
    res = collection.update_one({'_id':ObjectId(donar_id)},{'$push':{"share_contact":recepUserData}})
    if res.modified_count == 0:
        return jsonify({"msg":"Target User Not Found"})
    return jsonify({"msg":"successfully send"})
#=======================================================================================
@app.route('/updatecount', methods=['POST'])
def updatecount():
    id = request.json['id']
    value = request.json['value']

    collection.update_one(
        {'_id': ObjectId(id)},
        {'$inc': {'count': value}}
    )

    return jsonify({"msg": "Count updated"})
#=======================================================================================
@app.route('/recedelete',methods=['POST'])
def recedelete():
    id = request.json['id']
    result = collection.update_one(
        {'_id': ObjectId(id)},
        {'$unset': {'share_contact': ""}}
    )
    return jsonify({"msg":"Your are successfully deleted recept user data"})
#=======================================================================================
@app.route('/recepupdatestatus', methods=['POST'])
def recepupdatestatus():
    try:
        data = request.get_json()
        print("Received Data:", data)

        id = data.get('id')
        recepCollection.update_one(
    {'_id': ObjectId(id)},
    {'$set': {'status': '✅'}}
)

        return jsonify({"msg": "successfully update"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"msg": str(e)}), 500
#=======================================================================================
@app.route('/totalUsers', methods=['GET'])
def totalUsers():
    total = collection.count_documents({})
    totalrequests = recepCollection.count_documents({})
    penddingrecep = recepCollection.count_documents({"status":'❌'})
    donerecep = recepCollection.count_documents({"status":'✅'})
    total_donated = collection.count_documents({"donate": "✅"})
    not_donated = collection.count_documents({"donate": "❌"})

    return jsonify({
        "total_users": total,
        "donated_user":total_donated,
        "total_request":totalrequests,
        "total_not_donated":not_donated,
        "pendding_request":penddingrecep,
        "done_recep":donerecep
    })
#=======================================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000, debug=True)