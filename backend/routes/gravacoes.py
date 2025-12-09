from flask import Blueprint, request, jsonify
from app import db
from models.gravacao import Gravacao
from utils.jwt_utils import token_required, decode_token
from flask import request as flask_request
from datetime import datetime

bp = Blueprint('gravacoes', __name__)

def get_user_id():
    token = flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token)
    return payload['user_id'] if payload else None

@bp.route('', methods=['GET'])
@token_required
def get_gravacoes():
    user_id = get_user_id()
    query = Gravacao.query.filter_by(user_id=user_id)
    
    # Filtros
    radio_id = request.args.get('radio_id')
    if radio_id and radio_id != 'all':
        query = query.filter_by(radio_id=radio_id)
    
    # Filtro por data
    data_filter = request.args.get('data')
    if data_filter:
        try:
            start_date = datetime.strptime(data_filter, '%Y-%m-%d')
            end_date = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59)
            query = query.filter(Gravacao.criado_em >= start_date, Gravacao.criado_em <= end_date)
        except:
            pass
    
    # Filtro por cidade/estado (via join com radio)
    cidade = request.args.get('cidade')
    estado = request.args.get('estado')
    
    gravacoes = query.order_by(Gravacao.criado_em.desc()).all()
    
    # Aplicar filtros de cidade/estado após busca
    if cidade or estado:
        gravacoes = [g for g in gravacoes if g.radio and 
                     (not cidade or (g.radio.cidade and cidade.lower() in g.radio.cidade.lower())) and
                     (not estado or (g.radio.estado and estado.upper() == g.radio.estado.upper()))]
    
    return jsonify([g.to_dict(include_radio=True) for g in gravacoes]), 200

@bp.route('/<gravacao_id>', methods=['GET'])
@token_required
def get_gravacao(gravacao_id):
    user_id = get_user_id()
    gravacao = Gravacao.query.filter_by(id=gravacao_id, user_id=user_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    return jsonify(gravacao.to_dict(include_radio=True)), 200

@bp.route('/<gravacao_id>', methods=['DELETE'])
@token_required
def delete_gravacao(gravacao_id):
    user_id = get_user_id()
    gravacao = Gravacao.query.filter_by(id=gravacao_id, user_id=user_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    
    db.session.delete(gravacao)
    db.session.commit()
    
    # Broadcast update
    from services.websocket_service import broadcast_update
    broadcast_update(f'user_{user_id}', 'gravacao_deleted', {'id': gravacao_id})
    
    return jsonify({'message': 'Gravacao deleted'}), 200

@bp.route('/batch-delete', methods=['POST'])
@token_required
def batch_delete():
    user_id = get_user_id()
    data = request.get_json()
    gravacao_ids = data.get('gravacao_ids', [])
    
    if not gravacao_ids:
        return jsonify({'error': 'No gravacao IDs provided'}), 400
    
    gravacoes = Gravacao.query.filter(
        Gravacao.id.in_(gravacao_ids),
        Gravacao.user_id == user_id
    ).all()
    
    for gravacao in gravacoes:
        db.session.delete(gravacao)
    
    db.session.commit()
    
    # Broadcast update
    from services.websocket_service import broadcast_update
    broadcast_update(f'user_{user_id}', 'gravacoes_deleted', {'ids': gravacao_ids})
    
    return jsonify({'message': f'{len(gravacoes)} gravacoes deleted'}), 200

@bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    user_id = get_user_id()
    gravacoes = Gravacao.query.filter_by(user_id=user_id).all()
    
    total = len(gravacoes)
    total_duration = sum(g.duracao_segundos or 0 for g in gravacoes)
    total_size = sum(g.tamanho_mb or 0 for g in gravacoes)
    unique_radios = len(set(g.radio_id for g in gravacoes))
    
    return jsonify({
        'totalGravacoes': total,
        'totalDuration': total_duration,
        'totalSize': total_size,
        'uniqueRadios': unique_radios
    }), 200

