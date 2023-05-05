import base64
import html
from flask import *  # fix this later
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .auth import SignUp
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


def log_check():
    try:
        cookie = request.cookies
        user_cookie = cookie.get("user")
        menu_items = []
    except jwt.exceptions.DecodeError:
        return {}

    if user_cookie is not None:
        user = deco(user_cookie)
        if user is not None:
            pic_query = session.query(SignUp.photo).filter_by(name=user["name"]).first()





            encoded_image = base64.b64encode(pic_query[0] if pic_query else None).decode('utf-8')
            named = html.escape(user["name"])
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


@views.route('/', methods=['GET', 'POST'])
def home():

    # s = session.query(SignUp).filter(SignUp.emails == "luisjaviercg9@gmail.com").first()
    res = make_response(render_template("front.html", code=log_check()))
    return res

