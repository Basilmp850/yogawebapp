from flask import Flask, render_template,url_for,request, flash, redirect, session, abort,jsonify
# from flask.globals import _request_ctx_stack
from flask_socketio import SocketIO, emit
from functools import wraps
import google.auth.transport.requests
from dotenv import load_dotenv
# import requests
import pathlib
import os
import cv2
# import datetime,time
import numpy as np
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import custom_modules.yogaposturedetection as ygp
import custom_modules.yogaposecorrection as ypc
import jsonpickle
import shutil
# import threading
import json
import io, base64
from PIL import Image
import eventlet
from passlib.hash import pbkdf2_sha256
import uuid
from random import randint
from json import JSONEncoder
from flask_mail import Mail,Message
from pip._vendor import cachecontrol
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import requests
import pdfkit

load_dotenv()
file_details = [
{
        "full_filename" : "",
        "idname" : "",
        
    }
]

mongoclient = MongoClient(os.getenv("MONGO_CLIENT"))
db=mongoclient.User_authentication

#for the purpose of isolating updation of active_user_dictionary

first = True



allowed_formats = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','mp4'])
y_pred_label=""
app = Flask(__name__)
socketio = SocketIO(app,transports=['websocket','polling'], async_mode='eventlet' ,socket=True)

app.config["DEBUG"]=True
app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465     
app.config["MAIL_USERNAME"] = 'jonathannebu10@gmail.com'  
# app.config['MAIL_PASSWORD'] = 'dbyczdyjhldjtdzl'  
app.config['MAIL_PASSWORD'] = os.getenv("APP_PASS")
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True  
#routes


# from user_auth import models

import custom_modules.diseaseprediction as diseasepredictor
app.register_blueprint(diseasepredictor.disease_prediction)

import custom_modules.yogafrombenefits as yogafrombenefits
app.register_blueprint(yogafrombenefits.yoga_from_benefits)

# from user_auth import routes
# app.register_blueprint(routes.user_auth_routes)


# import user_auth.models as user_authorization_model


# import custom_modules.google_authentication as google_authentication
# app.register_blueprint(google_authentication.google_authentication_routes)

app.secret_key = os.getenv("SECRET_KEY")







class EmployeeEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

# global preprocessor
mail = Mail(app)   


class User:
    def start_session(self,user,verification_status=False):
        # global preprocessor
        session['logged_in']=True
        session['user']=user
        session['user_id']=user['_id']
        session['name']=user['name']
        session['verified']=True
                
        user_header='static/'+session['user_id']
        if not os.path.exists(user_header):
           os.makedirs(user_header+'/uploadedimage/chair')
           os.makedirs(user_header+'/image_csv')
           os.makedirs(user_header+'/uploaded_video')
           os.makedirs(user_header+'/processed_videos')
           os.makedirs(user_header+'/rendered_files')
        session['user_header']=user_header
        app.config['UPLOAD_FOLDER'] = os.path.join(user_header, 'uploaded_video')
        images_in_test_folder = os.path.join(user_header, 'uploadedimage')
        images_out_test_folder = 'uploadedimage_output'
        csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
        preprocessor = ygp.MoveNetPreprocessor(
        images_in_folder=images_in_test_folder,
        images_out_folder=images_out_test_folder,
        csvs_out_path=csvs_out_test_path
            )
        print("-----------------Before Loading-------------------")
        print(preprocessor)
        preprocessorJSON = jsonpickle.encode(preprocessor, unpicklable=True)
        print("----------------------preprocessorJSON")
        print(preprocessorJSON)
        # preprocessorJSONData = json.dumps(preprocessorJSON, indent=4)
        # print("----------------------preprocessorJSONDATA")
        # print(preprocessorJSONData)
        # preprocessor_decodedJSON = jsonpickle.decode(preprocessorJSONData)
        # print("------------------------------preprocessor_decodedJSON")
        # print(preprocessor_decodedJSON)

        # preprocessor_loadedJSON = jsonpickle.decode(preprocessorJSON)
        # print("---------------- After loading-----------------------")
        # print(preprocessor_loadedJSON)
        print("preprocessor MARKING --------------------------")
        session['preprocessor']=preprocessorJSON
        if not verification_status:
         db.User.update_one({"email":user['email']},{"$set":{"verified": True}})
         return jsonify(user),200
        #  return redirect(url_for('hello'))
        return jsonify(user),200

    def signup(self):
        user = {
            "_id":uuid.uuid4().hex,
            "name": request.form.get("name"),
            "email":request.form.get("email"),
            "password":request.form.get("psw"),
            "password-repeat":request.form.get("psw-repeat"),
            "verified": False
        }
        if user['password']!=user['password-repeat']:
           return jsonify({"error":"Passwords don't match"}),400
        user['password'] = user['password-repeat'] = pbkdf2_sha256.encrypt(user['password'])
        existing_user = db.User.find_one({"email": user['email']})
        if existing_user:
            if not existing_user['verified']:
              db.User.delete_one(existing_user)
              return self.verify(user)
            else:
             return jsonify({"error":"Email address already in use"}), 400
        if db.User.insert_one(user): 
            return self.verify(user)
        return jsonify({"error":"Signup failed!!"}), 400
    
    def verify(self,user):
        user["random-otp"] = randint(100000,999999)
        db.User.update_one({"email":user['email']},{"$set":{"random-otp": user["random-otp"]}})
        print(user)
        msg = Message(str(user['random-otp']),sender = 'jonathannebu10@gmail.com', recipients = [user['email']])  
        # msg.body = "Your OTP is: "+str(user["random-otp"])  
        msg.html = render_template('Basic_layouts/verification_mail.html',otp=user['random-otp'])
        try: 
         mail.send(msg)  
        except: 
         db.User.delete_one(user)
         return jsonify({"error":"Invalid email address"}), 400

        # render_template(url_for('verification'),email=user['email'])
        return jsonify(user),200

    def validate(self):
        user_id=request.form['user-id']
        print("user--------------"+user_id)
        user_otp = request.form['otp']  
        print(int(user_otp))
        
        user = db.User.find_one({"_id": user_id})
        print(user)
        if user["random-otp"]==int(user_otp):  
         return self.start_session(user)
        else:
         return jsonify({"error":"Invalid OTP"}), 400
    
    def login(self):
        user = db.User.find_one({"email": request.form.get('email')})
        flag = 0
        if user and pbkdf2_sha256.verify(request.form.get('psw'),user['password']):
            if user['verified']:
             return self.start_session(user,verification_status=True)
            else:
               flag = 1
        if flag:
           return jsonify({"error":"Unverified email"}),401
        return jsonify({"error":"Invalid Username/Password"}),401
       
    def signout(self):
        session.clear()
        return redirect('/')
    

