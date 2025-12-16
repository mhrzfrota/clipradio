from flask import Blueprint, request, jsonify
from app import db
from models.gravacao import Gravacao
from utils.jwt_utils import token_required, decode_token
from flask import request as flask_request
from services.recording_service import start_recording, stop_recording

bp = Blueprint('recording', __name__)

def get_user_ctx():
    token = flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token) or {}
    return {
        'user_id': payload.get('user_id'),
        'is_admin': payload.get('is_admin', False)
    }

@bp.route('/start', methods=['POST'])
@token_required
def start():
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    data = request.get_json()
    
    recording_id = data.get('recording_id')
    if not recording_id:
        return jsonify({'error': 'recording_id is required'}), 400
    
    gravacao = Gravacao.query.filter_by(id=recording_id).first() if is_admin else Gravacao.query.filter_by(id=recording_id, user_id=user_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    
    try:
        start_recording(gravacao)
        return jsonify({'message': 'Recording started', 'gravacao': gravacao.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/stop/<recording_id>', methods=['POST'])
@token_required
def stop(recording_id):
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    
    gravacao = Gravacao.query.filter_by(id=recording_id).first() if is_admin else Gravacao.query.filter_by(id=recording_id, user_id=user_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    
    try:
        stop_recording(gravacao)
        return jsonify({'message': 'Recording stopped', 'gravacao': gravacao.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/process-ai', methods=['POST'])
@token_required
def process_ai():
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    data = request.get_json()
    
    gravacao_id = data.get('gravacao_id')
    palavras_chave = data.get('palavras_chave', [])
    
    if not gravacao_id:
        return jsonify({'error': 'gravacao_id is required'}), 400
    
    gravacao = Gravacao.query.filter_by(id=gravacao_id).first() if is_admin else Gravacao.query.filter_by(id=gravacao_id, user_id=user_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    
    # Processar com IA (implementar em recording_service)
    from services.recording_service import process_audio_with_ai
    try:
        result = process_audio_with_ai(gravacao, palavras_chave)
        return jsonify({'message': 'Processing started', 'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
