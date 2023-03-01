from flask import Flask,jsonify,request

class User:
    def signup(self):
        user = {
            "_id":"",
            "name":"",
            "email":request.forms.get('email'),
            "password":request.forms.get('psw')
        }

        return jsonify(user), 200
        