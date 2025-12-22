from flask import Blueprint, request, jsonify
from app import db
from models.radio import Radio
from models.user import User
from utils.jwt_utils import token_required, decode_token
from flask import request as flask_request

bp = Blueprint('radios', __name__)

def get_user_ctx():
    token = flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token) or {}
    user_id = payload.get('user_id')
    is_admin = payload.get('is_admin', False)
    cidade = None
    estado = None
    if user_id and not is_admin:
        user = User.query.get(user_id)
        if user:
            cidade = user.cidade
            estado = user.estado
    return {
        'user_id': user_id,
        'is_admin': is_admin,
        'cidade': cidade,
        'estado': estado,
    }


def _radio_access_allowed(radio, ctx):
    if ctx.get('is_admin'):
        return True
    cidade = ctx.get('cidade')
    estado = ctx.get('estado')
    if cidade or estado:
        if cidade and (not radio.cidade or radio.cidade.lower() != cidade.lower()):
            return False
        if estado and (not radio.estado or radio.estado.upper() != estado.upper()):
            return False
        return True
    return radio.user_id == ctx.get('user_id')

ALLOWED_BITRATES = {96, 128}
ALLOWED_FORMATS = {'mp3', 'opus'}
ALLOWED_AUDIO_MODES = {'mono', 'stereo'}

def _sanitize_bitrate(value):
    try:
        ivalue = int(value)
        return ivalue if ivalue in ALLOWED_BITRATES else 128
    except Exception:
        return 128

def _sanitize_format(value):
    value = (value or '').lower()
    return value if value in ALLOWED_FORMATS else 'mp3'

def _sanitize_audio_mode(value):
    value = (value or '').lower()
    return value if value in ALLOWED_AUDIO_MODES else 'stereo'

@bp.route('', methods=['GET'])
@token_required
def get_radios():
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    cidade = ctx.get('cidade')
    estado = ctx.get('estado')

    query = Radio.query
    if not is_admin:
        if cidade or estado:
            if cidade:
                query = query.filter(db.func.lower(Radio.cidade) == cidade.lower())
            if estado:
                query = query.filter(db.func.upper(Radio.estado) == estado.upper())
        else:
            query = query.filter_by(user_id=user_id)
    radios = query.order_by(Radio.favorita.desc(), Radio.criado_em.desc()).all()
    return jsonify([radio.to_dict() for radio in radios]), 200

@bp.route('/<radio_id>', methods=['GET'])
@token_required
def get_radio(radio_id):
    ctx = get_user_ctx()
    is_admin = ctx.get('is_admin', False)
    radio = Radio.query.filter_by(id=radio_id).first()
    if not radio:
        return jsonify({'error': 'Radio not found'}), 404
    if not is_admin and not _radio_access_allowed(radio, ctx):
        return jsonify({'error': 'Radio not found'}), 404
    return jsonify(radio.to_dict()), 200

@bp.route('', methods=['POST'])
@token_required
def create_radio():
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    cidade_permitida = ctx.get('cidade')
    estado_permitido = ctx.get('estado')
    data = request.get_json()
    
    if not data.get('nome') or not data.get('stream_url'):
        return jsonify({'error': 'Nome and stream_url are required'}), 400

    if not ctx.get('is_admin') and (cidade_permitida or estado_permitido):
        if cidade_permitida:
            cidade_req = (data.get('cidade') or '').strip()
            if cidade_req and cidade_req.lower() != cidade_permitida.lower():
                return jsonify({'error': 'Cidade not allowed for this user'}), 403
            data['cidade'] = cidade_req or cidade_permitida
        if estado_permitido:
            estado_req = (data.get('estado') or '').strip().upper()
            if estado_req and estado_req != estado_permitido.upper():
                return jsonify({'error': 'Estado not allowed for this user'}), 403
            data['estado'] = estado_req or estado_permitido.upper()
    
    bitrate = _sanitize_bitrate(data.get('bitrate_kbps', 128))
    output_format = _sanitize_format(data.get('output_format', 'mp3'))
    audio_mode = _sanitize_audio_mode(data.get('audio_mode', 'stereo'))
    
    radio = Radio(
        user_id=user_id,
        nome=data['nome'],
        stream_url=data['stream_url'],
        cidade=data.get('cidade'),
        estado=data.get('estado'),
        favorita=data.get('favorita', False),
        bitrate_kbps=bitrate,
        output_format=output_format,
        audio_mode=audio_mode,
    )
    
    db.session.add(radio)
    db.session.commit()
    
    # Broadcast update via WebSocket
    from services.websocket_service import broadcast_update
    broadcast_update(f'user_{user_id}', 'radio_created', radio.to_dict())
    
    return jsonify(radio.to_dict()), 201

@bp.route('/<radio_id>', methods=['PUT'])
@token_required
def update_radio(radio_id):
    ctx = get_user_ctx()
    is_admin = ctx.get('is_admin', False)
    radio = Radio.query.filter_by(id=radio_id).first()
    if not radio:
        return jsonify({'error': 'Radio not found'}), 404
    if not is_admin and not _radio_access_allowed(radio, ctx):
        return jsonify({'error': 'Radio not found'}), 404
    
    data = request.get_json()
    if not is_admin and (ctx.get('cidade') or ctx.get('estado')):
        if 'cidade' in data and ctx.get('cidade'):
            cidade_req = (data.get('cidade') or '').strip()
            if cidade_req and cidade_req.lower() != ctx.get('cidade').lower():
                return jsonify({'error': 'Cidade not allowed for this user'}), 403
            data['cidade'] = ctx.get('cidade')
        if 'estado' in data and ctx.get('estado'):
            estado_req = (data.get('estado') or '').strip().upper()
            if estado_req and estado_req != ctx.get('estado').upper():
                return jsonify({'error': 'Estado not allowed for this user'}), 403
            data['estado'] = ctx.get('estado')
    if 'nome' in data:
        radio.nome = data['nome']
    if 'stream_url' in data:
        radio.stream_url = data['stream_url']
    if 'cidade' in data:
        radio.cidade = data['cidade']
    if 'estado' in data:
        radio.estado = data['estado']
    if 'favorita' in data:
        radio.favorita = data['favorita']
    if 'bitrate_kbps' in data:
        radio.bitrate_kbps = _sanitize_bitrate(data.get('bitrate_kbps'))
    if 'output_format' in data:
        radio.output_format = _sanitize_format(data.get('output_format'))
    if 'audio_mode' in data:
        radio.audio_mode = _sanitize_audio_mode(data.get('audio_mode'))
    
    db.session.commit()
    
    # Broadcast update
    from services.websocket_service import broadcast_update
    broadcast_update(f'user_{ctx.get("user_id")}', 'radio_updated', radio.to_dict())
    
    return jsonify(radio.to_dict()), 200

@bp.route('/<radio_id>', methods=['DELETE'])
@token_required
def delete_radio(radio_id):
    ctx = get_user_ctx()
    is_admin = ctx.get('is_admin', False)
    radio = Radio.query.filter_by(id=radio_id).first()
    if not radio:
        return jsonify({'error': 'Radio not found'}), 404
    if not is_admin and not _radio_access_allowed(radio, ctx):
        return jsonify({'error': 'Radio not found'}), 404
    
    db.session.delete(radio)
    db.session.commit()
    
    # Broadcast update
    from services.websocket_service import broadcast_update
    broadcast_update(f'user_{ctx.get("user_id")}', 'radio_deleted', {'id': radio_id})
    
    return jsonify({'message': 'Radio deleted'}), 200