@app.route('/user/signup', methods = ['GET','POST'])
def signup_m():
    return User().signup()


@app.route('/user/login', methods = ['GET','POST'])
def login_m():
    return User().login()


@app.route('/user/verify/<user_id>',methods=['GET','POST'])
def verification(user_id):
    return render_template('User/verification.html',user_id=user_id)

@app.route('/user/validate',methods=['GET','POST'])
def otp_validate():
    return User().validate()


os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1" #possibly requires change in future

client_secrets_file=os.path.join(pathlib.Path("custom_modules/"), "client_secret1.json")
print(client_secrets_file)
flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email","openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

# global preprocessor
# preprocessor = None

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"]=state
    print(authorization_url)
    return redirect(authorization_url)
    # print(session)
    # print(session["state"]+"- initial state")
    # print("[AUTHORIZATION URL]"+authorization_url)
    # print(state)

    #  session['google_id'] = "Test"
    # return redirect("/protected_area")

@app.route('/callback')
def callback():

    # print(session["state"])
    # print(request.args["state"]+" - request state")
    flow.fetch_token(authorization_response=request.url)
    #for security purposes. Fix this later.
    # if not (session["state"]==request.args["state"]):
    #   abort(500) # state does not match

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=os.getenv("CLIENT_ID")
    )
    session['google_id']=id_info.get("sub")
    session['email']=id_info.get("email")
    session["name"]=id_info.get("name")

    user=db.User.find_one({"email": session['email']})

    if user and "password" in user:  
        email=session['email']
        session.clear()
        return render_template('User/signup.html',email=email)
    if not user:
     user = {
            "_id":uuid.uuid4().hex,
            "name": session['name'],
            "email": session['email'],
            "verified": True
        }
    
     db.User.insert_one(user)
    
    session['user_id']=user['_id']
    user_header='static/'+session['user_id']
    if not os.path.exists(user_header):
           os.makedirs(user_header+'/uploadedimage/chair')
           os.makedirs(user_header+'/image_csv')
           os.makedirs(user_header+'/uploaded_video')
           os.makedirs(user_header+'/processed_videos')
           os.makedirs(user_header+'/rendered_files')
    # global preprocessor
    session['user_header']=user_header
    from app import app
    app.config['UPLOAD_FOLDER'] = os.path.join(user_header, 'uploaded_video')
    images_in_test_folder = os.path.join(user_header, 'uploadedimage')
    images_out_test_folder = 'uploadedimage_output'
    csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
    preprocessor = ygp.MoveNetPreprocessor(
    images_in_folder=images_in_test_folder,
    images_out_folder=images_out_test_folder,
    csvs_out_path=csvs_out_test_path
            )
    preprocessorJSON = jsonpickle.encode(preprocessor, unpicklable=True)
    session['preprocessor']=preprocessorJSON
    # print(session)
    return redirect("/home")


