import base64
import html
import bleach
import jwt
import psycopg2
from flask import *
import re

from pagina import create_app

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
            owner_name TEXT, 
            category TEXT,
            photos BYTEA[],
            id INTEGER
            );""")
except:
    pass


def log_check():
    user_cookie = request.cookies.get("user")
    nav_option = []
    if user_cookie is not None:
        user = deco(user_cookie)
        if user is not None:
            with connection:
                with connection.cursor() as cu:
                    cu.execute("SELECT photo FROM sign_up WHERE fname = %s;", (user["name"],))
                    pic_query = cu.fetchone()

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
                """, " ", " ", " ", " "
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


def poster():
    user_cookie = request.cookies.get("user")

    elements = {}
    if user_cookie is not None:
        user = deco(user_cookie)
        if user["role"] in [ "Supervisor", "admin", "Editor", "Administrador de inventario"]:
            elements["button"] = f"""
            </form>
                <form method="POST" enctype="multipart/form-data" ID="btn_wrapper">
                    <button id="create_btn" type="submit" name="post" value="Upload">
                        <span id="adding"><span id="plus">+</span> Subir </span>
                    </button>
                </form>
            """
        if user["role"] == "Editor":
            elements["ed_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="btn_wrapper">
                    <button onclick='document.cookie = "check=exist; expires=Thu, 18 Dec 2024 12:00:00 UTC; path=/";' type="submit" name="generic" value="editor" class="btn btn-primary">
                    <svg id="icon_empty" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.539-18.073-22.002-12.074-37.538-25.543l-115.846 51.923-90.922-163.306 102.077-76.549q-1-8.299-1.885-20.135-.885-11.836-.885-21.7 0-8.612.885-19.641.885-11.029 1.885-22.129L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q52.876 0 89.784-36.866 36.907-36.866 36.907-89.684 0-52.817-36.907-89.825-36.908-37.007-89.784-37.007-52.692 0-89.691 36.866-37 36.866-37 89.684 0 52.817 37 89.825 36.999 37.007 89.691 37.007Zm-.618-58.384q-28.228 0-47.959-20.056-19.73-20.057-19.73-48.369 0-28.311 19.936-48.25 19.937-19.939 48.077-19.939 28.525 0 48.563 20.056 20.039 20.057 20.039 48.369 0 28.311-20.156 48.25-20.157 19.939-48.77 19.939ZM480-481Zm-42.846 338.615h85.52L537.096-255q32.596-8 60.586-23.931 27.99-15.931 54.499-41.146l103.28 45.231 40-70.847L704-413.923q4-17.406 6.807-33.964 2.808-16.558 2.808-33.259 0-17.469-2.5-32.815-2.5-15.346-6.115-33.346l91.23-68-39-70.847-105.615 44.231q-21.077-23.692-51.919-42.564-30.843-18.872-63.637-23.513l-12.213-110.615h-87.692l-12.231 110.231q-35.23 7.615-64.192 24.153-28.961 16.539-53.115 41.924l-102.564-43.847-41.282 70.847 91.461 67.846q-4.385 16.846-6.692 33.153-2.308 16.308-2.308 33.178 0 16.13 2.308 32.553 2.307 16.423 6.307 34.654l-91.076 68.23 41 70.847 103.461-44.847q26 26.385 54.654 42.231 28.654 15.846 61.654 23.846l13.615 111.231Z"/></svg>
                    <svg id="icon_full" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.731-18.346-22.192-12.346-37.346-25.27l-115.846 51.923-90.922-163.306 102.077-76.384q-1-8.539-1.885-20.5-.885-11.962-.885-21.5 0-8.154.885-19.616t1.885-22.154L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q53.076 0 89.884-36.807 36.807-36.808 36.807-89.884t-36.807-89.884q-36.808-36.807-89.884-36.807-52.692 0-89.691 36.807-37 36.808-37 89.884t37 89.884q36.999 36.807 89.691 36.807Z"/></svg>
                     <span>Editar</span></button>
                </form>
            """
        elif user["role"] == "Administrador de inventario":
            elements["ad_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="btn_wrapper">
                    <button onclick='document.cookie = "check=exist; expires=Thu, 18 Dec 2024 12:00:00 UTC; path=/";' type="submit" name="generic" value="adm_d_inv" class="btn btn-primary">
                    <svg id="icon_empty" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.539-18.073-22.002-12.074-37.538-25.543l-115.846 51.923-90.922-163.306 102.077-76.549q-1-8.299-1.885-20.135-.885-11.836-.885-21.7 0-8.612.885-19.641.885-11.029 1.885-22.129L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q52.876 0 89.784-36.866 36.907-36.866 36.907-89.684 0-52.817-36.907-89.825-36.908-37.007-89.784-37.007-52.692 0-89.691 36.866-37 36.866-37 89.684 0 52.817 37 89.825 36.999 37.007 89.691 37.007Zm-.618-58.384q-28.228 0-47.959-20.056-19.73-20.057-19.73-48.369 0-28.311 19.936-48.25 19.937-19.939 48.077-19.939 28.525 0 48.563 20.056 20.039 20.057 20.039 48.369 0 28.311-20.156 48.25-20.157 19.939-48.77 19.939ZM480-481Zm-42.846 338.615h85.52L537.096-255q32.596-8 60.586-23.931 27.99-15.931 54.499-41.146l103.28 45.231 40-70.847L704-413.923q4-17.406 6.807-33.964 2.808-16.558 2.808-33.259 0-17.469-2.5-32.815-2.5-15.346-6.115-33.346l91.23-68-39-70.847-105.615 44.231q-21.077-23.692-51.919-42.564-30.843-18.872-63.637-23.513l-12.213-110.615h-87.692l-12.231 110.231q-35.23 7.615-64.192 24.153-28.961 16.539-53.115 41.924l-102.564-43.847-41.282 70.847 91.461 67.846q-4.385 16.846-6.692 33.153-2.308 16.308-2.308 33.178 0 16.13 2.308 32.553 2.307 16.423 6.307 34.654l-91.076 68.23 41 70.847 103.461-44.847q26 26.385 54.654 42.231 28.654 15.846 61.654 23.846l13.615 111.231Z"/></svg>
                    <svg id="icon_full" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.731-18.346-22.192-12.346-37.346-25.27l-115.846 51.923-90.922-163.306 102.077-76.384q-1-8.539-1.885-20.5-.885-11.962-.885-21.5 0-8.154.885-19.616t1.885-22.154L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q53.076 0 89.884-36.807 36.807-36.808 36.807-89.884t-36.807-89.884q-36.808-36.807-89.884-36.807-52.692 0-89.691 36.807-37 36.808-37 89.884t37 89.884q36.999 36.807 89.691 36.807Z"/></svg>
                    <span>Administrar</span></button>
                </form>
            """
        elif user["role"] == "admin":
            elements["fadmin_btm"] = f"""
                <form method="POST" enctype="multipart/form-data" ID="btn_wrapper">
                    <button onclick='document.cookie = "check=exist; expires=Thu, 18 Dec 2024 12:00:00 UTC; path=/";' type="submit" name="generic" value="full_admin" class="btn btn-primary">
                    <svg id="icon_empty" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.539-18.073-22.002-12.074-37.538-25.543l-115.846 51.923-90.922-163.306 102.077-76.549q-1-8.299-1.885-20.135-.885-11.836-.885-21.7 0-8.612.885-19.641.885-11.029 1.885-22.129L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q52.876 0 89.784-36.866 36.907-36.866 36.907-89.684 0-52.817-36.907-89.825-36.908-37.007-89.784-37.007-52.692 0-89.691 36.866-37 36.866-37 89.684 0 52.817 37 89.825 36.999 37.007 89.691 37.007Zm-.618-58.384q-28.228 0-47.959-20.056-19.73-20.057-19.73-48.369 0-28.311 19.936-48.25 19.937-19.939 48.077-19.939 28.525 0 48.563 20.056 20.039 20.057 20.039 48.369 0 28.311-20.156 48.25-20.157 19.939-48.77 19.939ZM480-481Zm-42.846 338.615h85.52L537.096-255q32.596-8 60.586-23.931 27.99-15.931 54.499-41.146l103.28 45.231 40-70.847L704-413.923q4-17.406 6.807-33.964 2.808-16.558 2.808-33.259 0-17.469-2.5-32.815-2.5-15.346-6.115-33.346l91.23-68-39-70.847-105.615 44.231q-21.077-23.692-51.919-42.564-30.843-18.872-63.637-23.513l-12.213-110.615h-87.692l-12.231 110.231q-35.23 7.615-64.192 24.153-28.961 16.539-53.115 41.924l-102.564-43.847-41.282 70.847 91.461 67.846q-4.385 16.846-6.692 33.153-2.308 16.308-2.308 33.178 0 16.13 2.308 32.553 2.307 16.423 6.307 34.654l-91.076 68.23 41 70.847 103.461-44.847q26 26.385 54.654 42.231 28.654 15.846 61.654 23.846l13.615 111.231Z"/></svg>
                    <svg id="icon_full" xmlns="http://www.w3.org/2000/svg" height="48" viewBox="0 -960 960 960" width="48"><path d="m389.693-84.001-19.077-124.231q-17.538-6-39.731-18.346-22.192-12.346-37.346-25.27l-115.846 51.923-90.922-163.306 102.077-76.384q-1-8.539-1.885-20.5-.885-11.962-.885-21.5 0-8.154.885-19.616t1.885-22.154L86.771-599.154l90.922-161.152 113.461 51.154q16.308-12.924 38.231-25.578 21.924-12.654 40.847-19.038l19.461-123.231h181.614l18.077 123.615q20.077 7.154 41.154 19.231 21.077 12.077 36.769 25.001l116.384-51.154 90.538 161.152-105.615 76.308q1.769 10.923 2.962 22.5 1.192 11.577 1.192 20.346 0 8.385-1.385 19.654-1.384 11.269-1.769 21.962l103.23 75.153-90.922 163.306-116.615-52.307q-16.692 13.692-36.846 25.962-20.154 12.269-38.077 17.654L571.307-84.001H389.693Zm88.153-270.308q53.076 0 89.884-36.807 36.807-36.808 36.807-89.884t-36.807-89.884q-36.808-36.807-89.884-36.807-52.692 0-89.691 36.807-37 36.808-37 89.884t37 89.884q36.999 36.807 89.691 36.807Z"/></svg>
                     <span>Ajustar</span></button>
                </form>
            """

    with entries.cursor() as cu:
        cu.execute("SELECT * FROM posts ORDER BY id")
        produ = cu.fetchall()

        elements["squares"] = []
        for item in produ:
            memories = [bytes(memory) for memory in item[6]]
            elements["squares"].append(memories)

        elements["img"] = [[base64.b64encode(element).decode('utf-8') for element in sublist] for sublist in
                           elements["squares"]]

        elements["names"] = [item[0] for item in produ]
        elements["price"] = [item[1] for item in produ]
        elements["cuant"] = [item[2] for item in produ]
        elements["desc"] = [item[3] for item in produ]
        elements["owner"] = [item[4] for item in produ]
        elements["cate"] = [item[5] for item in produ]
        elements["id"] = [item[7] for item in produ]

        elements["unq_ow"] = list(set(elements["owner"]))
    return elements


@views.route('/', methods=['GET', 'POST'])
def home():

    if not request.cookies.get('check'):
        return render_template("lo_front.html")

    if request.method == "POST":
        if 'post' in request.form:
            return redirect(url_for('views.sell'))

    res = make_response(render_template("front.html", code=log_check(), poster=poster()))
    return res


@views.route("/assignment", methods=['POST', "GET"])
def assignment():
    user_cookie = request.cookies.get("user")
    user = deco(user_cookie)

    with connection:
        with connection.cursor() as cu:
            cu.execute("SELECT fname, rola FROM sign_up;")
            result = cu.fetchall()

    name_role_list = list(set([(name, role) for name, role in result]))

    names_not_admin = [f"{name} ({role})" for name, role in name_role_list if role != 'admin']
    names_roleless = [name for name, role in name_role_list if role != 'admin']
    lengthiest_combined = max([f"{name} ({role})" for name, role in name_role_list], key=len)
    result = (len(lengthiest_combined) - 12) // 2

    underscore = ''
    for i in range(result):
        underscore += '-'

    if request.method == "POST":
        role = request.form.get("role")
        changed_user = request.form.get("user")
        if (role != "------Seleccione un rol------" or None) and (changed_user != "--Seleccione un usuario--" or None):
            with connection:
                with connection.cursor() as cu:
                    cu.execute("""
                        UPDATE sign_up
                        SET rola = %s
                        WHERE fname = %s;
                    """, (role, changed_user))
            flash("Rol del usuario actualizado correctamente", category="success")

            return redirect(url_for('auth.profile'))
        else:
            flash("Por favor seleccione un usuario y un rol", category="error")

    if user_cookie is not None and user["role"] == "admin":
        return render_template("assignment.html", code=log_check(), non_admin_users=names_not_admin,
                               roleless=names_roleless, largest_name=underscore, result=result)
    else:
        abort(404)


@views.route("/posts/<num>", methods=['POST', 'GET'])
def posts(num):
    if int(num) < 1:
        num = "1"
    if not request.cookies.get('check'):
        return render_template("lo_posts.html")

    if request.method == "POST":
        if not request.cookies.get('cf_check'):
            return render_template("lo_config.html")

        poser = poster()
        for i in range(len(poser["desc"])):
            # This is what you see while in the editor
            poser["desc"][i] = poser["desc"][i].replace("<br>", "")
            poser["desc"][i] = poser["desc"][i].replace("</ul>\n", "</ul>\n\n")
            poser["desc"][i] = poser["desc"][i].replace("</ol>\n", "</ol>\n\n")
            poser["desc"][i] = poser["desc"][i].replace("<li>", "    <li>")
            poser["desc"][i] = poser["desc"][i].replace("</li></ol>", "</li>\n</ol>")
            poser["desc"][i] = poser["desc"][i].replace("</li></ul>", "</li>\n</ul>")
            poser["desc"][i] = poser["desc"][i].replace("<ul>    <li>", "<ul>\n    <li>")
            poser["desc"][i] = poser["desc"][i].replace("<ol>    <li>", "<ol>\n    <li>")
            poser["desc"][i] = poser["desc"][i].replace("</li>    <li>", "</li>\n    <li>")
            poser["desc"][i] = re.sub(r'</ol>(?![\n])', r'</ol>\n', poser["desc"][i])
            poser["desc"][i] = re.sub(r'</ul>(?![\n])', r'</ul>\n', poser["desc"][i])

        user_cookie = request.cookies.get("user")

        if user_cookie is not None:
            user = deco(user_cookie)

            # This takes out the current viewer, and the owner of the current product out of the list
            temp = []
            comparator = poser["unq_ow"]
            for instance in comparator:
                if poser["owner"][int(num) - 1] == instance:
                    temp.append(instance)
                elif user["name"] == instance:
                    temp.append(instance)

            poser["unq_ow"] = [item for item in comparator if item not in temp]

            # Give user to other returns
            if request.form.get('generic') in ["editor", 'full_admin', 'adm_d_inv']:
                return render_template("P_config.html",
                                       code=log_check(), poster=poser,
                                       num=int(num) - 1, state=user["role"], user=user)

            if "subby" in request.form:
                # Editor
                if "quantity" not in request.form:

                    pho_by, title, desc, category, owner = product_getter()
                    desc = markup_checker(poser, desc, num)

                    if not desc:
                        desc = poser["desc"][int(num) - 1]
                    if not title:
                        title = poser["names"][int(num) - 1]
                    if len(title) < 2:
                        flash("Ese título es demasiado pequeño", category="error")
                    elif len(title) > 30:
                        flash("Ese título es demasiado grande", category="error")
                    elif len(desc) > 1200:
                        flash("La descripción ha excedido el límite de caracteres", category="error")
                    else:
                        try:
                            price = int(request.form.get("price"))
                        except:
                            price = poser["price"][int(num) - 1]

                        if pho_by[0] == b'':
                            pho_by = img_empty(pho_by, poser, num)
                        else:
                            for photo in pho_by:
                                if not (photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                                                :4] == b'\x89PNG'):
                                    flash(
                                        "Este tipo de archivo no es compatible, asegúrate de subir un archivo PNG o JPEG",
                                        category="error")
                                    return render_template("P_config.html",
                                                           code=log_check(), poster=poser,
                                                           num=int(num) - 1, state=user["role"], user=user)

                        update(num, [("title", title), ("price", price), ("descrip", desc),
                                     ("category", category), ("owner_name", owner), ("photos", (pho_by))])
                        flash("Artículo correctamente editado", category="success")
                        return redirect(url_for('views.posts', num=num))

                    return render_template("P_config.html",
                                           code=log_check(), poster=poser,
                                           num=int(num) - 1, state=user["role"], user=user)
                # Administrador de inventario
                elif "title" not in request.form:
                    try:
                        quantity = int(request.form.get("quantity"))
                    except:
                        quantity = poser["cuant"][int(num) - 1]

                    update(num, [("quant", quantity)])
                    flash("Artículo correctamente administrado", category="success")

                # Admin
                else:
                    pho_by, title, desc, category, owner = product_getter()
                    desc = markup_checker(poser, desc, num)

                    if not title:
                        title = poser["names"][int(num) - 1]
                    if len(title) < 2:
                        flash("Ese título es demasiado corto", category="error")
                    elif len(title) > 30:
                        flash("Ese título es demasiado largo", category="error")
                    elif len(desc) > 1200:
                        flash("La descripción superó el límite de caracteres", category="error")
                    else:
                        try:
                            price = int(request.form.get("price"))
                        except:
                            price = poser["price"][int(num) - 1]
                        try:
                            quantity = int(request.form.get("quantity"))
                        except:
                            quantity = poser["cuant"][int(num) - 1]

                        if pho_by[0] == b'':
                            pho_by = img_empty(pho_by, poser, num)
                        else:
                            for photo in pho_by:
                                if not (photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                                                :4] == b'\x89PNG'):
                                    flash(
                                        "Este tipo de archivo no es compatible, asegúrate de subir un archivo PNG o JPEG",
                                        category="error")
                                    return render_template("P_config.html",
                                                           code=log_check(), poster=poser,
                                                           num=int(num) - 1, state=user["role"], user=user)
                        update(num, [("title", title), ("quant", quantity), ("price", price), ("descrip", desc),
                                     ("category", category), ("owner_name", owner), ("photos", (pho_by))])
                        flash("Artículo correctamente ajustado", category="success")
                        return redirect(url_for('views.posts', num=num))

                    return render_template("P_config.html",
                                           code=log_check(), poster=poser,
                                           num=int(num) - 1, state=user["role"], user=user)
            elif "del" in request.form:
                with entries:
                    with entries.cursor() as cu:
                        cu.execute("SELECT MAX(id) FROM posts;")
                        MAXIMUM = int(cu.fetchone()[0])

                    with entries.cursor() as cu:
                        cu.execute("DELETE FROM posts WHERE id = %s;", (int(num),))

                    for i in range(int(num)+1, MAXIMUM+1, 1):
                        try:
                            with entries.cursor() as cu:
                                cu.execute(f"UPDATE posts SET id = id - 1 WHERE id = {i}")
                        except:
                            pass

                    return redirect(url_for('views.home'))
    return render_template("products.html", code=log_check(), poster=poster(), num=int(num) - 1)


