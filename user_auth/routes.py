from flask import Flask
from app import app
from user_auth.models import User

@app.route('/user/signup', methods = ['POST'])
def signup_m():
    return User().signup()
    

