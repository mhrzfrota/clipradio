from functools import wraps
from flask import jsonify, request
from utils.jwt_utils import decode_token

def get_user_id_from_token():
    """Extrai user_id do token JWT"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    payload = decode_token(token)
    return payload['user_id'] if payload else None

