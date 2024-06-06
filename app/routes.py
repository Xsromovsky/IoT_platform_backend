from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, influxdb_client
from app.models import User, Device
from app.auth import token_required, refresh_token_required, SECRET_KEY, REFRESH_SECRET_KEY
from influxdb_client import Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.flux_table import FluxStructureEncoder
from app.utils.dev_token_generator import generate_api_token
import jwt
import datetime
import logging
import json

bp = Blueprint('routes', __name__)

@bp.route('/')
def home():
    return "Hello, world!"

@bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password_hash(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=50)
    }, SECRET_KEY)

    refresh_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }, REFRESH_SECRET_KEY)

    user.set_refresh_token(refresh_token)

    return jsonify({'access_token': access_token, 'refresh_token': refresh_token})

@bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'message': 'User already exists'}), 400

    user = User(username=username)
    
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/api/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': f'Hello, {current_user.username}! This is a protected route.'})

@bp.route('/api/refresh', methods=['POST'])
@refresh_token_required
def refresh_token(current_user):
    access_token = jwt.encode({
        'user_id': current_user.id,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=50)
    }, SECRET_KEY)

    return jsonify({'access_token': access_token}), 201


# INFLUX API

@bp.route('/api/add-device', methods=['POST'])
@token_required
def add_device(current_user):
    data = request.get_json()
    device_name = data.get('dev_name')
    device_token = generate_api_token()
    
    # if User.query.filter_by(username=username).first() is not None:
    #     return jsonify({'message': 'User already exists'}), 400
    
    if Device.query.filter_by(dev_name=device_name).first() is not None:
        return jsonify({'message': 'Device name already exists'}), 400
    
    device = Device(dev_name = device_name, dev_token = device_token, user_id = current_user.id)
    
    
    
    
    db.session.add(device)
    db.session.commit()
    
    return jsonify({'Message': 'Device added successfully', 'Device-Token': device_token}), 201
    
@bp.route('/api/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    devices = Device.query.filter_by(user_id=current_user.id).all()
    devices_list = [{'owner': current_user.username, 'device_id': device.dev_id, 'device_name': device.dev_name} for device in devices]
    return jsonify(devices_list), 200
    

# @bp.route('/api/data', methods=['POST'])
# @token_required
# def receive_data():
#     try:
#         data = request.get_json()
#         device_id = data.get('device_id')
#         timestamp = data.get('timestamp')
#         sensor_data = data.get('data') 
#         print("##################################")
#         print(f"{sensor_data}")
#         print("##################################")
#         write_api = influxdb_client.write_api(write_options=WriteOptions(batch_size=10, flush_interval=10000))

#         points = []
#         for sensor_name, sensor_value in sensor_data.items():
#             try:
#                 sensor_value = float(sensor_value) 
#             except ValueError:
#                 logging.error(f"Invalid data type for sensor {sensor_name} on device {device_id}. Skipping entry.")
#                 continue
#             point = Point("sensor_data") \
#                 .tag("device_id", device_id) \
#                 .field(f"{sensor_name}", sensor_value) \
#                 # .time(timestamp)
#             write_api.write(bucket='test', org='my_org', record=point)
#             # points.append(point)

        
#         return jsonify({'message': 'Data received'}), 200
#     except Exception as e:
#         logging.error(f"Error writing data to InfluxDB: {str(e)}")
#         return jsonify({'message': 'Error writing data to InfluxDB'}), 500
    
    
# @bp.route('/api/data/query', methods=['GET'])
# @token_required
# def query_device_data(current_user):
#     device_id = request.args.get('device_id')
#     start = request.args.get('start', '-1h')
#     stop = request.args.get('stop', datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z')
    
#     query_api = influxdb_client.query_api()
#     query = f'''
#         from(bucket: "test")
#         |> range(start: {start})
#         |> filter(fn: (r) => r["device_id"] == "{device_id}")
#         |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
#         |> sort(columns: ["_time"], desc: false)
#     '''
    
#     result = query_api.query(query=query, org='my_org')
#     output = json.dumps(result, cls=FluxStructureEncoder, indent=2)
#     data = json.loads(output)


#     return jsonify(data[0]['records']), 200