# System operations
import os
from datetime import datetime

# Flask
from flask import Flask, redirect, render_template, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# SQLalchemy
from flask_sqlalchemy import SQLAlchemy

# Security
from werkzeug.security import check_password_hash, generate_password_hash

# View schema
from sqlalchemy import inspect
from sqlalchemy.sql import func

# json
import json


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Intiate SQLAlchemy
db = SQLAlchemy(app)

# Intiate LoginManager. Being used in replacement of sessions
login_manager = LoginManager(app)

# Will redirect any unauthorised users who try to access a route 
# decorated with @login_required to @app.route("/login")
login_manager.login_view = "login"

# Create User datebase tables
# UserMixin supplies features such as is_authenticated and get_id()
class User(db.Model, UserMixin):
    # __tablename defines the name of table when using SQLAlchemy
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    images = db.relationship('UserImage', back_populates='user')

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    images_for_users = db.relationship('UserImage', back_populates='image')

# Linking table for users and images
class UserImage(db.Model):
    __tablename__ = 'user_images'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))

    # Relationships back to the parent tables
    user = db.relationship('User', back_populates='images')
    image = db.relationship('Image', back_populates='images_for_users')

# JSON file based reading. Replaced with SQLAlchemy table.    
# def load_images():
#     with open("static/data/images.json", "r", encoding="utf-8") as file:
#         return json.load(file)

# The following function load the users id from User. 
# User.query.get(int(user_id)) is used to find the users id in User and stores the return in user_id
# Updated from User.query.get(int(user_id)) to db.session.get(User, int(user_id)) to meet SQL standards
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/api/images_html")
def get_images_html():
    images = Image.query.order_by(func.random()).limit(1).all()
    return render_template("partials/_image_cards.html", images=images)

# Direction to main page or "index.html"
@app.route("/")
def explore():
    images = Image.query.order_by(func.random()).limit(1).all()
    return render_template("index.html", images=images)


@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    errors = {}

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            errors["username"] = "Username is required"
        if not password:
            errors["password"] = "Password is required"

        # Query User for existing profile
        if not errors:
            user = User.query.filter_by(username=username).first()
            if not user or not check_password_hash(user.password, password):
                errors["invalid"] = "Invalid login"
            
        if errors:
            return render_template("login.html", errors=errors)
    
        login_user(user)
        return redirect("/")
    
    # Get method
    return render_template("login.html", errors=errors)
 

@app.route("/register", methods=["GET", "POST"])
def register():

    errors = {}

    if request.method == "POST":

        # Retrieve data from form
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Input field checks
        if not username:
            errors["username"] = "Username is required"
        if not email:
            errors["email"] = "Email is required"
        if not password:
            errors["password"] = "Password is requied"
        if not confirmation:
            confirmation["confirmation"] = "Confirm your password"
        elif password != confirmation:
            errors["confirmation"] = "Passwords do not match"

        # Check for existing data
        if not errors:
            existing_user = User.query.filter(User.username == username).first()
            existing_email = User.query.filter(User.email == email).first()
            if existing_user:
                errors["username"] = "Username already exists"
            if existing_email:
                errors["email"] = "Email already exists"
        
        # If error recall register with error codes
        if errors:
            return render_template("register.html", errors=errors)

        hashed_password = generate_password_hash(password)
        try:
            new_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            errors["general"] = f"An unexpected error occurred: {e}"
            return render_template("register.html", errors=errors)
        
        login_user(new_user)
        return redirect("/")
    
    # Get method return
    return render_template("register.html", errors=errors)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/schema", methods=["GET"])
# @login_required
def schema():
    users = User.query.all() 
    inspector = inspect(db.engine)
    schemas = {}
    for table_name in inspector.get_table_names():
        schemas[table_name] = inspector.get_columns(table_name)
    return render_template("schema.html", schemas=schemas, users=users)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Get form data
        title = request.form.get("title")
        description = request.form.get("description")
        image_url = request.form.get("image_url")

        new_image = Image(
            title=title,
            description=description,
            image_url=image_url
        )
        db.session.add(new_image)
        db.session.commit()

        return redirect("/admin")

    # Get method render
    users = User.query.all()
    images = Image.query.all()
    user_inspector = inspect(db.engine)
    user_schema = {}
    for i in user_inspector.get_table_names():
        user_schema[i] = user_inspector.get_columns(i)

    return render_template("admin.html", user_schema=user_schema, users=users, images=images)



if __name__ == "__main__":
    app.run(debug=True)