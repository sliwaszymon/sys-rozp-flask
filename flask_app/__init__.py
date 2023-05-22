from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import hashlib
from apputils import create_qr, qr_to_base64



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
    links = db.relationship('Link', lazy='select', backref=db.backref('user', lazy='joined'))

    def __init__(self, email, password):
        self.email = email
        self.password = password
    



class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String, nullable=False)
    short_link = db.Column(db.String, nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, link, short_link, owner):
        self.link = link
        self.short_link = short_link
        self.owner = owner



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
    if "authusr" in session:
        db_usr = db.session.query(User).filter_by(email=session['authusr']).first()
        if request.method == "POST":
            link = request.form['link']
            short_link = request.form['short_link']
            full_short_link = str(request.root_url + str(db_usr.id) + '/' +short_link)
            qr = create_qr(full_short_link)
            if db.session.query(Link).filter_by(owner=db_usr.id, short_link=short_link).first():
                flash("You have already created same short link!", "error")
            if db.session.query(Link).filter_by(owner=db_usr.id, link=link).first():
                render_template("cutit.html", cutted={"qrcode": qr_to_base64(qr), "short_link": full_short_link})
            link_obj = Link(
                link = link,
                short_link = short_link,
                owner = db_usr.id
            )
            db.session.add(link_obj)
            db.session.commit()
            return render_template("cutit.html", cutted={"qrcode": qr_to_base64(qr), "short_link": full_short_link})
        else:
            return render_template("cutit.html", usrid=db_usr.id)
    else:
        return redirect(url_for("login"))
    
# TODO: DELETING LINKS
@app.route("/mylinks", methods=["GET", "DELETE"])
def mylinks():
    if "authusr" in session:
        db_usr = db.session.query(User).filter_by(email=session['authusr']).first()
        links = [{"id": link.id, "link": link.link, "short_link": link.short_link, "owner": link.owner} for link in db_usr.links]
        return render_template("mylinks.html", links=links)
    else:
        return redirect(url_for("login"))

# TODO: REDIRECTING VIA LINKS
@app.route("/<int:owner>/<str:short_link>")
def redirect():
    pass

    
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
