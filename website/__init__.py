import os
import stat
from flask import Flask, render_template, request, session, redirect, send_from_directory
from markupsafe import escape
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from datetime import datetime as dt
from PIL import Image

ckeditor = CKEditor()

BASE_DIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

os.makedirs(MEDIA_ROOT, exist_ok=True)
os.chmod(MEDIA_ROOT, stat.S_IRWXU)

def create_app(test_config=None):
    global MEDIA_ROOT
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    ckeditor.init_app(app)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        MEDIA_ROOT = MEDIA_ROOT
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
        cursor.execute("SELECT intervention_id, event_name, event_venue, event_details, thumbnail_image FROM intervention WHERE event_status='Upcoming' ORDER BY start_date LIMIT 3")
        latest_events = cursor.fetchall()
        cursor.execute("SELECT article_id, title, content, thumbnail_image FROM article WHERE article_type='B' ORDER BY date_published DESC LIMIT 3")
        blog_posts = cursor.fetchall()
        cursor.close()
        return render_template("index.html", latest_events=latest_events, blog_posts=blog_posts)
    
    @app.route("/login/", methods=('GET', 'POST'))
    def login():
        if request.method == 'GET':
            if session.get("user") is not None:
                return redirect(app.url_for("index"))

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
        return render_template("login.html")
    
    @app.route("/register/", methods=('GET', 'POST'))
    def register():
        if request.method == 'GET':
            if session.get("user") is not None:
                return redirect(app.url_for("index"))

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
    
    @app.route("/faq/")
    def faq():
        mydb = db.get_db()
        cursor = mydb.cursor()
        cursor.execute("SELECT title, content FROM article WHERE article_type = 'F' ORDER BY article.date_published DESC")

        all_articles = cursor.fetchall()
        cursor.close()
        return render_template("faq.html", all_articles=all_articles)

    @app.route("/events/")
    def events():
        mydb = db.get_db()
        cursor = mydb.cursor()
        cursor.execute(f"SELECT intervention_id, thumbnail_image, event_name, start_date, event_venue, event_details FROM intervention ORDER BY start_date DESC")
        all_events = cursor.fetchall()
        print(all_events)
        cursor.close()
        return render_template("events.html", all_events=all_events)
    @app.route("/events/<id>")
    def event_details(id):
        # if request.method == "GET":
        #     if not id:
        #         mydb = db.get_db()
        #         cursor = mydb.cursor()
        #         cursor.execute(f"SELECT intervention_id, thumbnail_image, event_name, start_date, event_venue, event_details FROM intervention ORDER BY start_date DESC")
        #         all_events = cursor.fetchall()
        #         print(all_events)
        #         cursor.close()
        return render_template("events.html")
    
    @app.route("/blog/")
    @app.route("/blog/<id>")
    def blog(id=None):
        if request.method == "GET":
            if not id:
                mydb = db.get_db()
                cursor = mydb.cursor()
                cursor.execute(f"SELECT article_id, title, date_published, content, thumbnail_image FROM article WHERE article_type='B' ORDER BY date_published DESC")
                all_articles = cursor.fetchall()
                print(all_articles)
                cursor.close()
        return render_template("blog.html", all_articles=all_articles)
    
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
                    cursor.execute(f"SELECT article_id, title, date_published, content, thumbnail_image FROM article WHERE author_id={session.get('user')['user_id']} AND article_type='B' ORDER BY date_published DESC")
                    my_articles = cursor.fetchall()
                    return render_template("dashboard.html", my_articles=my_articles)
                else:
                    return "<h1>Page Not Found</h1>"
            elif request.url.endswith("?page=faq_articles"):
                if session.get("user")['user_type'] == 'ADM':
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"SELECT article_id, title, date_published, content, thumbnail_image FROM article WHERE author_id={session.get('user')['user_id']} AND article_type='F' ORDER BY date_published DESC")
                    my_articles = cursor.fetchall()
                    return render_template("dashboard.html", my_articles=my_articles)
                else:
                    return "<h1>Page Not Found</h1>"
            elif request.url.endswith('?page=intervention_events'):
                if session.get("user")['user_type'] in ('ORG', 'ADM'):
                    mydb = db.get_db()
                    cursor = mydb.cursor()
                    cursor.execute(f"SELECT intervention_id, event_name, event_venue, start_date, end_date, event_details, thumbnail_image FROM intervention WHERE organizer_id={session.get('user')['user_id']} ORDER BY start_date DESC")
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
                            intervention_report.report_content,
                            intervention.thumbnail_image
                        FROM intervention_report, intervention, user
                        WHERE intervention_report.author_id=1
                                AND user.user_id=intervention_report.author_id
                                AND intervention_report.intervention_id=intervention.intervention_id 
                        ORDER BY intervention_report.date_reported DESC;
                    """)
                    intervention_reports = cursor.fetchall()
                    print(intervention_reports)
                    return render_template("dashboard.html", intervention_reports=intervention_reports)
                else:
                    return "<h1>Page Not Found</h1>"
            else:
                return "<h1>Page Not Found</h1>"

    @app.route("/create-article/", methods=("GET", "POST"))
    def create_article():
        if request.method == "GET":
            if session.get("user"):
                if session.get("user")['user_type'] in ('HCP', 'ADM'):
                    return render_template("create_edit_article.html")
            else:
                return redirect(app.url_for("login"))
            
        if request.method == "POST":
            if session.get("user"):
                if session.get("user")['user_type'] in ('HCP', 'ADM'):
                    title = escape(request.form['title'])
                    content = escape(request.form['content'])
                    article_type = request.form.get('article_type')
                    if not article_type:
                        article_type = 'B'
                    filename = None
                    if 'thumbnail_image' in request.files:
                        img = request.files['thumbnail_image']
                        if img:
                            image = Image.open(img)
                            filename = secure_filename(img.filename)
                            image.save(os.path.join(MEDIA_ROOT, filename))

                    mydb = db.get_db()
                    cursor = mydb.cursor()

                    if filename:
                        query = f"""
                            INSERT INTO article
                                (article_id, thumbnail_image, author_id, title, date_published, content, article_type)
                            VALUES
                                (NULL, '{filename}', {session.get('user')['user_id']}, '{title}', '{str(dt.today().date())}', '{content}', '{article_type}')
                        """
                    else:
                        query = f"""
                            INSERT INTO article
                                (article_id, thumbnail_image, author_id, title, date_published, content, article_type)
                            VALUES
                                (NULL, NULL, {session.get('user')['user_id']}, '{title}', '{str(dt.today().date())}', '{content}', '{article_type}')
                        """
                    print(query)
                    cursor.execute(query)
                    mydb.commit()
                    cursor.close()
                    return redirect(app.url_for("create_article_success"))
                
    @app.route("/create-article-success/")
    def create_article_success():
        if request.method == "GET":
            if session.get("user"):
                if session.get("user")['user_type'] in ('ORG', 'ADM'):
                    return render_template("create_article_success.html")
                
    @app.route("/images/<filename>")
    def images(filename):
        return send_from_directory(MEDIA_ROOT, filename)
    
    @app.route("/create-intervention-event/", methods=("GET", "POST"))
    def create_intervention_event():
        if request.method == "GET":
            if session.get("user"):
                if session.get("user")['user_type'] in ('ORG', 'ADM'):
                    return render_template("create_edit_intervention.html")
            else:
                return redirect(app.url_for("login"))
        if request.method == "POST":
            event_name = escape(request.form['event_name'])
            start_date = escape(request.form['start_date'])
            end_date = escape(request.form['end_date'])
            event_venue = escape(request.form['event_venue'])
            event_details = escape(request.form['event_details'])

            filename = None
            if 'thumbnail_image' in request.files:
                img = request.files['thumbnail_image']
                if img:
                    image = Image.open(img)
                    filename = secure_filename(img.filename)
                    image.save(os.path.join(MEDIA_ROOT, filename))
            mydb = db.get_db()
            cursor = mydb.cursor()

            if filename:
                query = f"""
                    INSERT INTO intervention
                        (intervention_id, thumbnail_image, organizer_id, start_date, end_date, event_name, event_venue, event_details, event_status)
                    VALUES
                        (NULL, '{filename}', {session.get("user")['user_id']}, '{start_date}', '{end_date}', '{event_name}', '{event_venue}', '{event_details}', 'Upcoming')
                """
            else:
                query = f"""
                    INSERT INTO intervention
                        (intervention_id, thumbnail_image, organizer_id, start_date, end_date, event_name, event_venue, event_details, event_status)
                    VALUES
                        (NULL, NULL, {session.get("user")['user_type']}, '{start_date}', '{end_date}', '{event_name}', '{event_venue}', '{event_details}', 'Upcoming')
                """

            cursor.execute(query)

            mydb.commit()
            cursor.close()
            return redirect(app.url_for('create_intervention_success'))

            
        return render_template("create_edit_intervention.html")
    
    @app.route("/create-intervention-success/")
    def create_intervention_success():
        return render_template("create_intervention_success.html")

    @app.route("/create-intervention-report/", methods=("GET", "POST"))
    def create_intervention_report():
        if request.method == "GET":
            if not session.get("user"):
                return redirect(app.url_for("login"))
            if not session.get("user")['user_type'] in ('ORG', 'ADM'):
                return "<h1>Page Not Found</h1>"

            mydb = db.get_db()
            cursor = mydb.cursor()

            cursor.execute(f"""
                SELECT intervention_id, event_name FROM intervention WHERE organizer_id = {session.get("user")['user_id']}
            """)
            interventions = cursor.fetchall()
            cursor.close()

            return render_template("create_edit_intervention_report.html", interventions=interventions)
        
        if request.method == "POST":
            if not session.get("user"):
                return redirect(app.url_for("login"))
            if not session.get("user")["user_type"] in ('ORG', 'ADM'):
                return "<h1>Page Not Found</h1>"
            
            mydb = db.get_db()
            cursor = mydb.cursor()

            intervention_id = escape(request.form['intervention_id'])
            report_title = escape(request.form['report_title'])
            date_reported = escape(request.form['date_reported'])
            report_content = escape(request.form['report_content'])

            cursor.execute(f"""
                INSERT INTO intervention_report
                    (report_id, author_id, intervention_id, date_reported, report_title, report_content)
                VALUES
                    (NULL, {session.get("user")['user_id']}, {intervention_id}, '{date_reported}', '{report_title}', '{report_content}')
            """)

            mydb.commit()
            cursor.close()

            return render_template("create_intervention_report_success.html")

    return app