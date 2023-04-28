from flask import Flask, render_template,url_for,Response,request, flash, redirect, session, abort,jsonify
# from flask.globals import _request_ctx_stack
from flask_socketio import SocketIO, emit
from functools import wraps
import google.auth.transport.requests
from dotenv import load_dotenv
import requests
import pathlib
import os
import cv2
import datetime,time
import numpy as np
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import custom_modules.yogaposturedetection as ygp
import custom_modules.yogaposecorrection as ypc
import jsonpickle
import shutil
import threading
import json
import io, base64, imutils
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
# global user_header
# user_header = ""

#for the purpose of isolating updation of active_user_dictionary
sem = threading.Semaphore()

# global images_in_test_folder, images_out_test_folder, csvs_out_test_path, first
first = True
# IMAGES_ROOT = "static"
# images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
# images_out_test_folder = 'uploadedimage_output'
# csvs_out_test_path = 'static/image_csv/uploaded_image.csv'
# preprocessor = ygp.MoveNetPreprocessor(
#      images_in_folder=images_in_test_folder,
#      images_out_folder=images_out_test_folder,
#      csvs_out_path=csvs_out_test_path,
#             )



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

# global capture, out, selected_pose
# selected_pose="tree"
# correction=0
# capture=0
# camera = cv2.VideoCapture(0)


active_user_dictionary={}   # to store user specific variables

class Globalvars:
    def __init__(self):
        self.selected_pose="tree"
        self.correction=0
        self.camera = cv2.VideoCapture(0)
        self.previous_command=""
        self.previous_closest_label=""
        self.capture=0

    def select_pose(self,pose):
       self.selected_pose=pose
    
    def set_correction(self,b):
       if b:
          self.correction=1
       else:
          self.correction=0

# user_vars = Globalvars()


# global previous_command, previous_closest_label
# previous_command=""
# previous_closest_label=""

# def _session_save(session):  # pass flask.session from context
#     app.session_interface.save_session(app, session, Response())

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_formats
predicted_pose = ""





