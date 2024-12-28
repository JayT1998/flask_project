import os
from datetime import datetime
from flask import Flask, redirect, render_template, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import inspect

# ========================================================================================================== #

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ========================================================================================================== #

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(Integer, primary_key=True)
    username = db.Column(String, unique=True, nullable=False)
    email = db.Column(String, unique=True, nullable=False)
    password = db.Column(String, nullable=False)
    role = db.Column(String, nullable=False, default='user')

    profile = db.relationship("Profile", uselist=False, back_populates="user")

class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    username = db.Column(String, nullable=False)

    user = db.relationship("User", back_populates="profile")
    games = db.relationship("Game", secondary='profile_games', back_populates="profiles")

# Association table for many-to-many relationship between Profiles and Games
game_genre_association = Table(
    'game_genre_association', db.metadata,
    Column('game_id', Integer, ForeignKey('games.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

# Association table for many-to-many relationship between Games and Developers
game_developer_association = Table(
    'game_developer_association', db.metadata,
    Column('game_id', Integer, ForeignKey('games.id'), primary_key=True),
    Column('developer_id', Integer, ForeignKey('developers.id'), primary_key=True)
)

# Association table for many-to-many relationship between Games and Platforms
game_platform_association = Table(
    'game_platform_association', db.metadata,
    Column('game_id', Integer, ForeignKey('games.id'), primary_key=True),
    Column('platform_id', Integer, ForeignKey('platforms.id'), primary_key=True)
)

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(Integer, primary_key=True)
    title = db.Column(String, nullable=False)
    description = db.Column(String, nullable=False)
    year = db.Column(Integer, nullable=False)

    genres = db.relationship("Genre", secondary=game_genre_association, back_populates="games")
    developers = db.relationship("Developer", secondary=game_developer_association, back_populates="games")
    platforms = db.relationship("Platform", secondary=game_platform_association, back_populates="games")
    profiles = db.relationship("Profile", secondary='profile_games', back_populates="games")

class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, unique=True, nullable=False)
    description = db.Column(String, nullable=True)

    games = db.relationship("Game", secondary=game_genre_association, back_populates="genres")

class Developer(db.Model):
    __tablename__ = 'developers'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, unique=True, nullable=False)

    games = db.relationship("Game", secondary=game_developer_association, back_populates="developers")

class Platform(db.Model):
    __tablename__ = 'platforms'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, unique=True, nullable=False)

    games = db.relationship("Game", secondary=game_platform_association, back_populates="platforms")

# Updated Profile Games Association
profile_games = Table(
    'profile_games', db.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id'), primary_key=True),
    Column('game_id', Integer, ForeignKey('games.id'), primary_key=True)
)

# ========================================================================================================== #

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/")
def explore():
    return render_template("index.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

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

            # creates new user in users
            new_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

            # creates new profile in profile
            new_profile = Profile(
                user_id=new_user.id,
                username=new_user.username
            )
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            errors["general"] = f"An unexpected error occurred: {e}"
            return render_template("register.html", errors=errors)
        
        login_user(new_user)
        return redirect("/")
    
    # Get method return
    return render_template("register.html", errors=errors)

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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Get form data
        title = request.form.get("title")
        description = request.form.get("description")
        image_url = request.form.get("image_url")
        genre = request.form.get("genre")

        # ipload new data to images table
        new_image = Game(
            title=title,
            description=description,
            image_url=image_url,
            genre=genre
        )
        db.session.add(new_image)
        db.session.commit()

        return redirect("/admin")

    # Get method render
    users = User.query.all()
    images = Game.query.all()
    user_inspector = inspect(db.engine)
    user_schema = {}
    for i in user_inspector.get_table_names():
        user_schema[i] = user_inspector.get_columns(i)

    return render_template("admin.html", user_schema=user_schema, users=users, images=images)


if __name__ == "__main__":
    app.run(debug=True)