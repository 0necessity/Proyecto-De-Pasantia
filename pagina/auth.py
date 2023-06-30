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


# The Uri to connect to PostGres Database
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
    menu_items = []
    if user_cookie is not None:
        user = deco(user_cookie)
        if user is not None:
            with connection:
                with connection.cursor() as cu:
                    cu.execute("SELECT photo FROM sign_up WHERE fname = %s;", (user["name"],))
                    pic_query = cu.fetchone()

            encoded_image = base64.b64encode(pic_query[0] if pic_query else b"").decode('utf-8')

            named = html.escape(user["name"])
            menu_items = [
                f'<a class="nav-item nav-link" id="logout" href="/logout">Cerrar sesión</a>',
                f"""
                <a href="/profile" class="link">
                    <p><span style="color: white;">Hola, {named}</span></p>
                    <img src="data:image/png;base64,{encoded_image}" class="rounded-circle me-2 ms-auto">
                </a>
                """,
                f'<img id="ppfp" src="data:image/png;base64,{encoded_image}" style="padding-right: 8px; border-radius: 20px">'
            ]
    return menu_items


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
    usuario = deco(user_cookie)

    if user_cookie:
        try:
            with connection:
                with connection.cursor() as cu:
                    cu.execute("SELECT * FROM sign_up WHERE fname = %s;", (usuario["name"],))
                    user = cu.fetchall()
                    print(user)
        except:
            with connection.cursor() as cu:
                cu.execute("SELECT * FROM sign_up WHERE fname = %s;", (usuario["name"],))
                user = cu.fetchall()
                print(user)
    else:
        user = []

    if request.method == "POST":
        print(request.form)
        print(request.method)
        if 'edit' in request.form:

            if user_cookie is not None:

                enmail = str(request.form.get("email")).lower()
                fname = str(request.form.get("firstName"))
                lname = str(request.form.get("lastName"))
                password1 = str(request.form.get("password1"))
                photo = request.files["image"].read()
                role = request.form.get("role")
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                match = re.match(pattern, str(request.form.get("email")))
                with connection:
                    with connection.cursor() as cu:
                        cu.execute("SELECT * FROM sign_up WHERE fname = %s;", (fname,))
                        r = cu.fetchone()
                        cu.execute("SELECT * FROM sign_up WHERE emails = %s;", (enmail,))
                        s = cu.fetchone()

                if 0 < len(enmail) and match is None:
                    flash("Ingresa un correo electrónico válido", category="error")
                elif 0 < len(fname) < 3:
                    flash("Tu nombre debe ser más largo", category="error")
                elif 0 < len(lname) < 3:
                    flash("Tu apellido debe ser más largo", category="error")
                elif 0 < len(password1) < 9:
                    flash("Tu contraseña debe ser más larga", category="error")
                elif r is not None and fname != usuario["name"]:
                    flash("Ese nombre ya está en uso, por favor selecciona uno nuevo", category="error")
                elif s is not None and enmail != usuario["emails"]:
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
                            with connection.cursor() as cu:
                                cu.execute("SELECT photo FROM sign_up WHERE fname = %s;", (usuario["name"],))
                                actual_photo = cu.fetchall()
                        PHOTO = psycopg2.Binary(photo) if len(photo) >= 5 else psycopg2.Binary(actual_photo[0][0])

                        apli = create_app()

                        with connection:
                            with connection.cursor() as cu:
                                cu.execute("""
                                    UPDATE sign_up
                                    SET fname = %s, emails = %s, rola = %s, lastname = %s, password = %s, photo = %s
                                    WHERE fname = %s;
                                """, (fname, enmail, role, lname, password1, PHOTO, usuario["name"]))

                        token = jwt.encode({
                            'name': fname,
                            "emails": enmail,
                            "role": role,
                            "lastname": lname,
                            "password": password1,
                            'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
                        },
                            apli.config['SECRET_KEY'])

                        res = make_response(redirect(url_for('auth.profile')))
                        res.delete_cookie("user")
                        res.set_cookie('user', token, 6000)

                        return res

                    except jwt.ExpiredSignatureError:
                        print("Expired signature error occurred")
                    except jwt.InvalidTokenError:
                        print("Invalid token error occurred")
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
        with connection.cursor() as cu:
            cu.execute("SELECT * FROM sign_up WHERE emails = %s;", (id_info["email"],))
            s = cu.fetchone()

    if s is not None:
        res = make_response(redirect(url_for('views.home')))
        cookie = request.cookies
        stat = cookie.get("user")

        if stat is None:
            apli = create_app()

            token = jwt.encode({
                'name': s[0],
                "emails": s[1],
                "role": s[2],
                "lastname": s[3],
                "password": s[4],
                'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
            },
                apli.config['SECRET_KEY'])

            res.set_cookie('user', token, 6000)

        return res

    global globo
    globo = id_info

    return redirect(url_for('auth.continues'))


