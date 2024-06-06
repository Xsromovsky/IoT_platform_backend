from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from influxdb_client import InfluxDBClient

db = SQLAlchemy()
influxdb_client = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    
    global influxdb_client
    influxdb_client = InfluxDBClient(
        url=app.config['INFLUXDB_URL'],
        token=app.config['INFLUXDB_TOKEN'],
        org=app.config['INFLUXDB_ORG'],
    )

    with app.app_context():
        from app import models 
        db.create_all()

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
