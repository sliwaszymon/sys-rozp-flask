from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import hashlib
from apputils import create_qr, qr_to_base64



db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = "lincutbysliwaandmartyniuk"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dbusr:passwd@db:3306/flaskapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=5)
db.init_app(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    links = db.relationship('Link', lazy='select', backref=db.backref('user', lazy='joined'))

    def __init__(self, email, password):
        self.email = email
        self.password = password


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(255), nullable=False)
    short_link = db.Column(db.String(20), nullable=False)
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
                flash("Login succesfull!", "success")
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
    return redirect(url_for("login"))


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
            flash("User created succesfully", "success")
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
        db_links = [tmp_link for tmp_link in db_usr.links]
        if request.method == "POST":
            form_link = request.form['link']
            form_short_link = request.form['short_link']
            if form_link in [tmp_link.link for tmp_link in db_links]:
                flash("This link was cutted last time", "info")
                link_obj = [tmp_link for tmp_link in db_links if tmp_link.link == form_link][0]
                full_short_link = str(request.root_url + str(db_usr.id) + '/' + link_obj.short_link)
                qr = create_qr(full_short_link)
                return render_template("cutit.html", usrid=db_usr.id, cutted={"qrcode": qr_to_base64(qr), "short_link": full_short_link})
            elif form_short_link in [link.short_link for link in db_links]:
                    flash("You have already created same short link!", "error")
                    return render_template("cutit.html", usrid=db_usr.id)
            else:
                full_short_link = str(request.root_url + str(db_usr.id) + '/' + form_short_link)
                qr = create_qr(full_short_link)
                link_obj = Link(
                    link = form_link,
                    short_link = form_short_link,
                    owner = db_usr.id
                )
                db.session.add(link_obj)
                db.session.commit()
                return render_template("cutit.html", usrid=db_usr.id, cutted={"qrcode": qr_to_base64(qr), "short_link": full_short_link})
        else:
            return render_template("cutit.html", usrid=db_usr.id)
    else:
        return redirect(url_for("login"))
    

@app.route("/mylinks")
def mylinks():
    if "authusr" in session:
        db_usr = db.session.query(User).filter_by(email=session['authusr']).first()
        links = [{"id": link.id, "link": link.link, "short_link": link.short_link, "owner": link.owner, "full_short_link": str(request.root_url + str(db_usr.id) + '/' + link.short_link), "qrcode": qr_to_base64(create_qr(str(request.root_url + str(db_usr.id) + '/' + link.short_link)))} for link in db_usr.links]
        return render_template("mylinks.html", links=links)
    else:
        return redirect(url_for("login"))
    

@app.route("/mylinks/delete/<int:id>")
def delete_link(id):
    if "authusr" in session:
        db_usr = db.session.query(User).filter_by(email=session['authusr']).first()
        link = [link for link in db_usr.links if link.id==id][0]
        if link.owner == db_usr.id:
            db.session.delete(link)
            db.session.commit()
            flash("Link succesfully deleted!", "info")
            return redirect(url_for("mylinks"))
        else:
            flash("This is not your link!", "error")
            return redirect(url_for("mylinks"))
    else:
        return redirect(url_for("login"))


@app.route("/<int:owner>/<short_link>")
def redirecting(owner, short_link):
    db_usr = db.session.query(User).filter_by(id=owner).first()
    links = [link for link in db_usr.links]
    if short_link in [link.short_link for link in links]:
        link = [x.link for x in links if short_link == x.short_link][0]
        return redirect(link)
    else:
        return redirect(url_for("home"))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # app.run(debug=True)
    app.run(host='0.0.0.0')

