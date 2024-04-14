from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

class ArticleForm(FlaskForm):
    title = StringField("Title")
    content = CKEditorField('Content', validators=[DataRequired])
