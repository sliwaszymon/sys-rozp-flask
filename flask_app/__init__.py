from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        pass
    else:
        return render_template("login_page.html")

if __name__ == "__main__":
    app.run(debug=True)