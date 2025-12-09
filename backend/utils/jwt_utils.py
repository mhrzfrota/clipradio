import jwt
from datetime import datetime, timedelta
from flask import current_app
from functools import wraps
from flask import request, jsonify

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token not provided'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated

