# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from form import RecipeForm, RegistrationForm, LoginForm, DeleteRecipeForm
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define database models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    likes = db.Column(db.Integer, default=0)  # New field to store the number of likes
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='recipes', lazy=True)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of the LoginForm
    if form.validate_on_submit():  # Check if form is submitted and valid
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Check if user exists and password is correct
            login_user(user)  # Log in the user
            flash('Logged in successfully.', 'success')
            # Redirect to the index page where all recipes are displayed
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html', form=form)  # Pass the LoginForm object to the template


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create an instance of the RegistrationForm
    if form.validate_on_submit():  # Check if form is submitted and valid
        username = form.username.data
        email = form.email.data
        password = form.password.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))  # Redirect to register page if username already exists
        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Set the password for the new user
        db.session.add(new_user)  # Add the new user to the database
        db.session.commit()  # Commit changes to the database
        login_user(new_user)  # Log in the newly registered user
        flash('Account created successfully. Welcome!', 'success')
        return redirect(url_for('view_recipe'))  # Redirect to view_recipe page after successful registration
    return render_template('register.html', form=form)  # Pass the RegistrationForm object to the template

# Like Recipe
@app.route('/like_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def like_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Ensure likes is not None before incrementing
    if recipe.likes is None:
        recipe.likes = 0
    
    recipe.likes += 1
    db.session.commit()
    flash('You liked the recipe!', 'success')
    return redirect(url_for('view_recipe', recipe_id=recipe.id))

# View recipe
@app.route('/view_recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        likes_count = recipe.likes
        return render_template('view_recipe.html', recipe=recipe, likes_count=likes_count)
    else:
        # Handle case where recipe is not found
        return render_template('error.html', message='Recipe not found'), 404

# Add recipe# Add Recipe route
@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        ingredients = form.ingredients.data
        instructions = form.instructions.data

        # Process the ingredients and instructions input
        ingredients_list = [ingredient.strip() for ingredient in ingredients.split('\n') if ingredient.strip()]
        instructions_list = [instruction.strip() for instruction in instructions.split('\n') if instruction.strip()]

        # Check if an image file was uploaded
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                # Save the image file to the specified upload folder
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

        # Create a new Recipe instance with the form data
        new_recipe = Recipe(
            title=title,
            description=description,
            ingredients='\n'.join(ingredients_list),
            instructions='\n'.join(instructions_list),
            image=filename if 'filename' in locals() else None,
            user=current_user
        )

        # Add the new recipe to the database
        db.session.add(new_recipe)
        db.session.commit()

        # Flash a success message
        flash('Recipe added successfully!', 'success')

        # Redirect to the view_recipe page
        return redirect(url_for('view_recipe', recipe_id=new_recipe.id))

    # If the form is not submitted or is invalid, render the add_recipe template with the form
    return render_template('add_recipe.html', form=form)

# Edit Recipe

@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required  # Ensure that only logged-in users can access this route
def edit_recipe(recipe_id):
    # Retrieve the recipe from the database based on the provided recipe_id
    recipe = Recipe.query.get_or_404(recipe_id)

    # Check if the current user is the owner of the recipe
    if recipe.user != current_user:
        # If not, abort with a 403 Forbidden error
        abort(403)

    # Create a form instance and populate it with the recipe data
    form = RecipeForm(obj=recipe)

    if form.validate_on_submit():
        # Update the recipe data based on the form submission
        recipe.title = form.title.data
        recipe.description = form.description.data
        
        # Process the ingredients and instructions input
        ingredients_list = [ingredient.strip() for ingredient in form.ingredients.data.split('\n') if ingredient.strip()]
        instructions_list = [instruction.strip() for instruction in form.instructions.data.split('\n') if instruction.strip()]

        recipe.ingredients = '\n'.join(ingredients_list)
        recipe.instructions = '\n'.join(instructions_list)

        # Check if the 'keep_image' checkbox is checked
        if form.keep_image.data:
            # Keep the existing image
            pass
        else:
            # Check if an image file was uploaded
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename != '':
                    # Save the image file to the specified upload folder
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    # Update the image attribute of the recipe with the new filename
                    recipe.image = filename

        # Save the updated recipe to the database
        db.session.commit()

        # Redirect to the view_recipe page for the updated recipe
        return redirect(url_for('view_recipe', recipe_id=recipe.id))

    # If it's a GET request or the form is not valid, render the edit_recipe template
    return render_template('edit_recipe.html', form=form, recipe=recipe)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/search')
def search():
    query = request.args.get('query')  # Get the search query from the URL parameter
    # Query the database for recipes matching the query (e.g., by name)
    recipes = Recipe.query.filter(Recipe.title.ilike(f'%{query}%')).all()
    return render_template('search_results.html', recipes=recipes, query=query)

# Delette recipe

@app.route('/delete_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required  # Ensure that only logged-in users can access this route
def delete_recipe(recipe_id):
    # Retrieve the recipe from the database based on the provided recipe_id
    recipe = Recipe.query.get_or_404(recipe_id)

    # Check if the current user is the owner of the recipe
    if recipe.user != current_user:
        # If not, abort with a 403 Forbidden error
        abort(403)

    form = DeleteRecipeForm()  # Create an instance of the DeleteRecipeForm
    if request.method == 'POST' and form.validate_on_submit():
        # Delete the recipe from the database
        db.session.delete(recipe)
        db.session.commit()

        # Redirect to the index page or any other appropriate page
        flash('Recipe deleted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('delete.html', recipe=recipe, form=form)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

