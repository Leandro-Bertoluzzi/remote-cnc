from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from routes.userRoutes import userBlueprint
from routes.fileRoutes import fileBlueprint
from config import Config
from database.base import db

# Configurate app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask extensions here
db.init_app(app)

# Routes
app.register_blueprint(userBlueprint, url_prefix='/users')
app.register_blueprint(fileBlueprint, url_prefix='/files')

# Migrations controller
migrate = Migrate(app, db)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"