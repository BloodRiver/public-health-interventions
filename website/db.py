import pymysql as mysql
import click
from flask import current_app, g
from hashlib import sha256
import json

# DO NOT TOUCH THIS PYTHON CODE

DB_HOST = 'localhost'
DB_USER = 'flask'
DB_USER_PASSWORD = 'test'
DB_NAME = 'flask'

def get_db():
    if 'db' not in g:
        g.db = mysql.connect(
            host='localhost',
            user='flask',
            password='test',
            database='flask'
        )

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cursor = db.cursor()
    with current_app.open_resource('schema.sql') as f:
        schema_sql = f.read().decode('utf8')

        for statement in schema_sql.split(";"):
            if (statement.strip()):
                cursor.execute(statement)

        db.commit()


def make_password(password):
    return sha256(password.encode()).hexdigest()

def create_admin_user(username, email, password):
    db = get_db()
    cursor = db.cursor()
    password_encrypted = str(make_password(password))
    address = {"country": "", "city": "", "area": ""}
    cursor.execute(f"""
        INSERT INTO user (user_id, username, email, phone_number, `password`, address, user_type) VALUES (NULL, "{username}", "{email}", "blank", "{password_encrypted}", '{json.dumps(address)}', "ADM");
    """)
    db.commit()


def drop_all_tables():
    global DB_NAME
    db = get_db()
    cursor = db.cursor()

    with current_app.open_resource("delete_schema.sql") as f:
        delete_schema_sql = f.read().decode('utf8')

        for statement in delete_schema_sql.split(";"):
            if (statement.strip()):
                cursor.execute(statement)
    db.commit()


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


@click.command('create-admin-user')
def create_admin_user_command():
    """Create an admin user"""
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    create_admin_user(username, email, password)
    click.echo("Admin user created successfully!")


@click.command("drop-all-tables")
def drop_all_tables_command():
    """Deletes all tables from the database"""

    print("WARNING. Running this command will delete ALL tables from the database along with all the data.\nThis action is IRREVERSIBLE\n")
    confirm = input("Are you sure you wish to continue? (y/n): ").lower()

    if (confirm == 'y'):
        drop_all_tables()
        click.echo("All tables have been deleted from database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_user_command)
    app.cli.add_command(drop_all_tables_command)