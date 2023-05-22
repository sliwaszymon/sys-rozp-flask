from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import hashlib

db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = "lincutbysliwaandmartyniuk"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=5)
db.init_app(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = password


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db_user = db.session.query(User).filter_by(email=email).first()
        if db_user:
            if hashlib.md5(password.encode()).hexdigest() == db_user.password:
                session.permanent = True
                session["authusr"] = email
                flash("Login succesfull!")
                return redirect(url_for("cutit"))
            else:
                flash("Wrong password!", "error")
                return redirect(url_for("login"))
        flash("User with that email doesnt exist", "error")
        return redirect(url_for("login"))
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    flash("You have been logged out!", "info")
    session.pop("authusr", None)
    return(redirect(url_for("login")))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        password_repeat = request.form['passwordRepeat']
        if db.session.query(User).filter_by(email=email).first():
            flash("User with that email already exist.", "error")
            return(redirect(url_for("register")))
        elif password != password_repeat:
            flash("Passwords are not the same.", "error")
            return(redirect(url_for("register")))
        else:
            user = User(
                email=email,
                password=hashlib.md5(password.encode()).hexdigest()
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
    else:
        return render_template("register.html")
    

@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/cutit", methods=["POST", "GET"])
def cutit():
    authusr = None
    if "authusr" in session:
        authusr = session["authusr"]
    return render_template("cutit.html")

@app.route("/users")
def users():
    user = db.session.query(User).first()
    return {user.email : user.password}
    


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)