@auth.route("/continuing", methods=['POST', "GET"])
def continues():
    if "family_name" in globo and len(globo["family_name"]) < 3:
        lname_is_missing = True
    else:
        lname_is_missing = "family_name" not in globo

    if request.method == "POST":
        lname = request.form.get("lastName")
        if not lname_is_missing:
            lname = globo.get("family_name", "")
        photo = b""
        if "picture" in globo:
            photo_response = requests.get(globo["picture"])
            if photo_response.status_code == 200:
                photo = photo_response.content
        if not len(lname) > 2:
            flash("Tu apellido debe ser más largo", category="error")
        else:
            email = globo["email"].lower()
            fname = globo["given_name"]
            password1 = ''.join(
                random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(20))
            role = request.form.get("role")

            with connection:
                with connection.cursor() as cu:
                    cu.execute("INSERT INTO sign_up VALUES (%s, %s, %s, %s, %s, %s);", (
                        fname, email, role, lname, password1, photo))

            res = make_response(redirect(url_for('auth.login')))
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

            res.set_cookie('user', token, 6000)
            return res

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

        username = "p8455947@gmail.com"
        password = "vydfcrcyaeathtmd"

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)


        except Exception as e:
            print(f"Failed to send email. Error: {str(e)}")

        return "<h1>MAIL SEND!</h1>"
    return render_template("password_send.html")

@auth.route("/password/<numeros>", methods=['POST', 'GET'])
def user_profile(numeros):
    if numeros == temp_pass_code:
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
    return f"{numeros} NO EXISTE!!"


@auth.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        lo_password = request.form.get("password")
        lo_email = request.form.get("email").lower()


        with connection:
            with connection.cursor() as cu:
                cu.execute("SELECT * FROM sign_up WHERE emails = %s;", (lo_email,))
                user = cu.fetchone()

        if not lo_email:
            flash("Por favor ingresa un correo electrónico", category="error")
        elif not lo_password:
            flash("Por favor ingresa una contraseña", category="error")
        elif not user:
            flash("Correo electrónico incorrecto", category="error")
        elif user[4] != lo_password:
            flash("Contraseña incorrecta", category="error")
        else:
            res = make_response(redirect(url_for('views.home')))
            cookie = request.cookies
            stat = cookie.get("user")

            if stat is None:
                apli = create_app()

                token = jwt.encode({
                    'name': user[0],
                    "emails": user[1],
                    "role": user[2],
                    "lastname": user[3],
                    "password": user[4],
                    'expiration': str(datetime.utcnow() + timedelta(seconds=6000))
                },
                    apli.config['SECRET_KEY'])

                res.set_cookie('user', token, 6000)
                return res
            return res
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
        import datetime as dd
        day = int(request.form['day'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        dob = dd.date(year, month, day)
        today = dd.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        # ///////////////////////////

        with connection:
            with connection.cursor() as cu:
                cu.execute("SELECT * FROM sign_up WHERE fname = %s;", (fname,))
                r = cu.fetchone()

        with connection:
            with connection.cursor() as cu:
                cu.execute("SELECT * FROM sign_up WHERE emails = %s;", (enmail,))
                s = cu.fetchone()

        if r is not None:
            flash("Ese nombre ya está en uso, por favor selecciona uno nuevo", category="error")
        elif s is not None:
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

            res = make_response(redirect(url_for('auth.login')))
            return res

        print(len(photo))
        print(fname)
        print(email)
    return render_template("sign-up.html", image_data=encoded_image, y=years, code=log_check())
