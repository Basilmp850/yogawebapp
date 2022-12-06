from flask import Flask, render_template,url_for,Response,request
import os
import cv2
import datetime,time
import numpy as np
from threading import Thread

app = Flask(__name__)

global capture, switch, out 
capture=0
switch=1
camera = cv2.VideoCapture(0)

def gen_frames():  # generate frame by frame from camera
    global out, capture
    while True:
        success, frame = camera.read() 
        if success:
            if(capture):
                capture=0
                now = datetime.datetime.now()
                #to save the image in the pc
                p = os.path.sep.join(['capture', "capture_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
            
         
                
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
                
        else:
            pass



@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('Basic_layouts/aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('Basic_layouts/contactus.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capturepose')
def capture_pose():
    return render_template('capturepose.html')


@app.route('/requests',methods=['POST','GET'])
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
        return render_template('capturepose.html')
    return render_template('capturepose.html')

if __name__ == '__main__':
    app.run(debug=True)