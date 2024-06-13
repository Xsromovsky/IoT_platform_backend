from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from influxdb_client import InfluxDBClient
import os

db = SQLAlchemy()
migrate = Migrate()
influxdb_client = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    
    global influxdb_client
    influxdb_client = InfluxDBClient(
        url=os.getenv('INFLUXDB_URL'),
        token=os.getenv('INFLUXDB_API_TOKEN'),
        org=os.getenv('INFLUXDB_ORG'),
    )

    with app.app_context():
        from app import models 
        db.create_all()

    from app.routes.device_routes import bp_device as device_routes_bp
    from app.routes.user_routes import bp_user as user_routes_bp
    app.register_blueprint(device_routes_bp, url_prefix='/api')
    app.register_blueprint(user_routes_bp, url_prefix='/api')

    return app
