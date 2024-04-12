# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import FileStorage

from form import RecipeForm, RegistrationForm, LoginForm, DeleteRecipeForm
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from sqlalchemy import desc
import secrets
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
    category = db.Column(db.String(100), nullable=True)  # Add the category column
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='recipes', lazy=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    recipes = Recipe.query.all()
    return render_template('index.html', recipes=recipes)

# Category
@app.route('/category/<category_name>')
def category(category_name):
    # Retrieve recipes for the category and order them by ID in descending order
    category_recipes = Recipe.query.filter_by(category=category_name).order_by(desc(Recipe.id)).all()
    return render_template('category.html', category_name=category_name, recipes=category_recipes)

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
        return redirect(url_for('index'))  # Redirect to view_recipe page after successful registration
    return render_template('register.html', form=form)  # Pass the RegistrationForm object to the template


# main dish
@app.route('/main_dish')
def main_dish():
    # Query the database for recipes with the 'cocktail' category
    recipes = Recipe.query.filter_by(category='main_dish').all()
    print("This is recipe:", recipes[1].image)
    # Debug logging
    app.logger.debug(f"Found {len(recipes)} main_dish recipes")

    # Render the cocktail.html template and pass the recipes
    return render_template('main_dish.html', recipes=recipes)

# Edit Recipe
@app.route('/edit_recipeonetime/<int:recipe_id>', methods=['GET'])
 
def edit_recipeonetime(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    recipe.image = 'paella.jpg'  # UPDATE THE IMAGE FILENAME
 
    db.session.commit()
       
    return redirect('/')
 


# veggies
@app.route('/vegetables')
def vegetables():
    # Query the database for recipes with the 'cocktail' category
    recipes = Recipe.query.filter_by(category='vegetables').all() 
    # Debug logging
    app.logger.debug(f"Found {len(recipes)} vegetables recipes")

    # Render the cocktail.html template and pass the recipes
    return render_template('vegetables.html', recipes=recipes)

# cocktail
@app.route('/cocktail')
def cocktail():
    # Query the database for recipes with the 'cocktail' category
    recipes = Recipe.query.filter_by(category='cocktail').all()

    # Debug logging
    app.logger.debug(f"Found {len(recipes)} cocktail recipes")

    # Render the cocktail.html template and pass the recipes
    return render_template('cocktail.html', recipes=recipes)

# Dessert
@app.route('/dessert')
def dessert():
    # Query the database for recipes with the 'dessert' category
    recipes = Recipe.query.filter_by(category='dessert').all()

    # Debug logging
    app.logger.debug(f"Found {len(recipes)} dessert recipes")

    # Render the dessert.html template and pass the recipes
    username = str(current_user.username) if current_user.is_authenticated else ''
    return render_template('dessert.html', recipes=recipes, username=username)




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




# ****************
@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        # HANDLE FILE UPLOAD
        image_filename = None
        if form.image.data:  # CHECK IF IMAGE DATA EXISTS
            image = form.image.data
            image_filename = save_image(image)  # SAVE THE IMAGE AND GET THE FILENAME
        
        # CREATE A NEW RECIPE OBJECT
        new_recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            image=image_filename,  # USE FILENAME INSTEAD OF FileStorage OBJECT
            likes=0,  # SET LIKES DEFAULT VALUE
            category=form.category.data.lower(),  # ENSURE CATEGORY IS LOWERCASE
            user_id=current_user.id
        )
        # ADD THE NEW RECIPE TO THE DATABASE
        db.session.add(new_recipe)
        db.session.commit()

        # REDIRECT TO THE APPROPRIATE CATEGORY PAGE
        return redirect(url_for('category', category_name=new_recipe.category))
    
    return render_template('add_recipe.html', form=form)


def save_image(image):
    if image and isinstance(image, FileStorage):  # Check if image is not None and is a FileStorage object
        # GENERATE A UNIQUE FILENAME FOR THE IMAGE
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(image.filename)
        image_fn = random_hex + f_ext
        # SAVE THE IMAGE TO THE UPLOADS FOLDER
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_fn)
        image.save(image_path)
        return image_fn
    return None

# Edit Recipe
# Edit Recipe
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if the current user is the owner of the recipe
    if recipe.user != current_user:
        flash('You are not authorized to edit this recipe.', 'error')
        return redirect(url_for('index'))  # Redirect the user back to the home page
    
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        # Update the recipe object with form data
        form.populate_obj(recipe)

        # Handle image upload if a new image is provided
        if form.image.data:
            image = form.image.data
            if isinstance(recipe.image, str):  # Check if recipe.image is a string (filename)
                # Delete the old image file if it exists
                delete_image(recipe.image)
            else:
                # Delete the old image file object if it exists
                delete_image(recipe.image.filename)
            image_filename = save_image(image)  # SAVE THE NEW IMAGE AND GET THE FILENAME
            recipe.image = image_filename  # UPDATE THE IMAGE FILENAME

        # Ensure category is lowercase
        if form.category.data:
            recipe.category = form.category.data.lower()
        
        db.session.commit()
        flash('Your recipe has been updated!', 'success')
        
        # Redirect to the appropriate page based on the new category
        if recipe.category == 'dessert':
            return redirect(url_for('dessert'))
        elif recipe.category == 'vegetables':
            return redirect(url_for('vegetables'))
        elif recipe.category == 'cocktail':
            return redirect(url_for('cocktail'))
        else:
            return redirect(url_for('index'))
    
    return render_template('edit_recipe.html', form=form)


def save_image(image):
    if image and isinstance(image, FileStorage):  # Check if image is not None and is a FileStorage object
        # GENERATE A UNIQUE FILENAME FOR THE IMAGE
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(image.filename)
        image_fn = random_hex + f_ext
        # SAVE THE IMAGE TO THE UPLOADS FOLDER
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_fn)
        image.save(image_path)
        return image_fn
    return None



def delete_image(filename):
    # DELETE THE IMAGE FILE
    if isinstance(filename, str):  # Check if filename is a string
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    else:
        # Log or handle the error if filename is not a string
        print("Error: Filename is not a string")




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

# Delete recipe
@app.route('/delete_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required  # Ensure that only logged-in users can access this route
def delete_recipe(recipe_id):
    # Retrieve the recipe from the database based on the provided recipe_id
    recipe = Recipe.query.get_or_404(recipe_id)

    # Check if the current user is the owner of the recipe
    if recipe.user != current_user:
        flash('You are not authorized to delete this recipe.', 'error')
        return redirect(url_for('index'))

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
