import base64
import html
import os
import random
import time

import psycopg2
from flask import *  # fix this later
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# from .auth import SignUp
from pagina import create_app
import jwt
from datetime import datetime, timedelta

engine = create_engine("sqlite:///mydb.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()
views = Blueprint("views", __name__)


def deco(token):
    apli = create_app()
    payload = jwt.decode(token, apli.config['SECRET_KEY'], algorithms=['HS256'])
    return payload


connection = psycopg2.connect(
    "postgres://csxmmwsv:2ySU--ymn0e_2TscHlD1C038WqJeTAZ6@drona.db.elephantsql.com/csxmmwsv"
)
entries = psycopg2.connect(
    "postgres://bzbgygjd:xVajVaaV111nO6eiS59S_r7Y3aFgr8k5@drona.db.elephantsql.com/bzbgygjd"
)

try:
    with entries:
        with entries.cursor() as cu:
            cu.execute("""
            CREATE TABLE posts (
            title TEXT,
            price INTEGER,
            quant INTEGER,
            descrip TEXT,
            owner_name TEXT, --this == sign_up.fname
            category TEXT,
            photos BYTEA[],
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
            # if pic_query is None:
            #     pic_query = b""
            # else:
            #     pic_query = pic_query.encode('utf-8')
            encoded_image = base64.b64encode(pic_query[0] if pic_query else b"").decode('utf-8')

            named = html.escape(user["name"])
            menu_items = [
                f'<a class="nav-item nav-link" id="logout" href="/logout">Logout</a>',
                f"""
                <a href="/profile" class="link">
                    <p><span style="color: white;">Hola, {named}</span></p>
                    <img src="data:image/png;base64,{encoded_image}" class="rounded-circle me-2 ms-auto">
                </a>
                """
            ]
    return menu_items


def poster():
    cookie = request.cookies
    user_cookie = cookie.get("user")
    elements = {}
    if user_cookie is not None:
        user = deco(user_cookie)
        if user["role"] in ["admin", "Editor", "Administrador de inventario"]:
            elements["button"] = f"""
            </form>
                <form method="POST" enctype="multipart/form-data" ID="tbh">
                    <button type="submit" name="post" value="Upload" class="btn btn-primary">POSTER!</button>
                </form>
            """
        if user["role"] == "Editor":
            elements["ed_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="tbh">
                    <button type="submit" name="generic" value="editor" class="btn btn-primary">Editar</button>
                </form>
            """
        elif user["role"] == "Administrador de inventario":
            elements["ad_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="tbh">
                    <button type="submit" name="generic" value="adm_d_inv" class="btn btn-primary">Administrar</button>
                </form>
            """
        elif user["role"] == "admin":
            elements["fadmin_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="tbh">
                    <button type="submit" name="generic" value="full_admin" class="btn btn-primary">Ajustar</button>
                </form>
            """

    with entries.cursor() as cu:
        cu.execute("SELECT * FROM posts ORDER BY id")
        pasto = cu.fetchall()
        print(pasto)

        elements["squares"] = []
        for item in pasto:
            memories = [bytes(memory) for memory in item[6]]
            elements["squares"].append(memories)

        elements["img"] = [[base64.b64encode(element).decode('utf-8') for element in sublist] for sublist in
                           elements["squares"]]
        # for i in elements["img"]:
        #     for j in i:
        #        print(j[:10])
        # print("om"*70)
        # for i in elements["squares"]:
        #     for j in i:
        #        print(j[:10])
        # print("     ")
        # for i in pasto:
        #     print(i[7])
        elements["names"] = [item[0] for item in pasto]
        elements["price"] = [item[1] for item in pasto]
        elements["cuant"] = [item[2] for item in pasto]
        elements["desc"] = [item[3] for item in pasto]
        elements["owner"] = [item[4] for item in pasto]
        elements["cate"] = [item[5] for item in pasto]
        elements["id"] = [item[7] for item in pasto]

        # elements["squares"] = [item[7].strip('{"}').split(',')[0].replace('\\\\', '\\').strip('"') for item in
        #                        pasto]

    return elements


@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        if 'post' in request.form:
            return redirect(url_for('views.sell'))

    res = make_response(render_template("front.html", code=log_check(), poster=poster()))
    return res


@views.route("/posts/<num>", methods=['POST', 'GET'])
def posts(num):
    if request.method == "POST":
        cookie = request.cookies
        user_cookie = cookie.get("user")
        if user_cookie is not None:
            user = deco(user_cookie)
            print(request.form)
            if request.form.get('generic') in ["editor", 'full_admin', 'adm_d_inv']:
                return render_template("P_config.html",
                                       code=log_check(), poster=poster(),
                                       num=int(num) - 1, state=user["role"])

            if "subby" in request.form:
                # Editor
                if "quantity" not in request.form:
                    photos = request.files.getlist("photos")
                    pho_by = []
                    for photo in photos:
                        photo_bytes = photo.read()
                        pho_by.append(photo_bytes)
                    title = str(request.form.get("title"))
                    desc = str(request.form.get("desc"))
                    categoria = str(request.form.get("categoria"))

                    if not desc:
                        desc = '[No Description Available]'
                    if not title:
                        flash("Please enter a title", category="error")
                    elif len(title) < 2:
                        flash("That title is too small", category="error")
                    elif len(title) > 30:
                        flash("That title is too large", category="error")
                    elif len(desc) > 300:
                        flash("The description exceeded the limit of characters", category="error")
                    else:
                        try:
                            price = int(request.form.get("price"))
                        except:
                            flash("Please enter a price", category="error")
                            return render_template("P_config.html",
                                                   code=log_check(), poster=poster(),
                                                   num=int(num) - 1, state=user["role"])
                        if pho_by[0] is b'':
                            flash("Please enter one image as minimum", category="error")
                            return render_template("P_config.html",
                                                   code=log_check(), poster=poster(),
                                                   num=int(num) - 1, state=user["role"])
                        else:
                            for photo in pho_by:
                                if not photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[:4] == b'\x89PNG':
                                    flash("This type of files is not supported, please make sure to upload a PNG or JPEG file", category="error")
                                    return render_template("P_config.html",
                                                           code=log_check(), poster=poster(),
                                                           num=int(num) - 1, state=user["role"])
                        with entries:
                            with entries.cursor() as cu:
                                cu.execute("""
                                    UPDATE posts
                                    SET title = %s, price = %s, descrip = %s, category = %s, photos = (%s)
                                    WHERE id = %s;
                                """, (title, price, desc, categoria, (pho_by), int(num)))
                                flash("Entry successfully edited", category="success")
                                return render_template("products.html", code=log_check(), poster=poster(),
                                                       num=int(num) - 1)
                    return render_template("P_config.html",
                                           code=log_check(), poster=poster(),
                                           num=int(num) - 1, state=user["role"])
                # Administrador de inventario
                elif "title" not in request.form:
                    try:
                        quantity = int(request.form.get("quantity"))
                    except:
                        flash("Please enter the quantity of items to sell", category="error")
                        return render_template("P_config.html",
                                               code=log_check(), poster=poster(),
                                               num=int(num) - 1, state=user["role"])
                    with entries:
                        with entries.cursor() as cu:
                            cu.execute(""" 
                                UPDATE posts
                                SET quant = %s
                                WHERE id = %s;
                            """, (quantity, int(num)))
                # Admin
                else:
                    photos = request.files.getlist("photos")
                    pho_by = []
                    for photo in photos:
                        photo_bytes = photo.read()
                        pho_by.append(photo_bytes)
                    title = str(request.form.get("title"))
                    desc = str(request.form.get("desc"))
                    categoria = str(request.form.get("categoria"))

                    if not desc:
                        desc = '[No Description Available]'
                    if not title:
                        flash("Please enter a title", category="error")
                    elif len(title) < 2:
                        flash("That title is too small", category="error")
                    elif len(title) > 30:
                        flash("That title is too large", category="error")
                    elif len(desc) > 300:
                        flash("The description exceeded the limit of characters", category="error")
                    else:
                        try:
                            price = int(request.form.get("price"))
                        except:
                            flash("please enter a price", category="error")
                            return render_template("P_config.html",
                                                   code=log_check(), poster=poster(),
                                                   num=int(num) - 1, state=user["role"])

                        try:
                            quantity = int(request.form.get("quantity"))
                        except:
                            flash("please enter the quantity of items to sell", category="error")
                            return render_template("P_config.html",
                                                   code=log_check(), poster=poster(),
                                                   num=int(num) - 1, state=user["role"])
                        if pho_by[0] is b'':
                            flash("Please enter one image as minimum", category="error")
                            return render_template("P_config.html",
                                                   code=log_check(), poster=poster(),
                                                   num=int(num) - 1, state=user["role"])

                        else:
                            for photo in pho_by:
                                if not photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                                               :4] == b'\x89PNG':
                                    flash(
                                        "This type of files is not supported, please make sure to upload a PNG or JPEG file",
                                        category="error")
                                    return render_template("P_config.html",
                                                           code=log_check(), poster=poster(),
                                                           num=int(num) - 1, state=user["role"])

                        with entries:
                            with entries.cursor() as cu:
                                cu.execute("""
                                    UPDATE posts
                                    SET title = %s, quant = %s, price = %s, descrip = %s, category = %s, photos = (%s)
                                    WHERE id = %s;
                                """, (title, quantity, price, desc, categoria, (pho_by), int(num)))
                                return render_template("products.html", code=log_check(), poster=poster(),
                                                       num=int(num) - 1)
                    return render_template("P_config.html",
                                           code=log_check(), poster=poster(),
                                           num=int(num) - 1, state=user["role"])
            elif "del" in request.form:
                with entries:
                    with entries.cursor() as cu:
                        cu.execute("DELETE FROM posts WHERE id = %s;", (int(num),))
                        cu.execute("UPDATE posts SET id = id - 1 WHERE id > %s", (int(num),))
                        return redirect(url_for('views.home'))

    return render_template("products.html", code=log_check(), poster=poster(), num=int(num) - 1)


@views.route('/selling', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        cookie = request.cookies
        user_cookie = cookie.get("user")
        if user_cookie is not None:
            user = deco(user_cookie)
            photos = request.files.getlist("photos")
            pho_by = []
            for photo in photos:
                photo_bytes = photo.read()
                pho_by.append(photo_bytes)
            title = str(request.form.get("title"))

            desc = str(request.form.get("desc"))
            categoria = str(request.form.get("categoria"))
            if not desc:
                desc = '[No Description Available]'
            if not title:
                flash("Please enter a title", category="error")
            elif len(title) < 2:
                flash("That title is too small", category="error")
            elif len(title) > 30:
                flash("That title is too large", category="error")
            elif len(desc) > 300:
                flash("The description exceeded the limit of characters", category="error")
            else:
                try:
                    price = int(request.form.get("price"))
                except:
                    flash("please enter a price", category="error")
                    return render_template("sold.html", code=log_check())

                try:
                    quantity = int(request.form.get("quantity"))
                except:
                    flash("please enter the quantity of items to sell", category="error")
                    return render_template("sold.html", code=log_check())

                if pho_by[0] is b'':
                    flash("Please enter one image as minimum", category="error")
                    return render_template("sold.html", code=log_check())
                else:
                    for photo in pho_by:
                        if not (photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                                        :4] == b'\x89PNG'):
                            flash("This type of files is not supported, please make sure to upload a PNG or JPEG file",
                                  category="error")
                            return render_template("sold.html", code=log_check())

                with entries:
                    with entries.cursor() as cu:
                        cu.execute("INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, (%s));",
                                   (title, price, quantity, desc, user["name"], categoria, (pho_by)))
                flash("Entry successfully added", category="success")

    return render_template("sold.html", code=log_check())
