import base64
import datetime
import email.charset
import os
import html
from pagina import create_app
import jwt
from datetime import datetime, timedelta
import pathlib
import re
import requests
from flask import Blueprint, render_template, flash, url_for
from flask import session as sa
from flask import Flask, session, abort, redirect, request, make_response
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import random
import string
import psycopg2

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # to allow Http traffic for local dev
GOOGLE_CLIENT_ID = "767012225869-o403codh716ib53pnug7pdhpmnqs7mid.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

auth = Blueprint("auth", __name__)


def deco(token):
    try:
        apli = create_app()
        payload = jwt.decode(token, apli.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.exceptions.DecodeError:
        return {}


connection = psycopg2.connect(
    "postgres://csxmmwsv:2ySU--ymn0e_2TscHlD1C038WqJeTAZ6@drona.db.elephantsql.com/csxmmwsv"
)
try:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE Sign_Up (
            fname TEXT,
            emails TEXT,
            rola TEXT,
            lastname TEXT,
            password TEXT,
            photo BYTEA,
            id SERIAL PRIMARY KEY
            );""")
except:
    pass


def log_check():
    cookie = request.cookies
    user_cookie = cookie.get("user")
    nav_option = []
    if user_cookie is not None:
        user = deco(user_cookie)
        if user is not None:
            with connection:
                pic_query = one_query(user["name"], "photo", "fname")

            encoded_image = base64.b64encode(pic_query[0] if pic_query else b"").decode('utf-8')

            named = html.escape(user["name"])
            nav_option = [
                f"""
                <div class="closure">
                <a class="nav-item nav-link" id="logout" href="/logout">Cerrar sesión</a>
                <div class="underline"></div>        
                </div>
                """,
                f"""
                <a href="/profile" class="link">
                    <p><span style="position: relative; color: white; top: 5px;">Hola, {named}</span></p>
                    <img src="data:image/png;base64,{encoded_image}" class="rounded-circle me-2 ms-auto">
                </a>
                """,
                f'<img id="ppfp"src="data:image/png;base64,{encoded_image}"style="margin-right:8px;border-radius:20px;border:solid 1px #c7c8c8;">',
                "", "", "", ""
            ]
    if user_cookie is None:
        nav_option.extend(["", "", "", """
                                        <div class="closure">
                                           <a class="nav-item nav-link" id="signUp" href="/sign_up">Registrate</a>
                                        <div class="underline"></div>        
                                        </div>
                                       """,

                                       """
                                        <div class="closure">
                                           <a class="nav-item nav-link" id="login" href="/login">Inicia Sesión</a>
                                        <div class="underline"></div>        
                                        </div>
                                       """])

    return nav_option


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)
user_token = {}


@auth.route("/OAuth_redirect")
def OAuth_redirect():
    authorization_url, state = flow.authorization_url()
    sa["state"] = state
    return redirect(authorization_url)


@auth.route("/profile", methods=['POST', "GET"])
def profile():
    user_cookie = request.cookies.get("user")
    usuario = deco(user_cookie)

    if user_cookie:
        try:
            with connection:
                user = all_query(usuario["name"], "*", "fname")
        except:
            user = all_query(usuario["name"], "*", "fname")

    else:
        user = []
    print(user[0][2])

    if request.method == "POST":
        if 'edit' in request.form:

            if user_cookie is not None:

                enmail, fname, lname, password1, photo, role, pattern, match = input_getter()
                role = user[0][2]

                with connection:
                    e_mail = one_query(enmail, "*", "emails")
                    name = one_query(fname, "*", "fname")

                if 0 < len(enmail) and match is None:
                    flash("Ingresa un correo electrónico válido", category="error")
                elif 0 < len(fname) < 3:
                    flash("Tu nombre debe ser más largo", category="error")
                elif 0 < len(lname) < 3:
                    flash("Tu apellido debe ser más largo", category="error")
                elif 0 < len(password1) < 9:
                    flash("Tu contraseña debe ser más larga", category="error")
                elif name is not None and fname != usuario["name"]:
                    flash("Ese nombre ya está en uso, por favor selecciona uno nuevo", category="error")
                elif e_mail is not None and enmail != usuario["emails"]:
                    flash("Ese correo electrónico ya está en uso, por favor selecciona uno nuevo", category="error")
                elif len(photo) > 5000000:
                    flash("El tamaño de tu foto de perfil es demasiado grande. Por favor, selecciona una más pequeña",
                          category="error")
                elif len(photo) != 0 and not any(
                        pattern in photo[:4] for pattern in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\x89PNG']):
                    flash("Este tipo de archivos no es compatible, por favor asegúrate de cargar un archivo PNG o JPEG",
                          category="error")

                else:
                    try:
                        with connection:
                            actual_photo = all_query(usuario["name"], "photo", "fname")
                        PHOTO = psycopg2.Binary(photo) if len(photo) >= 5 else psycopg2.Binary(actual_photo[0][0])

                        with connection:
                            with connection.cursor() as cu:
                                cu.execute("""
                                    UPDATE sign_up
                                    SET fname = %s, emails = %s, rola = %s, lastname = %s, password = %s, photo = %s
                                    WHERE fname = %s;
                                """, (fname, enmail, role, lname, password1, PHOTO, usuario["name"]))
                                flash("Edición de perfil establecida correctamente", category="success")

                        apli = create_app()

                        token = jwt.encode({
                            'name': fname,
                            "emails": enmail,
                            "role": role,
                            "lastname": lname,
                            "password": password1,
                            'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
                        },
                            apli.config['SECRET_KEY'])

                        biscuit = make_response(redirect(url_for('auth.profile')))
                        biscuit.delete_cookie("user")
                        biscuit.set_cookie('user', token, 6000)

                        return biscuit

                    except jwt.ExpiredSignatureError:
                        pass
                    except jwt.InvalidTokenError:
                        pass
        elif 'delete' in request.form:
            with connection.cursor() as cu:
                cu.execute("DELETE FROM sign_up WHERE fname = %s;", (usuario["name"],))
                return redirect(url_for('auth.logout'))

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

    with connection:
        existing_mail = one_query(id_info["email"], "*", "emails")

    if existing_mail is not None:
        biscuit = make_response(redirect(url_for('views.home')))
        cookie = request.cookies
        users_cookie = cookie.get("user")

        if users_cookie is None:
            biscuit.set_cookie('user', token_setter(existing_mail), 6000)

        return biscuit

    global user_token
    user_token = id_info

    return redirect(url_for('auth.continues'))


@auth.route("/continuing", methods=['POST', "GET"])
def continues():
    if "family_name" in user_token and len(user_token["family_name"]) < 3:
        lname_is_missing = True
    else:
        lname_is_missing = "family_name" not in user_token

    if request.method == "POST":
        lname = request.form.get("lastName")
        if not lname_is_missing:
            lname = user_token.get("family_name", "")
        photo = b""
        if "picture" in user_token:
            photo_response = requests.get(user_token["picture"])
            if photo_response.status_code == 200:
                photo = photo_response.content
        if not len(lname) > 2:
            flash("Tu apellido debe ser más largo", category="error")
        else:
            email = user_token["email"].lower()
            fname = user_token["given_name"]
            password1 = ''.join(
                random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(20))
            role = request.form.get("role")

            with connection:
                with connection.cursor() as cu:
                    cu.execute("INSERT INTO sign_up VALUES (%s, %s, %s, %s, %s, %s);", (
                        fname, email, role, lname, password1, photo))

            biscuit = make_response(redirect(url_for('auth.login')))
            apli = create_app()

            token = jwt.encode({
                'name': fname,
                "emails": email,
                "role": role,
                "lastname": lname,
                "password": password1,
                'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
            },
                apli.config['SECRET_KEY'])

            biscuit.set_cookie('user', token, 6000)
            return biscuit

    return render_template("tranquilo.html", lname_status=lname_is_missing, code=log_check())


temp_lo_email = ''
temp_pass_code = ''


@auth.route("/password", methods=['POST', "GET"])
def password():
    if request.method == "POST":
        global temp_pass_code
        temp_pass_code = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(30))
        global temp_lo_email
        temp_lo_email = request.form.get("email").lower()

        import smtplib
        from email.message import EmailMessage

        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        sender_email = "p8455947@gmail.com"

        subject = "Recuperacion de contraseña"
        body = "Para recuperar su contraseña, por favor ingrese a http://127.0.0.1:5000/password/" + temp_pass_code

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = temp_lo_email
        msg.set_content(body)

        USERNAME = "p8455947@gmail.com"
        PASSWORD = "vydfcrcyaeathtmd"

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(USERNAME, PASSWORD)
                server.send_message(msg)

        except Exception as e:
            pass
        return render_template("Mail.html")
    return render_template("password_send.html")


@auth.route("/password/<numbers>", methods=['POST', 'GET'])
def user_profile(numbers):
    if numbers == temp_pass_code:
        if request.method == "POST":
            password1 = str(request.form.get("password1"))
            with connection:
                with connection.cursor() as cu:
                    cu.execute("""
                        UPDATE sign_up
                        SET password = %s
                        WHERE emails = %s;
                    """, (password1, temp_lo_email))
            return redirect(url_for('auth.login'))
        return render_template("pass_rec.html")
    return abort(404)


@auth.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        lo_password = request.form.get("password")
        lo_email = request.form.get("email").lower()

        with connection:
            user = one_query(lo_email, "*", "emails")

        if not lo_email:
            flash("Por favor ingresa un correo electrónico", category="error")
        elif not lo_password:
            flash("Por favor ingresa una contraseña", category="error")
        elif not user:
            flash("Correo electrónico incorrecto", category="error")
        elif user[4] != lo_password:
            flash("Contraseña incorrecta", category="error")
        else:
            biscuit = make_response(redirect(url_for('views.home')))
            cookie = request.cookies
            users_cookie = cookie.get("user")

            if users_cookie is None:
                biscuit.set_cookie('user', token_setter(user), 6000)
                return biscuit
            return biscuit
    return render_template("login.html", code=log_check())


@auth.route("/logout")
def logout():
    biscuit = make_response(redirect(url_for('views.home')))
    biscuit.set_cookie("user", value="", expires=0)
    return biscuit


@auth.route("/sign_up", methods=['POST', "GET"])
def sign_up():
    yyears = []
    for year in range(1900, 2024):
        yyears.append(year)
    years = yyears[::-1]

    photo = b""
    encoded_image = base64.b64encode(photo).decode('utf-8')
    if request.method == "POST":
        password2 = str(request.form.get("password2"))

        enmail, fname, lname, password1, photo, role, pattern, match = input_getter()
        role = "Supervisor"

        encoded_image = base64.b64encode(photo).decode('utf-8')
        # ///////////////////////////
        import datetime as dd
        try:
            day = int(request.form['day'])
            month = int(request.form['month'])
            year = int(request.form['year'])
        except:
            flash("Por favor seleccione una fecha", category="error")
            return redirect(url_for('auth.sign_up'))

        dob = dd.date(year, month, day)
        today = dd.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        # ///////////////////////////

        with connection:
            name = one_query(fname, "*", "fname")
            e_mail = one_query(enmail, "*", "emails")

        if name is not None:
            flash("Ese nombre ya está en uso, por favor selecciona uno nuevo", category="error")
        elif e_mail is not None:
            flash("Ese correo electrónico ya está en uso, por favor selecciona uno nuevo", category="error")
        elif age < 18:
            flash("Debes tener más de 18 años para ingresar", category="error")
        elif password1 != password2:
            flash("Tus contraseñas deben ser iguales", category="error")
        elif len(password1) < 8:
            flash("Tu contraseña debe ser más larga", category="error")
        elif len(fname) < 3:
            flash("Tu nombre debe ser más largo", category="error")
        elif len(lname) < 3:
            flash("Tu apellido debe ser más largo", category="error")
        elif match is None:
            flash("Por favor ingresa una dirección de correo electrónico válida", category="error")
        elif len(photo) > 5000000:
            flash("El tamaño de tu imagen de perfil es demasiado grande. Por favor selecciona una más pequeña",
                  category="error")
        elif not (photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                          :4] == b'\x89PNG' or photo == b''):
            flash("Este tipo de archivo no es compatible, por favor asegúrate de subir un archivo PNG o JPEG",
                  category="error")

        else:
            if len(photo) < 5:
                image_path = os.path.join(os.getcwd(), 'pagina', 'static', "default.jpg")
                with open(image_path, 'rb') as image_file:
                    photo = image_file.read()

            with connection:
                with connection.cursor() as cu:
                    cu.execute("INSERT INTO sign_up VALUES (%s, %s, %s, %s, %s, %s);", (
                        fname, enmail, role, lname, password1, photo))

            biscuit = make_response(redirect(url_for('auth.login')))
            return biscuit

    return render_template("sign-up.html", image_data=encoded_image, y=years, code=log_check())


def all_query(example, amount, types):
    with connection.cursor() as cu:
        cu.execute(f"SELECT {amount} FROM sign_up WHERE {types} = %s;", (example,))
        return cu.fetchall()


def one_query(example, amount, types):
    with connection.cursor() as cu:
        cu.execute(f"SELECT {amount} FROM sign_up WHERE {types} = %s;", (example,))
        return cu.fetchone()


def input_getter():
    enmail = str(request.form.get("email")).lower()
    fname = str(request.form.get("firstName"))
    lname = str(request.form.get("lastName"))
    password1 = str(request.form.get("password1"))
    photo = request.files["image"].read()
    role = request.form.get("role")
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    match = re.match(pattern, str(request.form.get("email")))
    return enmail, fname, lname, password1, photo, role, pattern, match


def token_setter(value):
    apli = create_app()

    token = jwt.encode({
        'name': value[0],
        "emails": value[1],
        "role": value[2],
        "lastname": value[3],
        "password": value[4],
        'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
    },
        apli.config['SECRET_KEY'])

    return token