# from user_auth.models import User

def login_required(function): 
    @wraps(function)
    def wrapper(*args, **kwargs):
        if ("google_id" not in session) and ('logged_in' not in session):
            return redirect(url_for('start_page')) #Authorization needed
        else: 
            return function()
        
    return wrapper

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_formats
predicted_pose = ""



@app.route('/get_session_data')
def get_session_data():
    session_data = dict(session)
    return jsonify(session_data)


# @app.route('/detection_ajax',methods=['POST'])
# def detection_ajax():
#   if request.method == 'POST':
#     data = request.json
#     print(data)
#     session = json.loads(data.session_data)
#     user_header = session['user_header']
#     image_loc = user_header+'/uploadedimage/chair'
#     preprocessor=jsonpickle.decode(session['preprocessor'])
#     detection_threshold=0.15
#     y_pred_lab=""
#     # decode and convert into image
#     b = io.BytesIO(base64.b64decode(data.image_data))
#     try:
#      pimg = Image.open(b)
#      frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

#     ## converting RGB to BGR, as opencv standards


#     # Process the image frame

#     # print(session)

    
#      for file in os.listdir(user_header+'/uploadedimage/chair'):
#        os.remove(user_header+'/uploadedimage/chair/' + file)
            
#      cv2.imwrite(os.path.join(image_loc, 'videoframe.jpg'), frame)
#      csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
#      for file in os.listdir(user_header+'/image_csv'):
#         os.remove(user_header+'/image_csv/' + file)

#      preprocessor.process(per_pose_class_limit=None,detection_threshold=detection_threshold)
#      if len(os.listdir(user_header+'/image_csv'))!=0:
#              X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
#              print('LEFT HIP X')
#              print(df_test['LEFT_HIP_x'][0])
#              y_pred = ygp.model.predict(X_test)
#              y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
#              y_pred_lab = y_pred_label[0]
#     except: 
#      print("Not able to open image")
#     returndata = {'prediction': y_pred_lab}
#     return jsonify(returndata)

@socketio.on('detection')
def socket_detection(data):
    # sbuf = StringIO()
    stringData=""
    # sbuf.write(data_image)
    session = json.loads(data['session_data'])
    user_header = session['user_header']
    image_loc = user_header+'/uploadedimage/chair'
    preprocessor=jsonpickle.decode(session['preprocessor'])
    detection_threshold=0.15
    y_pred_lab=""
    try:
     nparr = np.frombuffer(data['image_data'], np.uint8)
     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # decode and convert into image
    # b = io.BytesIO(base64.b64decode(data['image_data']))
    #  pimg = Image.open(b)
    #  frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

    ## converting RGB to BGR, as opencv standards


    # Process the image frame

    # print(session)

    
     for file in os.listdir(user_header+'/uploadedimage/chair'):
       os.remove(user_header+'/uploadedimage/chair/' + file)
            
     cv2.imwrite(os.path.join(image_loc, 'videoframe.jpg'), frame)
     csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
     for file in os.listdir(user_header+'/image_csv'):
        os.remove(user_header+'/image_csv/' + file)

     preprocessor.process(per_pose_class_limit=None,detection_threshold=detection_threshold)
     if len(os.listdir(user_header+'/image_csv'))!=0:
             X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
             print('LEFT HIP X')
             print(df_test['LEFT_HIP_x'][0])
             y_pred = ygp.model.predict(X_test)
             y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
             y_pred_lab = y_pred_label[0]
    except: 
     print("Not able to open image")
    emit('message',y_pred_lab if not y_pred_lab=="" else "No Pose detected!!")
    # # frame = imutils.resize(frame, width=700)
    # frame = cv2.flip(frame, 1)
    # imgencode = cv2.imencode('.jpeg', frame)[1]

    # base64 encode
    # stringData = base64.b64encode(imgencode).decode('utf-8')
    # b64_src = 'data:image/jpeg;base64,' 
    # # data:image/jpeg;base64,/9j/4AAQSkZJRgA
    # stringData = b64_src + stringData
    # print(stringData+'\n')
    # # emit the frame back
    # emit('response_back', stringData)

