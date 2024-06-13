import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://myuser:mypassword@localhost/my_flask_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    
    INFLUXDB_URL = os.getenv('INFLUXDB_URL')
    INFLUXDB_TOKEN = os.getenv('INFLUXDB_API_TOKEN')
    INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
    INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')
