import base64
import datetime
import email.charset
import os
import html

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


def log_check():
    cookie = request.cookies
    user_cookie = cookie.get("user")
    menu_items = []

    if user_cookie is not None:
        user = session.query(SignUp).filter_by(cookieid=user_cookie).first()
        if user is not None:
            encoded_image = base64.b64encode(user.photo).decode('utf-8')
            named = html.escape(user.name)
            menu_items = [
                f'<a class="nav-item nav-link" id="logout" href="/logout">Logout</a>',
                f"""
                <link rel="stylesheet" href="../static/please.css">
                <a href="/profile" class="link">
                    <p><span style="color: white;">Hola, {named}</span></p>
                    <img src="data:image/png;base64,{encoded_image}" class="rounded-circle me-2 ms-auto">
                </a>
                """
            ]
    return menu_items


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

    def __str__(self):
        return f"{self.name} {self.emails} {self.role} {self.lastname} {self.password} {self.photo} {self.cookieid} {self.id}"


engine = create_engine("sqlite:///mydb.db", echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

globo = {}


@auth.route("/logan")
def logan():
    authorization_url, state = flow.authorization_url()
    sa["state"] = state
    return redirect(authorization_url)


@auth.route("/profile", methods=['POST', "GET"])
def profile():
    cookie = request.cookies
    user_cookie = cookie.get("user")
    user = session.query(SignUp).filter_by(cookieid=user_cookie).first()
    if request.method == "POST":
        if user_cookie is not None:
            enmail = str(request.form.get("email")).lower()
            fname = str(request.form.get("firstName"))
            lname = str(request.form.get("lastName"))
            password1 = str(request.form.get("password1"))
            photo = request.files["image"].read()
            role = request.form.get("role")
            encoded_image = base64.b64encode(photo).decode('utf-8')
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            match = re.match(pattern, str(request.form.get("email")))

            r = session.query(SignUp).filter_by(name=fname).first()

            s = session.query(SignUp).filter_by(emails=enmail).first()

            if 0 < len(enmail) and match is None:
                flash("Enter a valid email", category="error")
            elif 0 < len(fname) < 3:
                flash("Your first name need to be larger", category="error")
            elif 0 < len(lname) < 3:
                flash("Your last name need to be larger", category="error")
            elif 0 < len(password1) < 9:
                flash("Your password need to be larger", category="error")
            elif r is not None and fname != user.name:
                flash("That name is already in use, please select a new one", category="error")
            elif s is not None and enmail != user.emails:
                flash("That email is already in use, please select a new one", category="error")
            elif len(photo) > 5000000:
                flash("The size of your profile picture is too big. Please select an smaller one", category="error")
            elif len(photo) != 0 and not any(
                    pattern in photo[:4] for pattern in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\x89PNG']):
                flash("This type of files is not supported, please make sure to upload a PNG or JPEG file",
                      category="error")
            else:
                if len(fname) != 0:
                    user.name = fname
                if len(enmail) != 0:
                    user.emails = enmail
                if len(lname) != 0:
                    user.lastname = lname
                if len(password1) != 0:
                    user.password = password1
                if len(photo) >= 5:
                    user.photo = photo
                user.role = role
                session.commit()
    return render_template("profile.html", code=log_check(), user=user)


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

        print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")

        if stat is None:
            # need to make a query here:
            ras = session.query(SignUp.cookieid).filter(SignUp.emails == id_info["email"].lower()).first()
            cookieid = ras[0] if ras else None
            cookieid_str = str(cookieid) if cookieid else None
            res.set_cookie("user", cookieid_str, 600)

        return res

    global globo
    globo = id_info

    return redirect(url_for('auth.continues'))
# cgc > 2 --> False
# cg > 2 --> True

@auth.route("/continuing", methods=['POST', "GET"])
def continues():

    if "family_name" in globo:
        lname_is_missing = False
    else:
        lname_is_missing = True

    #
    if request.method == "POST":
        print(globo)
        if not lname_is_missing:
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
        enmail = globo["email"].lower()
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
        res.set_cookie("user", cookieID, 600)
        return res
    return render_template("tranquilo.html", lname_status=lname_is_missing, code=log_check())


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
                ebail = session.query(SignUp.password).filter(SignUp.emails == lo_email).first()
                passw = ebail[0] if ebail else None
                srt_of_qpass = str(passw) if passw else None

                if lo_password == srt_of_qpass:
                    res = make_response(redirect(url_for('views.home')))
                    cookie = request.cookies
                    stat = cookie.get("user")

                    if stat is None:
                        ras = session.query(SignUp.cookieid).filter(SignUp.emails == lo_email).first()
                        cookieid = ras[0] if ras else None
                        cookieid_str = str(cookieid) if cookieid else None
                        res.set_cookie("user", cookieid_str, 600)
                    return res
                else:
                    flash("Wrong password", category="error")

    return render_template("login.html", code=log_check())


@auth.route("/logout")
def logout():
    res = make_response(redirect(url_for('views.home')))
    res.set_cookie("user", value="", expires=0)
    return res


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

            # YOU PROB SHOULD MAKE THIS INTO A FUNCTION
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
    return render_template("sign-up.html", image_data=encoded_image, y=years, code=log_check())
