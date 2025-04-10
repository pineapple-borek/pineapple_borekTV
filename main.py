from flask import Flask
from flask import render_template
from markupsafe import escape

app = Flask(__name__,template_folder='website/templates')

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
@app.route("/hello/")
@app.route('/hello/<name>')
def hello(name=None):
     return  render_template('home.html',person=name)
#bölüm isimleri vesaire de kullanılabilir
#@app.route("/user/<username>")
#def show_user(username):
#    return f'kac {escape(username)}'
