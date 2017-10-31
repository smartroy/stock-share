from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, IntegerField, FloatField, FormField
from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from flask_wtf.file import FileField, FileRequired, FileAllowed
from ..models import User, Role
from flask_login import current_user


class CreateForm(FlaskForm):
    submit = SubmitField('Create New')


class NewStockForm(FlaskForm):
    upc = IntegerField('UPC of Product')
    sku = StringField('SKU of Product')
    brand = StringField('Brand')
    name = TextAreaField('Product Name')
    price = FloatField('Stock Price')
    submit = SubmitField('Create')


class SellItemForm(FlaskForm):
    upc = IntegerField('UPC of Product')
    sku = StringField('SKU of Product')
    name = TextAreaField('Product Name')
    price = FloatField('Sell Price')
    count = IntegerField('Qty.')
    more = SubmitField('Add More')

    def reset_form(self):
        self.price = 0
        self.upc = 0
        self.name=None
        self.count = 0




class SellForm(FlaskForm):

    buyer = TextAreaField('Buyer Name')
    address = TextAreaField('Buyer Address')
    description = TextAreaField('Memo')
    # items = FormField(SellItemForm)
    submit = SubmitField('Create')
    cancel = SubmitField('Cancel')






class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')