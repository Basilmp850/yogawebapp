from flask import Flask, render_template,url_for,Response,request, flash, redirect, session, abort,jsonify
# from flask.globals import _request_ctx_stack
from flask_socketio import SocketIO, emit
from functools import wraps
import google.auth.transport.requests
from dotenv import load_dotenv
# import requests
# import pathlib
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
socketio = SocketIO(app)

#routes

import custom_modules.google_authentication as google_authentication
import custom_modules.diseaseprediction as diseasepredictor
import custom_modules.yogafrombenefits as yogafrombenefits
from custom_modules.audiocommands import text_to_speech

app.secret_key = os.getenv("SECRET_KEY")
from user_auth import routes
import user_auth.models as user_authorization_model
from user_auth.models import User

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
    # decode and convert into image
    b = io.BytesIO(base64.b64decode(data['image_data']))
    try:
     pimg = Image.open(b)
     frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

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
    app.run(debug=True)
