import pymysql as mysql
import click
from flask import current_app, g

# DO NOT TOUCH THIS PYTHON CODE

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
            cursor.execute(statement)

        db.commit()


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)