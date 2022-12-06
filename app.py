from flask import Flask, render_template,url_for

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('Basic_layouts/aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('Basic_layouts/contactus.html')

if __name__ == '__main__':
    app.run(debug=True)