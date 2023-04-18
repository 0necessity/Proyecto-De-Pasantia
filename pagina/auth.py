import base64
import datetime
import email.charset
import os
import pathlib
import re
from flask import Blueprint, render_template, flash, url_for
from flask import session, redirect, request
from google_auth_oauthlib.flow import Flow
from sqlalchemy import *
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

import requests
from flask import session as sa
from flask import Flask, session, abort, redirect, request, make_response
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import random
import string

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # to allow Http traffic for local dev

GOOGLE_CLIENT_ID = "767012225869-o403codh716ib53pnug7pdhpmnqs7mid.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

auth = Blueprint("auth", __name__)
Base = declarative_base()

# KNOW PROBLEM THAT I MAY OR MAY NOT FIX IN THE FUTURE:
# THE COOKIES ARE SET TO IDs OF THE ENTRYS IN THE DATABASE THAT
# ARE ORGANIZED WITH AUTO-INCREMENT MAKING IT SO ANYONE CAN JUST INJECT THEIR COOKIE AN ACCESS THE PROFILE OF SOMEONE


class SignUp(Base):
    try:
        __tablename__ = "sign-up"
        name = Column("name", String, unique=True)
        emails = Column("emails", String, unique=True)
        role = Column("role", String)
        lastname = Column("lastname", String)
        password = Column("password", String)
        photo = Column("photo", String)
        cookieid = Column("cookieid", String)
        id = Column(Integer, primary_key=True, autoincrement=True)
    except:
        pass

    def __init__(self, name, emails, role, lastname, password, photo, cookieid):
        self.name = name
        self.emails = emails
        self.role = role
        self.lastname = lastname
        self.password = password
        self.photo = photo
        self.cookieid = cookieid
    def __repr__(self):
        return f"{self.name} {self.emails} {self.role} {self.lastname} {self.password} {self.photo} {self.cookieid} {self.id}"


