from flask import Blueprint, request, jsonify
from app import db
from models.user import User
from utils.jwt_utils import create_token, token_required

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    user = User(email=data['email'], nome=data.get('nome'))
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    token = create_token(user.id)
    return jsonify({'user': user.to_dict(), 'token': token}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.ativo:
        return jsonify({'error': 'User inactive'}), 403
    
    token = create_token(user.id)
    return jsonify({'user': user.to_dict(), 'token': token}), 200

@bp.route('/me', methods=['GET'])
@token_required
def get_me():
    from utils.jwt_utils import decode_token
    from flask import request
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token)
    user_id = payload['user_id']
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    return jsonify({'message': 'Logged out'}), 200