@socketio.on('correction')
def socket_correction(data):
    # sbuf = StringIO()
    stringData=""
    # sbuf.write(data_image)
    command=""
    session = json.loads(data['session_data'])
    user_header = session['user_header']
    image_loc = user_header+'/uploadedimage/chair'
    preprocessor=jsonpickle.decode(session['preprocessor'])
    selected_pose = data['selected_pose']
    detection_threshold=0
    y_pred_lab=""
    # decode and convert into image
    b = io.BytesIO(base64.b64decode(data['image_data']))
    try:
     pimg = Image.open(b)

    ## converting RGB to BGR, as opencv standards
     frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

    # Process the image frame

    # print(session)

    
     for file in os.listdir(user_header+'/uploadedimage/chair'):
       os.remove(user_header+'/uploadedimage/chair/' + file)
            
     cv2.imwrite(os.path.join(image_loc, 'videoframe.jpg'), frame)
     csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
     for file in os.listdir(user_header+'/image_csv'):
        os.remove(user_header+'/image_csv/' + file)

     preprocessor.process(per_pose_class_limit=None,detection_threshold=detection_threshold)
     if len(os.listdir(user_header+'/image_csv'))!=0:
             X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
             print('LEFT HIP X')
             print(df_test['LEFT_HIP_x'][0])
             y_pred = ygp.model.predict(X_test)
             y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
             y_pred_lab = y_pred_label[0]

             if selected_pose=="tree" :
                command = ypc.tree_pose_correction(df_test)
             elif selected_pose=="chair":
                 command = ypc.chair_pose_correction(df_test)
             elif selected_pose=="warrior":
                 command=ypc.warrior_pose_correction(df_test)
             elif selected_pose=="cobra":
                 command=ypc.cobra_pose_correction(df_test)
             elif selected_pose=="dog":
                 command = ypc.dog_pose_correction(df_test)
    except: 
     print("Not able to open image!!")
    emit('message',command if not command=="" else "Get ready!!")


@app.route('/home/')
@login_required
def hello():
    return render_template('index.html',name=session["name"].split()[0])

@app.route("/logout")
def logout():
    # print(session)
    user_header=session['user_header']
    print('-----------------------------------------'+user_header)
    if os.path.exists(user_header):
        shutil.rmtree(user_header, ignore_errors=True)
    # if active_user_dictionary[session['user_id']]:
    #     del active_user_dictionary[session['user_id']]
    print("--------Before Logging out ------------------")
    # print(active_user_dictionary)
    session.clear()
    return redirect('/')


@app.route("/")
def start_page():
    if ("google_id" in session) or ('logged_in' in session): 
       return redirect(url_for('hello'))
    return render_template('User/signup.html')


@app.route("/protected_area/")
@login_required
def protected_area():
    # return f"Hello {session['name']}! <br/><a href='/logout'><button>Logout</button></a>"
    return render_template('index.html',name = session["name"])

@app.route('/aboutus/')
@login_required
def aboutus():
    return render_template('Basic_layouts/aboutus.html')

@app.route('/contactus/')
@login_required
def contactus():
    return render_template('Basic_layouts/contactus.html')

@app.route('/capturepose/')
@login_required
def capture_pose():
    return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])

@app.route('/chronic/')
@login_required
def chronic():
    return render_template('Mainpages/chronic.html',name=session["name"].split()[0])

@app.route('/benefits/')
@login_required
def benefits():
    return render_template('Mainpages/benefits.html',name=session["name"].split()[0])




@app.route('/detection/', methods = ['POST','GET'])
@login_required
def detection():   
    app.config['UPLOAD_FOLDER'] = os.path.join(session['user_header'], 'uploadedimage/chair')

    preprocessorJSON = session['preprocessor']
    preprocessor = jsonpickle.decode(preprocessorJSON)
    user_header=session['user_header']
    image_loc = user_header+'/uploadedimage/chair'
    full_filename = ""
    y_pred_lab=""
    if request.method == 'POST':
        csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
        for file in os.listdir(user_header+'/uploadedimage/chair/'):
          os.remove(user_header+'/uploadedimage/chair/' + file)
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file'] 
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #processing
            # csvs_out_test_path = 'uploaded_image.csv'
            preprocessor.process(per_pose_class_limit=None,detection_threshold=0.15)
            if len(os.listdir(user_header+'/image_csv'))!=0:
             X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
             y_pred = ygp.model.predict(X_test)
             y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
             y_pred_lab = y_pred_label[0]
             print(full_filename)
             file_details[0]["full_filename"] = full_filename
             file_details[0]["idname"] = "detectbutton"
             file_details[0]['user_header']=session['user_header']
             file_details[0]['pose_prediction']=y_pred_lab
        return jsonify(file_details)

    return render_template('Mainpages/detection.html', image_uploaded = file_details, pose_prediction=y_pred_lab, name=session['name'].split()[0])



@app.route('/requests/',methods=['POST','GET'])
def tasks():
    return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])


@app.route('/liveyogacorrection/',methods=['POST','GET'])
def yogacorrectionform():
    return render_template('Mainpages/liveyogacorrection.html',name=session["name"].split()[0])

if __name__ == '__main__':
    # eventlet.monkey_patch()
    # app.run(debug=True)
    # eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    socketio.run(app,host='0.0.0.0',port=5000,debug=True) 
