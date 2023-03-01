from flask import Flask, render_template,url_for,Response,request, flash, redirect, session, abort,jsonify
from functools import wraps
import google.auth.transport.requests

import requests
import pathlib
import os
import cv2
import datetime,time
import numpy as np
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import custom_modules.yogaposturedetection as ygp



allowed_formats = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
y_pred_label=""
app = Flask(__name__)
#routes
from user_auth import routes
import custom_modules.google_authentication as google_authentication
import custom_modules.diseaseprediction as diseasepredictor
app.secret_key = "JonOnFire"

def login_required(function): 
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect(url_for('start_page')) #Authorization needed
        else: 
            return function()
        
    return wrapper

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploadedimage/chair')

file_details = [
    {
        "full_filename" : "",
        "idname" : "",
        
    }
]

global capture, switch, out 
capture=0
switch=1
camera = cv2.VideoCapture('posefind.mp4')
frame_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
video = cv2.VideoWriter('processed_video.avi', cv2.VideoWriter_fourcc(*'X264'),
                        25, (frame_width, frame_height))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_formats

def gen_frames():  # generate frame by frame from camera
    global out, capture
    image_loc = 'static/uploadedimage/chair'
    previous_closest_label=""
    i=0
    # print("prediction beforehand: "+y_pred_lab)
    while True:
        success, frame = camera.read() 
        if i%60:
            cv2.putText(
                 img = frame,
                 text = previous_closest_label if not previous_closest_label=="" else "No Pose Detected!!",
                 org = (200, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (125, 246, 55),
                 thickness = 3
                 )
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
            i=i+1
            continue
        print(success)
        y_pred_lab=""
        if success:
            for file in os.listdir('static/uploadedimage/chair'):
             os.remove('static/uploadedimage/chair/' + file)
            
            cv2.imwrite(os.path.join(image_loc, 'videoframe.jpg'), frame)
            # csvs_out_test_path = 'uploaded_image.csv'
            for file in os.listdir('static/image_csv'):
             os.remove('static/image_csv/' + file)
            IMAGES_ROOT = "static"
            images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
            images_out_test_folder = 'uploadedimage_output'
            csvs_out_test_path = 'static/image_csv/uploaded_image.csv'
            preprocessor = ygp.MoveNetPreprocessor(
            images_in_folder=images_in_test_folder,
            images_out_folder=images_out_test_folder,
             csvs_out_path=csvs_out_test_path,
            )
            preprocessor.process(per_pose_class_limit=None)
            if len(os.listdir('static/image_csv'))!=0:
             X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
             y_pred = ygp.model.predict(X_test)
             y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
             y_pred_lab = y_pred_label[0]
             print(y_pred_lab)
           
            cv2.putText(
                 img = frame,
                 text = y_pred_lab if not y_pred_lab=="" else "No Pose Detected!!",
                 org = (200, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (125, 246, 55),
                 thickness = 3
                 )
            previous_closest_label=y_pred_lab
            # cv2.flip(frame,1)
            # video.write(frame)
            if(capture):
                capture=0
                now = datetime.datetime.now()
                #to save the image in the pc
                p = os.path.sep.join(['static/capture', "capture_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
      
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
            i=i+1
        else:
            break



@app.route('/home/')
@login_required
def hello():
    # print(session["state"])
    return render_template('index.html',name=session["name"])

@app.route("/")
def start_page():
    # return "Hello there<a href='/login'><button>Login</button></a>"
    return render_template('User/signup.html')
    
@app.route('/register/')
def register():
    pass

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

@app.route('/video_feed/')
@login_required
def video_feed():
    if(switch):
     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else: 
        return "No response"


@app.route('/capturepose/')
@login_required
def capture_pose():
    return render_template('Mainpages/capturepose.html')

@app.route('/chronic/')
@login_required
def chronic():
    return render_template('Mainpages/chronic.html')

@app.route('/benefits/')
@login_required
def benefits():
    return render_template('Mainpages/benefits.html')

@app.route('/preventionchronic/')
@login_required
def preventionchronic():
    return render_template('Mainpages/preventionchronic.html')

@app.route('/detection/', methods = ['POST','GET'])
def detection():
    full_filename = ""
    y_pred_lab=""
    if request.method == 'POST':
        for file in os.listdir('static/uploadedimage/chair/'):
          os.remove('static/uploadedimage/chair/' + file)
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
            IMAGES_ROOT = "static"
            images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
            images_out_test_folder = 'uploadedimage_output'
            csvs_out_test_path = 'static/image_csv/uploaded_image.csv'
            preprocessor = ygp.MoveNetPreprocessor(
            images_in_folder=images_in_test_folder,
            images_out_folder=images_out_test_folder,
             csvs_out_path=csvs_out_test_path,
            )
            preprocessor.process(per_pose_class_limit=None)
            X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
            y_pred = ygp.model.predict(X_test)
            y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
            y_pred_lab = y_pred_label[0]
            print(full_filename)
            file_details[0]["full_filename"] = full_filename
            file_details[0]["idname"] = "detectbutton"
            

    return render_template('Mainpages/detection.html', image_uploaded = file_details, pose_prediction=y_pred_lab)

@app.route('/detection/uploadvideo',methods=['POST'])
def upload_video():
	if 'file' not in request.files:
		flash('No file part')
		return redirect(request.url)
	file = request.files['file']
	if file.filename == '':
		flash('No image selected for uploading')
		return redirect(request.url)
	else:
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		#print('upload_video filename: ' + filename)
		flash('Video successfully uploaded and displayed below')
		return render_template('detection.html', filename=filename)



@app.route('/requests/',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('stop') == 'Stop/Start':
            if(switch==1):
                switch=0
                camera.release()
                cv2.destroyAllWindows()
            else:
                camera = cv2.VideoCapture(0)
                switch=1       
    elif request.method=='GET':
        return render_template('Mainpages/capturepose.html')
    return render_template('Mainpages/capturepose.html')

if __name__ == '__main__':
    app.run(debug=True)
