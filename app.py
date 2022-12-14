from flask import Flask, render_template,url_for,Response,request, flash, redirect
import os
import cv2
import datetime,time
import numpy as np
from werkzeug.utils import secure_filename

allowed_formats = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploadedimages')

global capture, switch, out 
capture=0
switch=1
camera = cv2.VideoCapture(0)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_formats

def gen_frames():  # generate frame by frame from camera
    global out, capture
    while True:
        success, frame = camera.read() 
        if success:
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
    return render_template('Mainpages/capturepose.html')



@app.route('/chronic')
def chronic():
    return render_template('Mainpages/chronic.html')

@app.route('/benefits')
def benefits():
    pass

@app.route('/preventionchronic')
def preventionchronic():
    pass

@app.route('/detection', methods = ['POST','GET'])
def detection():
    full_filename = ""
    if request.method == 'POST':
        for file in os.listdir('static/uploadedimages'):
          os.remove('static/uploadedimages/' + file)
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
    return render_template('Mainpages/detection.html', uploaded_image = full_filename)


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
        return render_template('Mainpages/capturepose.html')
    return render_template('Mainpages/capturepose.html')

if __name__ == '__main__':
    app.run(debug=True)