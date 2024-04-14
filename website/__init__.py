import os

from flask import Flask, render_template, request, session, redirect
from markupsafe import escape
from . import db as database


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db, models
    db.init_app(app)

    #--------------------------------------------------------------------------------------------
    # This is where the coding starts
    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/login/", methods=('GET', 'POST'))
    def login():
        if request.method == 'GET':
            return render_template("login.html")

        if request.method == 'POST':
            print(request.form)
            email = escape(request.form['email'])
            password = escape(request.form['password'])

            user = models.User.get_user_by_email(email)
            if user is None:
                return render_template("login.html", error="email", email=email)
            
            if user.check_password(password):
                session.update({'user': user.to_json()})

                return render_template("login_successful.html")
            else:
                return render_template("login.html", error="password", email=email)
    
    @app.route("/register/", methods=('GET', 'POST'))
    def register():
        if request.method == 'POST':
            username = escape(request.form['username'])
            email = escape(request.form['email'])
            phone_number = escape(request.form['phone_number'])
            password = escape(request.form['password'])
            user_type = "MEM"

            new_user = models.User(username, email, phone_number, user_type)

            country = escape(request.form['country'])
            city = escape(request.form['city'])
            area = escape(request.form['area'])
            new_user.set_address(
                country,
                city,
                area
            )

            new_user.set_password(password)

            try:
                new_user.save()
            except models.User.EmailAlreadyExists as ex:
                print(ex)
                return render_template(
                    "register.html",
                    error="email",
                    username=username,
                    email=email,
                    phone_number=phone_number,
                    country=country,
                    city=city,
                    area=area
                )
            except models.User.PhoneNumberAlreadyExists as ex:
                print(ex)
                return render_template("register.html", error="phone_number")
            else:
                return render_template("registration_successful.html")

        return render_template("register.html")
    
    @app.route("/logout/")
    def logout():
        if session['user']:
            session['user'] = None
        return redirect(app.url_for('index'))

    @app.route("/events/")
    @app.route("/events/<id>")
    def events(id=None):
        return render_template("events.html")
    
    @app.route("/blog/")
    @app.route("/blog/<id>")
    def blog(id=None):
        return render_template("blog.html")

    
    return app