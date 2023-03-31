from flask import Flask, render_template,url_for,Response,request, flash, redirect, session, abort,jsonify
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



# global images_in_test_folder, images_out_test_folder, csvs_out_test_path, first
first = True
IMAGES_ROOT = "static"
images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
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
#routes

import custom_modules.google_authentication as google_authentication
import custom_modules.diseaseprediction as diseasepredictor
import custom_modules.yogafrombenefits as yogafrombenefits
app.secret_key = "JonOnFire"
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

# app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploaded_video')
# app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploadedimage/chair')


global capture, switch, out, selected_pose
selected_pose="tree"
correction=0
capture=0
switch=1
camera = cv2.VideoCapture(0)


global previous_command, previous_closest_label
previous_command=""
previous_closest_label=""
# frame_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
# frame_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
# video = cv2.VideoWriter('processed_video.avi', cv2.VideoWriter_fourcc(*'X264'),
                        # 25, (frame_width, frame_height))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_formats
predicted_pose = ""

def gen_frames(preprocessor,user_header,uploaded_filename=""):  # generate frame by frame from camera
    # user_header=session['user_header']
    image_loc = user_header+'/uploadedimage/chair'
    global out, capture, correction
    global previous_closest_label, previous_command
    # print(session['preprocessor'])
    # preprocessor=jsonpickle.decode(preprocessorJSON)
    previous_closest_label=""
    i=0
    previous_command=""
    print("-=--------------------------------------"+str(correction))
    if correction:
        detection_threshold = 0
    else:
        detection_threshold=0.15
    # print("prediction beforehand: "+y_pred_lab)
    while True:

        success, frame = camera.read() 
        if i%60:
            if not correction:
             cv2.putText(
                 img = frame,
                 text = previous_closest_label if not previous_closest_label=="" else "No Pose Detected!!",
                 org = (200, 200),
                 fontFace = cv2.FONT_HERSHEY_DUPLEX,
                 fontScale = 1.0,
                 color = (125, 246, 55),
                 thickness = 3
                 )
            else: 
             cv2.putText(
                 img = frame,
                 text = previous_command if not previous_command=="" else "",
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
             if correction:
              if selected_pose=="tree" :
                command = ypc.tree_pose_correction(df_test)
              elif selected_pose=="chair":
                 command = ypc.chair_pose_correction(df_test)
              elif selected_pose=="warrior":
                 command=ypc.warrior_pose_correction(df_test)
              previous_command=command

            if not correction:
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
            previous_command=command

            previous_closest_label=y_pred_lab if not y_pred_lab=="" else "No Pose Detected"
            predicted_pose=y_pred_lab
            # cv2.flip(frame,1)
            # video.write(frame)
            if(capture):
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



@app.route('/home/')
@login_required
def hello():
    # global first,images_in_test_folder,images_out_test_folder,csvs_out_test_path,first
    app.config['UPLOAD_FOLDER'] = os.path.join(session['user_header'], 'uploadedimage/chair')
    # if first:  
    #  global user_header
    #  user_header=session['user_id']
    # print(session['preprocessor'])
    #  if google_authentication.preprocessor:
    #     user_authorization_model.preprocessor = google_authentication.preprocessor
    #  app.config['UPLOAD_FOLDER'] = os.path.join(user_header, 'uploaded_video')
    #  images_in_test_folder = os.path.join(user_header, 'uploadedimage')
    #  images_out_test_folder = 'uploadedimage_output'
    #  csvs_out_test_path = user_header+'/image_csv/uploaded_image.csv'
    #  preprocessor = ygp.MoveNetPreprocessor(
    #  images_in_folder=images_in_test_folder,
    #  images_out_folder=images_out_test_folder,
    #  csvs_out_path=csvs_out_test_path,
    #         )
    #  first=False
    return render_template('index.html',name=session["name"].split()[0])

@app.route('/getvariables')
@login_required
def getvariables(methods=['GET']):
    global previous_command, previous_closest_label
    variables={
        "previous_command" : previous_command,
        "previous_closest_label" : previous_closest_label
    }
    return jsonify(variables)


@app.route("/")
def start_page():
    if ("google_id" in session) or ('logged_in' in session): 
       return redirect(url_for('hello'))
    return render_template('User/signup.html')

# @app.route("/<user_id>")
# def start_page1(user_id=""):
#     return render_template('User/signup.html', user_id=user_id)
    

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
     return Response(gen_frames(preprocessor=jsonpickle.decode(session['preprocessor']),user_header=session['user_header']), mimetype='multipart/x-mixed-replace; boundary=frame')
    else: 
        return "No response"


@app.route('/capturepose/')
@login_required
def capture_pose():
    return render_template('Mainpages/capturepose.html',pose=predicted_pose,name=session['name'])

@app.route('/chronic/')
@login_required
def chronic():
    return render_template('Mainpages/chronic.html',name=session["name"].split()[0])

@app.route('/benefits/')
@login_required
def benefits():
    return render_template('Mainpages/benefits.html',name=session["name"].split()[0])

# @app.route('/liveyogacorrection/')
# @login_required
# def liveyogacorrection():
#     return render_template('Mainpages/liveyogacorrection.html')






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
            preprocessor.process(per_pose_class_limit=None,detection_threshold=0.1)
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
    global switch,camera,correction
    correction = 0
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
    
        return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])
    return render_template('Mainpages/capturepose.html',name=session["name"].split()[0])


@app.route('/liveyogacorrection/',methods=['POST','GET'])
def yogacorrectionform():
    global switch,camera,correction,selected_pose
    correction = 1
    if request.method == 'POST':
        if request.form.get('yogaposes_dropdown'):
            selected_pose=request.form.get('yogaposes_dropdown')
            print(selected_pose)
        elif request.form.get('click') == 'Capture':
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
        return render_template('Mainpages/liveyogacorrection.html',selected=selected_pose.capitalize(),name=session["name"].split()[0])
    return render_template('Mainpages/liveyogacorrection.html',selected=selected_pose.capitalize(),name=session["name"].split()[0])

if __name__ == '__main__':
    app.run(debug=True)
