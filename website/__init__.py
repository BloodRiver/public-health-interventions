import os

from flask import Flask, render_template, request, session, redirect
from markupsafe import escape
from flask_ckeditor import CKEditor

ckeditor = CKEditor()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    ckeditor.init_app(app)
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
        mydb = db.get_db()
        cursor = mydb.cursor()
        cursor.execute("SELECT intervention_id, event_name, event_venue, event_details FROM intervention WHERE event_status='Upcoming' ORDER BY start_date LIMIT 3")
        latest_events = cursor.fetchall()
        cursor.execute("SELECT article_id, title, content FROM article WHERE article_type='B' ORDER BY date_published DESC LIMIT 3")
        blog_posts = cursor.fetchall()
        cursor.close()
        return render_template("index.html", latest_events=latest_events, blog_posts=blog_posts)
    
    @app.route("/login/", methods=('GET', 'POST'))
    def login():
        if request.method == 'GET':
            return render_template("login.html")

        if request.method == 'POST':
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
    
    @app.route("/dashboard/")
    @app.route("/dashboard")
    def dashboard():
        if request.method == "GET":
            if not session.get('user'):
                return redirect(app.url_for("login"))
            if request.url.rfind("?", 1) == -1:
                if session.get("user")['user_type'] == 'HCP':
                    return redirect(app.url_for("dashboard", page='blog_articles'))
                if session.get("user")['user_type'] == 'ADM':
                    return redirect(app.url_for("dashboard", page='faq_articles'))
                if session.get("user")['user_type'] == 'ORG' or session.get("user")['user_type'] == 'VOL':
                    return redirect(app.url_for("dashboard", page='intervention_events'))
            if request.url.endswith("?page=blog_articles"):
                if session.get("user")['user_type'] in ('HCP', 'ADM'):
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"SELECT article_id, title, date_published, content FROM article WHERE author_id={session.get('user')['user_id']} AND article_type='B' ORDER BY date_published DESC")
                    my_articles = cursor.fetchall()
                    return render_template("dashboard.html", my_articles=my_articles)
                else:
                    return "<h1>Page Not Found</h1>"
            elif request.url.endswith("?page=faq_articles"):
                if session.get("user")['user_type'] == 'ADM':
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"SELECT article_id, title, date_published, content FROM article WHERE author_id={session.get('user')['user_id']} AND article_type='F' ORDER BY date_published DESC")
                    my_articles = cursor.fetchall()
                    return render_template("dashboard.html", my_articles=my_articles)
                else:
                    return "<h1>Page Not Found</h1>"
            elif request.url.endswith('?page=intervention_events'):
                if session.get("user")['user_type'] in ('ORG', 'ADM'):
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"SELECT intervention_id, event_name, event_venue, start_date, end_date, event_details FROM intervention WHERE organizer_id={session.get('user')['user_id']} ORDER BY start_date DESC")
                    intervention_events = cursor.fetchall()
                    return render_template("dashboard.html", intervention_events=intervention_events)
                else:
                    return "<h1>Page Not Found</h1>"
            elif request.url.endswith('?page=intervention_reports'):
                if session.get("user")['user_type'] in ('ORG', 'ADM'):
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"""
                        SELECT 
                            intervention_report.report_id, user.username,
                            intervention_report.date_reported,
                            intervention_report.report_title,
                            intervention_report.report_content
                        FROM intervention_report, intervention, user
                        WHERE intervention_report.author_id=1
                                AND user.user_id=intervention_report.author_id 
                        ORDER BY intervention_report.date_reported DESC;
                    """)
                    intervention_reports = cursor.fetchall()
                    print(intervention_reports)
                    return render_template("dashboard.html", intervention_reports=intervention_reports)
                else:
                    return "<h1>Page Not Found</h1>"
            else:
                return "<h1>Page Not Found</h1>"

    
    return app