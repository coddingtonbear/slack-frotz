from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "OK"


@app.route("/play")
def play():
    pass

