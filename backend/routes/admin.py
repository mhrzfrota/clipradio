from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import db
from models.user import User
from models.cliente import Cliente
from utils.jwt_utils import token_required, decode_token
from flask import request as flask_request

bp = Blueprint('admin', __name__)


def get_user_ctx():
    token = flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token) or {}
    return {
        'user_id': payload.get('user_id'),
        'is_admin': payload.get('is_admin', False),
    }


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'y', 'sim')
    return default


def _sanitize_text(value, max_len=255):
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_len] if text else None


def _sanitize_state(value):
    if value is None:
        return None
    text = str(value).strip().upper()
    return text[:2] if text else None


@bp.route('/users', methods=['GET'])
@token_required
def list_users():
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403
    users = User.query.order_by(User.criado_em.desc()).all()
    return jsonify([user.to_dict() for user in users]), 200


@bp.route('/users', methods=['POST'])
@token_required
def create_user():
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    raw_nome = data.get('nome')
    if isinstance(raw_nome, str) and raw_nome.strip():
        nome = raw_nome.strip()[:255]
    else:
        email_prefix = email.split('@')[0] if '@' in email else email
        nome = (email_prefix or 'Usuario').strip()[:255]

    cliente_id = data.get('cliente_id')
    if cliente_id:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Invalid cliente_id'}), 400

    user = User(
        email=email,
        nome=nome,
        ativo=_parse_bool(data.get('ativo'), True),
        is_admin=_parse_bool(data.get('is_admin'), False),
        cidade=_sanitize_text(data.get('cidade')),
        estado=_sanitize_state(data.get('estado')),
        cliente_id=cliente_id or None,
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 409
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while creating user")
        db.session.rollback()
        return jsonify({'error': 'Database error while creating user', 'detail': str(e)}), 500

    return jsonify(user.to_dict()), 201


@bp.route('/users/<user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    if 'email' in data:
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'error': 'Email cannot be empty'}), 400
        exists = User.query.filter(User.email == email, User.id != user.id).first()
        if exists:
            return jsonify({'error': 'Email already exists'}), 409
        user.email = email

    if 'nome' in data:
        user.nome = _sanitize_text(data.get('nome'))

    if 'ativo' in data:
        user.ativo = _parse_bool(data.get('ativo'), user.ativo)

    if 'is_admin' in data:
        user.is_admin = _parse_bool(data.get('is_admin'), user.is_admin)

    if 'cidade' in data:
        user.cidade = _sanitize_text(data.get('cidade'))

    if 'estado' in data:
        user.estado = _sanitize_state(data.get('estado'))

    if 'cliente_id' in data:
        cliente_id = data.get('cliente_id')
        if cliente_id:
            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                return jsonify({'error': 'Invalid cliente_id'}), 400
        user.cliente_id = cliente_id or None

    if 'password' in data:
        new_password = data.get('password') or ''
        if new_password:
            user.set_password(new_password)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already exists'}), 409
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while updating user")
        db.session.rollback()
        return jsonify({'error': 'Database error while updating user', 'detail': str(e)}), 500

    return jsonify(user.to_dict()), 200


@bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while deleting user")
        db.session.rollback()
        return jsonify({'error': 'Database error while deleting user', 'detail': str(e)}), 500

    return jsonify({'message': 'User deleted'}), 200


@bp.route('/clients', methods=['GET'])
@token_required
def list_clients():
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403
    clients = Cliente.query.order_by(Cliente.criado_em.desc()).all()
    return jsonify([client.to_dict() for client in clients]), 200


@bp.route('/clients', methods=['POST'])
@token_required
def create_client():
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    nome = _sanitize_text(data.get('nome'))
    if not nome:
        return jsonify({'error': 'nome is required'}), 400

    client = Cliente(
        nome=nome,
        cidade=_sanitize_text(data.get('cidade')),
        estado=_sanitize_state(data.get('estado')),
    )

    try:
        db.session.add(client)
        db.session.commit()
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while creating client")
        db.session.rollback()
        return jsonify({'error': 'Database error while creating client', 'detail': str(e)}), 500

    return jsonify(client.to_dict()), 201


@bp.route('/clients/<client_id>', methods=['PUT'])
@token_required
def update_client(client_id):
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    client = Cliente.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    data = request.get_json() or {}
    if 'nome' in data:
        nome = _sanitize_text(data.get('nome'))
        if not nome:
            return jsonify({'error': 'nome is required'}), 400
        client.nome = nome

    if 'cidade' in data:
        client.cidade = _sanitize_text(data.get('cidade'))

    if 'estado' in data:
        client.estado = _sanitize_state(data.get('estado'))

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while updating client")
        db.session.rollback()
        return jsonify({'error': 'Database error while updating client', 'detail': str(e)}), 500

    return jsonify(client.to_dict()), 200


@bp.route('/clients/<client_id>', methods=['DELETE'])
@token_required
def delete_client(client_id):
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    client = Cliente.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    try:
        db.session.delete(client)
        db.session.commit()
    except SQLAlchemyError as e:
        current_app.logger.exception("Database error while deleting client")
        db.session.rollback()
        return jsonify({'error': 'Database error while deleting client', 'detail': str(e)}), 500

    return jsonify({'message': 'Client deleted'}), 200
