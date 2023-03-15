from flask import Flask,jsonify,request,session,redirect,render_template,url_for
import uuid
from passlib.hash import pbkdf2_sha256
from app import mongoclient
from app import app
from flask_mail import Mail,Message
from random import randint


app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465     
app.config["MAIL_USERNAME"] = 'jonathannebu10@gmail.com'  
app.config['MAIL_PASSWORD'] = 'dbyczdyjhldjtdzl'  
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True  

mail = Mail(app)   

db = mongoclient.User_authentication
class User:
    def start_session(self,user,verification_status=False):
        print("1")
        session['logged_in']=True
        print("2")
        session['user']=user
        session['name']=user['name']
        session['verified']=True
        if not verification_status:
         db.User.update_one({"email":user['email']},{"$set":{"verified": True}})
         return redirect(url_for('hello'))
        return jsonify(user),200

    def signup(self):
        user = {
            "_id":uuid.uuid4().hex,
            "name": request.form.get("name"),
            "email":request.form.get("email"),
            "password":request.form.get("psw"),
            "verified": False
        }
        user['password'] = pbkdf2_sha256.encrypt(user['password'])
        existing_user = db.User.find_one({"email": user['email']})
        if existing_user:
            if not existing_user['verified']:
              db.User.delete_one(existing_user)
              return self.verify(user)
            else:
             return jsonify({"error":"Email address already in use"}), 400
        if db.User.insert_one(user): 
            return self.verify(user)
        return jsonify({"error":"Signup failed!!"}), 400
    
    def verify(self,user):
        user["random-otp"] = randint(000000,999999)
        db.User.update_one({"email":user['email']},{"$set":{"random-otp": user["random-otp"]}})
        print(user)
        msg = Message('OTP',sender = 'stramerjosh@gmail.com', recipients = [user['email']])  
        msg.body = "Your OTP is: "+str(user["random-otp"])  
        mail.send(msg)  
        # render_template(url_for('verification'),email=user['email'])
        return jsonify(user),200

    def validate(self):
        user_id=request.form['user-id']
        print("user--------------"+user_id)
        user_otp = request.form['otp']  
        print(int(user_otp))
        
        user = db.User.find_one({"_id": user_id})
        print(user)
        if user["random-otp"]==int(user_otp):  
         return self.start_session(user)
        else:
         return "<h3>failure</h3>"
    
    def login(self):
        user = db.User.find_one({"email": request.form.get('email')})
        flag = 0
        if user and pbkdf2_sha256.verify(request.form.get('psw'),user['password']):
            if user['verified']:
             return self.start_session(user,verification_status=True)
            else:
               flag = 1
        if flag:
           return jsonify({"error":"Unverified email"}),401
        return jsonify({"error":"Invalid Username/Password"}),401
       
    def signout(self):
        session.clear()
        return redirect('/')
    