@views.route('/selling', methods=['GET', 'POST'])
def sell():
    user_cookie = request.cookies.get("user")
    if request.method == 'POST':
        if user_cookie is not None:
            user = deco(user_cookie)

            pho_by, title, desc, category, owner = product_getter()
            desc = desc.replace("\n", "<br />")
            desc = re.sub(r'<br />\s*<li>', '<li>', desc)
            desc = re.sub(r'</ol>\s*<br />', '</ol>', desc)
            desc = re.sub(r'</ul>\s*<br />', '</ul>', desc)

            desc = re.sub(r'</ol><br />', '</ol>', desc)
            desc = re.sub(r'</ul><br />', '</ul>', desc)

            desc = bleach.clean(desc, tags=['br', 'ul', 'ol', 'li'], strip=True)

            if not desc:
                desc = '[Descripción no disponible]'
            if not title:
                flash("Por favor ingresa un título", category="error")
            elif len(title) < 2:
                flash("Ese título es demasiado corto", category="error")
            elif len(title) > 30:
                flash("Ese título es demasiado largo", category="error")
            elif len(desc) > 1200:
                flash("La descripción excede el límite de caracteres", category="error")
            else:
                try:
                    price = int(request.form.get("price"))
                except:
                    flash("Por favor ingresa un precio", category="error")
                    return render_template("sold.html", code=log_check())

                try:
                    quantity = int(request.form.get("quantity"))
                except:
                    flash("Por favor ingresa la cantidad de artículos a vender", category="error")
                    return render_template("sold.html", code=log_check())

                if pho_by[0] == b'':
                    flash("Por favor ingresa al menos una imagen", category="error")
                    return render_template("sold.html", code=log_check())
                else:
                    for photo in pho_by:
                        if not (photo[:4] == b'\xff\xd8\xff\xe0' or photo[:4] == b'\xff\xd8\xff\xe1' or photo[
                                                                                                        :4] == b'\x89PNG'):
                            flash(
                                "No se admite este tipo de archivo, por favor asegúrate de subir un archivo PNG o JPEG",
                                category="error")
                            return render_template("sold.html", code=log_check())

                if "venta" in request.form:
                    with entries:
                        with entries.cursor() as cu:
                            cu.execute("SELECT MAX(id) FROM posts;")
                            MAXIMUM = cu.fetchone()[0]
                            if MAXIMUM is None:
                                MAXIMUM = 0
                            MAXIMUM = int(MAXIMUM) + 1
                        with entries.cursor() as cu:
                            cu.execute("INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, (%s), %s);",
                                       (title, price, quantity, desc, user["name"], category, (pho_by), MAXIMUM))
                    flash("Articulo añadido con éxito", category="success")

    if user_cookie is not None:
        return render_template("sold.html", code=log_check())
    else:
        abort(404)


