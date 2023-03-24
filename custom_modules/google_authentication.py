from flask import redirect, session, abort,request,url_for,render_template
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from google.oauth2 import id_token
import google.auth.transport.requests
import pathlib
import os
import requests
from app import app
from user_auth.models import db
import uuid
import jsonpickle
import custom_modules.yogaposturedetection as ygp

os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1" #possibly requires change in future

client_secrets_file=os.path.join(pathlib.Path(__file__).parent, "client_secret1.json")
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
    # global preprocessor
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
    preprocessorJSON = jsonpickle.encode(preprocessor, unpicklable=True)
    session['preprocessor']=preprocessorJSON
    # print(session)
    return redirect("/home")


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')