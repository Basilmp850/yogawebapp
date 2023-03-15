from flask import Flask,render_template
from app import app
from user_auth.models import User

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