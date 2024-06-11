from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, influxdb_client
from app.models import User, Device
from app.auth import token_required, refresh_token_required, device_token_required, SECRET_KEY, REFRESH_SECRET_KEY
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
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
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
    device_type = data.get('device_type')
    device_token = generate_api_token()
    device_measurement = f"devices_{current_user.username}"

    if Device.query.filter_by(dev_name=device_name, user_id=current_user.id).first() is not None:
        return jsonify({'message': 'Device name already exists'}), 400

    device = Device(dev_name=device_name, dev_token=device_token,
                    dev_type=device_type, user_id=current_user.id, dev_measurement = device_measurement)
    db.session.add(device)
    db.session.commit()
    
    stored_device = Device.query.filter_by(dev_name=device_name, user_id=current_user.id).first()
    if stored_device is None:
        return jsonify({'message': 'Device is not available'}), 400
    
    
    write_api = influxdb_client.write_api(
        write_options=WriteOptions(batch_size=10, flush_interval=10000))

    point = Point(device_measurement) \
        .tag("device_name", device_name) \
        .tag("device_type", device_type) \
        .field("device_id", stored_device.dev_id) \

    write_api.write(bucket='test', org='my_org', record=point)
 
    return jsonify({'Message': 'Device added successfully', 'Device-Token': device_token}), 201

@bp.route('/api/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    devices = Device.query.filter_by(user_id=current_user.id).all()
    devices_list = [{'owner': current_user.username, 'device_id': device.dev_id,
                     'device_name': device.dev_name, 'device_type': device.dev_type, 'device_token': device.dev_token} for device in devices]
    return jsonify(devices_list), 200


@bp.route('/api/device/<int:device_id>', methods=['GET'])
@token_required
def get_device(current_user, device_id):
    device = Device.query.filter_by(
        dev_id=device_id, user_id=current_user.id).first()
    if not device:
        return jsonify({'Message': 'Device not found or not authorized'}), 404

    device_data = {
        'device_id': device.dev_id,
        'device_name': device.dev_name,
        'device_token': device.dev_token
    }
    return jsonify(device_data), 200


@bp.route('/api/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        device_name = data.get('device_name')
        device_type = data.get('device_type')
        device_token = request.headers.get('Authorization')
        sensor_data = data.get('data')
        
        device = Device.query.filter_by(dev_name=device_name, dev_token=device_token).first()

        if device is None:
            return jsonify({'message': 'Device name not exist or token is invalid'}), 400

        write_api = influxdb_client.write_api(
            write_options=WriteOptions(batch_size=10, flush_interval=10000))

        points = []
        for sensor_name, sensor_value in sensor_data.items():
            try:
                sensor_value = float(sensor_value)
            except ValueError:
                logging.error(
                    f"Invalid data type for sensor {sensor_name} on device {device_name}. Skipping entry.")
                continue
            point = Point(device.dev_measurement) \
                .tag("device_name", device_name) \
                .tag("device_type", device_type) \
                .field("device_id", device.dev_id) \
                .field(f"{sensor_name}", sensor_value) \
                # .time(timestamp)
            points.append(point)
        write_api.write(bucket='test', org='my_org', record=points)

        return jsonify({'message': 'Data received'}), 200
    except Exception as e:
        logging.error(f"Error writing data to InfluxDB: {str(e)}")
        return jsonify({'message': 'Error writing data to InfluxDB'}), 500


@bp.route('/api/data/query', methods=['GET'])
@token_required
def query_device_data(current_user):
    device_token = request.args.get('dev_token')
    start = request.args.get('start')
    # stop = request.args.get('stop', datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z')
    current_device = Device.query.filter_by(dev_token=device_token, user_id=current_user.id).first()
    if current_device is None:
        return jsonify({"message": "Device not exist"}), 400
    
    query_api = influxdb_client.query_api()
    query = f'''
        from(bucket: "test")
        |> range(start: {start})
        |> filter(fn: (r) => r["device_name"] == "{current_device.dev_name}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: false)
    '''

    result = query_api.query(query=query, org='my_org')
    output = json.dumps(result, cls=FluxStructureEncoder, indent=2)
    data = json.loads(output)

    return jsonify(data[0]['records']), 200


@bp.route('/api/delete/<int:device_id>', methods=['DELETE'])
@token_required
def delete_device(current_user, device_id):
    device = Device.query.filter_by(dev_id=device_id, user_id=current_user.id).first()
    
    if not device:
        return jsonify({"message": "Device not found or not authorized"}), 404
    
    try: 
        db.session.delete(device)
        db.session.commit()
        
        delete_device_influxdb = influxdb_client.delete_api()
        start = "1970-01-01T00:00:00Z"
        stop = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        predicate = f'device_name="{device.dev_name}"'
        delete_device_influxdb.delete(start, stop, predicate, 'test', 'my_org')
        
        # query_api = influxdb_client.query_api()
        # query = f'DROP SERIES FROM "devices" WHERE "device_name" = "dev_name1000"'
        # query_api.query(org='my_org', query=query)
        
        return jsonify({'message': "Device successfully deleted"}), 200
    except Exception as e:
        print(f"error: {e}")
        db.session.rollback()
        return jsonify({"message": "Error deleting device"}), 500
    
@bp.route('/api/influxdb/delete', methods=['DELETE'])
@token_required
def delete_all_series(current_user):
    delete_api = influxdb_client.delete_api()
    start = "1970-01-01T00:00:00Z"
    stop = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    try:
        
        query_api = influxdb_client.query_api()
        query = "DROP SERIES FROM 'devices'"
        delete_api.delete(start, stop, '_measurement="devicessss"', 'test', 'my_org')
        
        return jsonify({'message': "all series are dropped!"}), 200
    except Exception as e:
        print(f"error: {e}")
        return jsonify({'message': 'error dropping series'}), 500
    