engine = create_engine("sqlite:///mydb.db", echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

globo = {}



# def login_is_required(function):
#     def wrapper(*args, **kwargs):
#         if "google_id" not in sa:
#             return abort(401)  # Authorization required
#         else:
#             return function()
#
#     return wrapper


@auth.route("/logan")
def logan():
    authorization_url, state = flow.authorization_url()
    sa["state"] = state
    return redirect(authorization_url)


@auth.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not sa["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    s = session.query(SignUp).filter(SignUp.emails == id_info["email"]).all()
    if len(s) > 0:
        # HERES WHERE YOU ARE GONNA GET THE COOKIE
        res = make_response(redirect(url_for('views.home')))
        cookie = request.cookies
        stat = cookie.get("user")
        print(s)
        print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
        print(len(s))
        try:
            print(s[7])
        except:
            pass

        print(stat)
        if stat is None:
            print(s)
            # need to make a query here:
            res.set_cookie("user", id_info["given_name"], 600)
        return res

    global globo
    globo = id_info

    return redirect(url_for('auth.continues'))


# @auth.route("/lagout")
# def lagout():
#     sa.clear()
#     return redirect("/")


# @auth.route("/protected_area")
# @login_is_required
# def protected_area():
#     return f"Hello {sa['name']}! <br/> <a href='/logout'><button>Logout</button></a>"


@auth.route("/continuing", methods=['POST', "GET"])
def continues():
    if "family_name" in globo:
        lname_is_missing = False
    else:
        lname_is_missing = True

#
    if request.method == "POST":
        print(globo)
        if lname_is_missing == False:
            lname = globo["family_name"]
        else:
            lname = request.form.get("lname")

        if "picture" in globo:
            print(globo["picture"])
            print(requests.get(globo["picture"]))
            photo = requests.get(globo["picture"]).content
        else:
            image_path = os.path.join(os.getcwd(), 'pagina', 'static', "default.jpg")
            with open(image_path, 'rb') as image_file:
                photo = image_file.read()

        chars = string.ascii_letters + string.digits + string.punctuation
        enmail = globo["email"]
        fname = globo["given_name"]
        password1 = ''.join(random.choice(chars) for i in range(20))
        role = request.form.get("role")
        chars = string.ascii_letters + string.digits + string.punctuation
        cookieID = ''.join(random.choice(chars) for i in range(30))

        huh = SignUp(fname, enmail, role, lname, password1, photo, cookieID)
        session.add(huh)
        session.commit()
        print(session.query(SignUp).all())

        res = make_response(redirect(url_for('auth.login')))
        # cHANGE IT so it sets id instead of name
        res.set_cookie("user", cookieID, 600)
        # HERES WHERE YOU ARE GONNA SET THE COOKIE
        return res
    return render_template("tranquilo.html", lname_status=lname_is_missing)


@auth.route("/login", methods=['POST', "GET"])
def login():
    if request.method == "POST":
        lo_password = str(request.form.get("password"))
        lo_email = str(request.form.get("email")).lower()
        ema = session.query(SignUp).filter_by(emails=lo_email).all()
        passo = session.query(SignUp).filter_by(password=lo_password).all()
        # THERES A PROBLEM, THIS ONLY CHECK IF YOU PUT AN EMAIL THAT EXIST AND AN PASSWORD THAT EXIST

        if len(lo_email) < 1:
            flash("Please enter an email", category="error")
        elif len(lo_password) < 1:
            flash("Please enter a password", category="error")
        else:
            if len(passo) < 1:
                flash("Wrong password", category="error")
            if len(ema) < 1:
                flash("Wrong email", category="error")
            if len(ema) == 1 and len(passo) == 1:
                # HERES WHERE YOU ARE GONNA GET THE COOKIE
                res = make_response(redirect(url_for('views.home')))
                cookie = request.cookies
                stat = cookie.get("user")
                print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(stat)
                if stat is None:
                    #this dosent work, really work with IDs
                    #res.set_cookie("user", id_info["given_name"], 600)
                    pass
                return res

    return render_template("login.html", coco=23)


@auth.route("/logout")
def logout():
    return ">:D"


@auth.route("/sign_up", methods=['POST', "GET"])
def sign_up():
    yyears = []
    for year in range(1900, 2024):
        yyears.append(year)
    years = yyears[::-1]

    photo = b""
    encoded_image = base64.b64encode(photo).decode('utf-8')
    if request.method == "POST":
        enmail = str(request.form.get("email")).lower()
        fname = str(request.form.get("firstName"))
        lname = str(request.form.get("lastName"))
        password1 = str(request.form.get("password1"))
        password2 = str(request.form.get("password2"))
        photo = request.files["image"].read()
        role = request.form.get("role")
        # This is neede it so you can display the saved images in your website
        encoded_image = base64.b64encode(photo).decode('utf-8')
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        match = re.match(pattern, str(request.form.get("email")))
        # ///////////////////////////
        day = int(request.form['day'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        dob = datetime.date(year, month, day)
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        # ///////////////////////////
        print(session.query(SignUp).all())
        print("huh?")

        r = session.query(SignUp).filter(SignUp.name == fname).all()
        s = session.query(SignUp).filter(SignUp.emails == enmail).all()

        print(password1)
        if len(r) > 0:
            flash("That name is already in use, please select a new one", category="error")
        elif len(s) > 0:
            flash("That email is already in use, please select a new one", category="error")
        elif age < 18:
            flash("You must be above 18 to enter", category="error")
        elif password1 != password2:
            flash("Your passwords need to be the same", category="error")
        elif len(password1) < 8:
            flash("Your password need to be larger", category="error")
        elif len(fname) < 3:
            flash("Your name need to be larger", category="error")
        elif len(lname) < 3:
            flash("Your last name need to be larger", category="error")
        elif match is None:
            flash("Please enter an valid email direction", category="error")
        elif len(photo) > 5000000:
            flash("The size of your profile picture is too big. Please select an smaller one", category="error")
        # DE-COMMENT THIS LATER (MAKE TEST ON THIS TOO TO MAKE SURE IT WORKS WELL)
        # elif not photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[:4] == b'\x89PNG' or photo == None:
        #     flash("This type of files is not supported, please make sure to upload a PNG or JPEG file", category="error")
        else:
            if len(photo) < 5:
                image_path = os.path.join(os.getcwd(), 'pagina', 'static', "default.jpg")
                with open(image_path, 'rb') as image_file:
                    photo = image_file.read()


            #YOU PROB SHOULD MAKE THIS INTO A FUNCTION
            chars = string.ascii_letters + string.digits + string.punctuation
            cookieID = ''.join(random.choice(chars) for i in range(30))

            huh = SignUp(fname, enmail, role, lname, password1, photo, cookieID)
            session.add(huh)
            session.commit()
            print(session.query(SignUp).all())
            # HERES WHERE YOU ARE GONNA SET THE COOKIE
            res = make_response(redirect(url_for('auth.login')))
            # cHANGE IT so it sets id instead of name
            res.set_cookie("user", cookieID, 600)
            return res

        print(len(photo))
        print(fname)
        print(email)
    return render_template("sign-up.html", image_data=encoded_image, y=years)