def gen_frames(preprocessor,user_id,user_header,uploaded_filename=""):  # generate frame by frame from camera
#    with app.app_context():
    image_loc = user_header+'/uploadedimage/chair'
    # global out, capture, correction
    # global previous_closest_label, previous_command
    user_vars=active_user_dictionary[user_id]
    user_vars.previous_closest_label=""
    user_vars.previous_command=""
    i=0
    print("---------------------------------------Inside gen_frames --------------------------------------")
    # print(session)
    # session['previous_command']=""
    # session["previous_closest_label"]=""
    # _session_save(session)
    print("-----------------------after adding----------------------------------")
    # print(session)

    # print("-=--------------------------------------"+str(correction))
    if user_vars.correction:
        detection_threshold = 0
    else:
        detection_threshold=0.15

    while True:

        success, frame = user_vars.camera.read() 
        if i%60:
            if not user_vars.correction:
             cv2.putText(
                 img = frame,
                 text = user_vars.previous_closest_label if not user_vars.previous_closest_label=="" else "No Pose Detected!!",
                 org = (200, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (125, 246, 55),
                 thickness = 3
                 )
            else: 
             cv2.putText(
                 img = frame,
                 text = user_vars.previous_command if not user_vars.previous_command=="" else "",
                 org = (100, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (0,0,0),
                 thickness = 2
                 )
            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
            i=i+1
            continue
        print(success)
        y_pred_lab=""
        command=""
        if success:
            
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
             print(y_pred_lab)
             if user_vars.correction:
              if user_vars.selected_pose=="tree" :
                command = ypc.tree_pose_correction(df_test)
              elif user_vars.selected_pose=="chair":
                 command = ypc.chair_pose_correction(df_test)
              elif user_vars.selected_pose=="warrior":
                 command=ypc.warrior_pose_correction(df_test)
              elif user_vars.selected_pose=="cobra":
                 command=ypc.cobra_pose_correction(df_test)
              elif user_vars.selected_pose=="dog":
                 command = ypc.dog_pose_correction(df_test)
              user_vars.previous_command=command
            #   session["previous_command"]=previous_command

            if not user_vars.correction:
             cv2.putText(
                 img = frame,
                 text = y_pred_lab+" "+command if not y_pred_lab=="" else "No Pose Detected!!",
                 org = (200, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (125, 246, 55),
                 thickness = 3
                 )
            else:
             cv2.putText(
                 img = frame,
                 text = command if not y_pred_lab=="" else "",
                 org = (100, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (0,0,0),
                 thickness = 2
                 )
            user_vars.previous_command=command
            # session["previous_command"]=previous_command

            user_vars.previous_closest_label=y_pred_lab if not y_pred_lab=="" else "No Pose Detected"
            predicted_pose=y_pred_lab
            # session["previous_closest_label"]=previous_closest_label
            if(user_vars.capture):
                capture=0
                now = datetime.datetime.now()
                #to save the image in the pc
                p = os.path.sep.join(['static/capture', "capture_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
      
            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
            i=i+1
        else:
            break 

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
    sem.acquire()
    if not session['user_id'] in active_user_dictionary.keys():
        user_vars=Globalvars()
        active_user_dictionary[session['user_id']]=user_vars
        # user_vars.preprocessor=session['preprocessor']
        # user_vars.user_id=session['user_id']
    sem.release()
    session['switch']=1
    print("----------------------Before logging in----------------------")
    print(active_user_dictionary)
    return render_template('index.html',name=session["name"].split()[0])

@app.route("/logout")
def logout():
    user_header='static/'+session['user_id']
    print('-----------------------------------------'+user_header)
    if os.path.exists(user_header):
        shutil.rmtree(user_header, ignore_errors=True)
    if active_user_dictionary[session['user_id']]:
        del active_user_dictionary[session['user_id']]
    print("--------Before Logging out ------------------")
    print(active_user_dictionary)
    session.clear()
    return redirect('/')

@app.route('/getvariables')
@login_required
def getvariables(methods=['GET']):
    # global previous_command, previous_closest_label
    user_vars=active_user_dictionary[session['user_id']]
    print("----------------------inside getvariables -------------------------")
    print(session)
    if session['switch'] and not (session['previous_speech_command']==user_vars.previous_command and session['count']<4):
     text_to_speech(user_vars.previous_command,'Male')
     session['previous_speech_command']=user_vars.previous_command
     session['count']=0
    else:
       session['count']=session['count']+1
    variables={
        "previous_command" : user_vars.previous_command,
        "previous_closest_label" : user_vars.previous_closest_label
     }
    return jsonify(variables)



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

@app.route('/video_feed/')
@login_required
def video_feed():
#    def cb1():
#        session['previous_command']=""
#        session['previous_closest_label']=""
    
#    def cb2(s):
#        session['previous_command']=s

#    def cb3(s):
#        session['previous_closest_label']=s  
  

   if(session['switch']):
     return Response(gen_frames(preprocessor=jsonpickle.decode(session['preprocessor']),user_id=session['user_id'],user_header=session['user_header']), mimetype='multipart/x-mixed-replace; boundary=frame')
   else: 
        return "No response"


@app.route('/capturepose/')
@login_required
def capture_pose():
    sem.acquire()
    if not session['user_id'] in active_user_dictionary.keys():
        user_vars=Globalvars()
        active_user_dictionary[session['user_id']]=user_vars
    sem.release()
    return render_template('Mainpages/capturepose.html',pose=predicted_pose,name=session["name"].split()[0])

@app.route('/chronic/')
@login_required
def chronic():
    return render_template('Mainpages/chronic.html',name=session["name"].split()[0])

@app.route('/benefits/')
@login_required
def benefits():
    return render_template('Mainpages/benefits.html',name=session["name"].split()[0])






# @app.route('/detection/', methods = ['POST','GET'])
# def detection():

#     full_filename = ""
#     y_pred_lab=""
#     if request.method == 'POST':
#         for file in os.listdir('static/uploadedimage/chair/'):
#           os.remove('static/uploadedimage/chair/' + file)
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file'] 
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             #processing
#             # csvs_out_test_path = 'uploaded_image.csv'
#             IMAGES_ROOT = "static"
#             images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
#             images_out_test_folder = 'uploadedimage_output'
#             csvs_out_test_path = 'static/image_csv/uploaded_image.csv'
#             preprocessor = ygp.MoveNetPreprocessor(
#             images_in_folder=images_in_test_folder,
#             images_out_folder=images_out_test_folder,
#              csvs_out_path=csvs_out_test_path,
#             )
#             preprocessor.process(per_pose_class_limit=None,detection_threshold=0.1)
#             X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
#             y_pred = ygp.model.predict(X_test)
#             y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
#             y_pred_lab = y_pred_label[0]
#             print(full_filename)
#             file_details[0]["full_filename"] = full_filename
#             file_details[0]["idname"] = "detectbutton"
            

#     return render_template('Mainpages/detection.html', image_uploaded = file_details, pose_prediction=y_pred_lab)


@app.route('/detection/', methods = ['POST','GET'])
@login_required
def detection():
#     full_filename = ""
#     y_pred_lab=""
#     print("0")
#     preprocessorJSON = session['preprocessor']
#     preprocessor = jsonpickle.decode(preprocessorJSON)
#     user_header=session['user_header']
#     image_loc = user_header+'/uploadedimage/chair'
#     if request.method == 'POST':
#         print("1")
#         for file in os.listdir(user_header+'/uploaded_video'):
#           os.remove(user_header+'/uploaded_video/' + file)
#         for file in os.listdir(user_header+'/processed_videos'):
#           os.remove(user_header+'/processed_videos/' + file)
#         print("2")
#         if 'file' not in request.files:
#             print("No file part")
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file'] 
#         print("3")
#         # print('file-----'+type(file))
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         print("4")
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             print("----------" + file.content_type)
#             #processing
#             # csvs_out_test_path = 'uploaded_image.csv'
#             codec = cv2.VideoWriter_fourcc(*'x264')
#             output_file = user_header+'/processed_videos/processed_video.mp4'
#             cap = cv2.VideoCapture(full_filename)
#             width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH ))
#             height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))
#             fps = cap.get(cv2.CAP_PROP_FPS)
#             output_size = (width, height) 
#             out = cv2.VideoWriter(output_file, codec, fps, output_size)
#             i=0
#             previous_closest_label=""
#             while cap.isOpened():
#                 # Read a frame from the video source
#               ret, frame = cap.read()
#               if i%30: 
#                 cv2.putText(
#                  img = frame,
#                  text = previous_closest_label if not previous_closest_label=="" else "No Pose Detected!!",
#                  org = (200, 200),
#                  fontFace = cv2.FONT_HERSHEY_DUPLEX,
#                  fontScale = 1.0,
#                  color = (125, 246, 55),
#                  thickness = 3
#                  )
#                 i=i+1
#                 out.write(frame)
#                 continue 
#               else:
#                 y_pred_lab=""
#                 if not ret:
#                     break
#                   # If there are no more frames, break out of the loop
#                 for file in os.listdir(user_header+'/uploadedimage/chair'):
#                     os.remove(user_header+'/uploadedimage/chair/' + file)
            
#                 cv2.imwrite(os.path.join(image_loc, 'videoframe.jpg'), frame)
#                 csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
#                 for file in os.listdir(user_header+'/image_csv'):
#                     os.remove(user_header+'/image_csv/' + file)
#                 preprocessor.process(per_pose_class_limit=None)
#                 if len(os.listdir(user_header+'/image_csv'))!=0:
#                  X_test, y_test, _, df_test = ygp.load_pose_landmarks(csvs_out_test_path)
#                  y_pred = ygp.model.predict(X_test)
#                  y_pred_label = [ygp.class_names[i] for i in np.argmax(y_pred, axis=1)]
#                  y_pred_lab = y_pred_label[0]
#                  print(full_filename)

                
#                 cv2.putText(
#                  img = frame,
#                  text = y_pred_lab if not y_pred_lab=="" else "No Pose Detected!!",
#                  org = (200, 200),
#                  fontFace = cv2.FONT_HERSHEY_DUPLEX,
#                  fontScale = 1.0,
#                  color = (125, 246, 55),
#                  thickness = 3
#                 )
#                 previous_closest_label=y_pred_lab
#                 predicted_pose=y_pred_lab
#                 print("----------------------" + full_filename)        
                 
#     # Write the frame to the output video
#                 out.write(frame)
                
#     # Display the frame (optional)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     break
#                 i=i+1
# # Release the VideoCapture and VideoWriter objects
#             print("5")
#             cap.release()
#             out.release()
#             cv2.destroyAllWindows()
#             file_details[0]["full_filename"] = "processed_video.mp4"
#             file_details[0]["idname"] = "detectbutton"   
#             file_details[0]['user_header']=session['user_header']
#             print("6")

#             # return render_template('Mainpages/detection.html', image_uploaded = file_details)   
#             return jsonify(file_details)
            
#     else:
# #      return render_template('Mainpages/detection.html', image_uploaded = file_details, name=session['name'].split()[0])    
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
    # global camera,correction
    user_vars=active_user_dictionary[session['user_id']]
    user_vars.set_correction(False)
    if request.method == 'POST':

        if request.form.get('click') == 'Capture':
            # global capture
            user_vars.capture=1
        elif  request.form.get('stop') == 'Stop/Start':
            if(session['switch']==1):
                session['switch']=0
                user_vars.camera.release()
                cv2.destroyAllWindows()
            else:
                user_vars.camera = cv2.VideoCapture(0)
                session['switch']=1       
    elif request.method=='GET':
    
        return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])
    return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])


@app.route('/liveyogacorrection/',methods=['POST','GET'])
def yogacorrectionform():
    # global camera,correction,selected_pose
    sem.acquire()
    if not session['user_id'] in active_user_dictionary.keys():
        user_vars=Globalvars()
        active_user_dictionary[session['user_id']]=user_vars
    sem.release()
    session['previous_speech_command']="Welcome to yoga correction"
    session['count']=0
    user_vars=active_user_dictionary[session['user_id']]
    user_vars.set_correction(True)
    if request.method == 'POST':
        if request.form.get('yogaposes_dropdown'):
            selected_pose=request.form.get('yogaposes_dropdown')
            user_vars.select_pose(selected_pose)
        elif request.form.get('click') == 'Capture':
            user_vars.capture=1
        elif  request.form.get('stop') == 'Stop/Start':
            if(session['switch']==1):
                session['switch']=0
                user_vars.camera.release()
                cv2.destroyAllWindows()
            else:
                user_vars.camera = cv2.VideoCapture(0)
                session['switch']=1       
    elif request.method=='GET':
        return render_template('Mainpages/liveyogacorrection.html',selected=user_vars.selected_pose.capitalize(),name=session["name"].split()[0])
    return render_template('Mainpages/liveyogacorrection.html',selected=user_vars.selected_pose.capitalize(),name=session["name"].split()[0])

if __name__ == '__main__':
    app.run(debug=True)
