# form.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()], render_kw={"class": "custom-textarea"})  
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    keep_image = BooleanField('Keep Existing Image')  


    def custom_validator(self, field):
        if field.data is not None and not field.data.startswith('example'):
            raise ValidationError('Field must start with "example".')

    my_field = StringField('My Field', validators=[custom_validator])


    # def validate(self):
    #     if not super().validate():
    #         return False
        
    #     if not self.ingredients.data.strip() or not self.instructions.data.strip():
    #         self.ingredients.errors.append('Ingredients cannot be empty.')
    #         self.instructions.errors.append('Instructions cannot be empty.')
    #         return False

    #     return True
    
    # def validate_title(self, title):
    #     if title.data == 'Some Condition':
    #         raise ValidationError('Your error message goes here.')

    submit = SubmitField('Save Changes')

class DeleteRecipeForm(FlaskForm):
     submit = SubmitField('Delete')