def img_empty(pho_by, poser, num):
    for photo in poser["img"][int(num) - 1]:
        pho_by.append(base64.b64decode(photo))

    image_prior = pho_by[1:]
    if image_prior[0] != b'':
        pho_by = pho_by[1:]

    return pho_by


def update(num, element):
    sets = []
    values = []
    for x in element:
        sets.append(x[0])
        values.append(x[1])

    if not sets or not values:
        return

    set_clause = ", ".join(f"{column} = %s" for column in sets)

    sql_query = f"""
        UPDATE posts
        SET {set_clause}
        WHERE id = %s;
    """
    final_val = values + [int(num)]

    with entries:
        with entries.cursor() as cu:
            cu.execute(sql_query, tuple(final_val))


def product_getter():
    photos = request.files.getlist("photos")
    pho_by = []
    for photo in photos:
        photo_bytes = photo.read()
        pho_by.append(photo_bytes)
    title = str(request.form.get("title"))
    desc = str(request.form.get("desc"))

    category = str(request.form.get("categoria"))

    owner = str(request.form.get("owner"))

    return pho_by, title, desc, category, owner


def markup_checker(posers, descr, nums):
    # This is what you see while in the product page
    if not descr:
        descr = posers['desc'][int(nums) - 1]

    descr = descr.replace('</li>', '</li>\n')
    descr = descr.replace('\n', '<br />')

    descr = re.sub(r'<br />\s*<li>', '<li>', descr)
    descr = re.sub(r'</li>\s*<br />', '</li>', descr)

    descr = re.sub(r'</ul>\s*<br />', '</ul>', descr)
    descr = re.sub(r'</ol>\s*<br />', '</ol>', descr)

    descr = re.sub(r'</ul><br />', '</ul>', descr)
    descr = re.sub(r'</ol><br />', '</ol>', descr)

    descr = descr.replace(r'</ul><br />', '</ul>')
    descr = descr.replace(r'</ol><br />', '</ol>')

    descr = re.sub(r'</li>\s*<br /></ul>', '</li></ul>', descr)
    descr = re.sub(r'</li>\s*<br /></ol>', '</li></ol>', descr)

    descr = bleach.clean(descr, tags=['br', 'ul', 'ol', 'li', 'b', 'i', 'u'], strip=True)

    return descr
