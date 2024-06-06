import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    INFLUXDB_URL = 'http://localhost:8086'
    INFLUXDB_TOKEN = 'qu3e311VmWj_fmscI2Rww_iXXIbZKHE6addFIDbHhnFzp6ibv0-xxh8Bn1lPod70Tz98rsBn97RFSTrfB0hyaA=='
    INFLUXDB_ORG = 'my_org'
    INFLUXDB_BUCKET = 'bucket'
    
