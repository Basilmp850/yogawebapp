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


os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1" #possibly requires change in future

client_secrets_file=os.path.join(pathlib.Path(__file__).parent, "client_secret1.json")
print(client_secrets_file)
flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email","openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)



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
    if not (session["state"]==request.args["state"]):
      abort(500) # state does not match

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=os.getenv("CLIENT_ID"),
        clock_skew_in_seconds=1
    )
    session['google_id']=id_info.get("sub")
    session['email']=id_info.get("email")
    session["name"]=id_info.get("name")

    user=db.User.find_one({"email": session['email']})
    if user:  
        email=session['email']
        session.clear()
        return render_template('User/signup.html',email=email)

    # print(session)
    return redirect("/home")


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')