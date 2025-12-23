from flask import Blueprint, request, jsonify
from app import db
from models.gravacao import Gravacao
from models.agendamento import Agendamento
from models.radio import Radio
from models.user import User
from utils.jwt_utils import token_required, decode_token
from flask import request as flask_request
from datetime import datetime
from sqlalchemy import desc
from services.recording_service import hydrate_gravacao_metadata

bp = Blueprint('gravacoes', __name__)

def get_user_ctx():
    token = flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = decode_token(token) or {}
    return {
        'user_id': payload.get('user_id'),
        'is_admin': payload.get('is_admin', False),
    }

def _gravacao_access_allowed(gravacao, ctx):
    return bool(ctx.get('is_admin') or gravacao.user_id == ctx.get('user_id'))

@bp.route('', methods=['POST'])
@token_required
def create_gravacao():
    """Cria um registro de gravação para o usuário autenticado"""
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    data = request.get_json() or {}

    radio_id = data.get('radio_id')
    if not radio_id:
        return jsonify({'error': 'radio_id is required'}), 400


    gravacao = Gravacao(
        user_id=user_id,
        radio_id=radio_id,
        status=data.get('status', 'iniciando'),
        tipo=data.get('tipo', 'manual'),
        duracao_minutos=data.get('duracao_minutos', 0),
        duracao_segundos=data.get('duracao_segundos', 0),
        tamanho_mb=data.get('tamanho_mb', 0.0),
        batch_id=data.get('batch_id')
    )

    db.session.add(gravacao)
    db.session.commit()

    return jsonify(gravacao.to_dict(include_radio=True)), 201

@bp.route('', methods=['GET'])
@token_required
def get_gravacoes():
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    include_stats = (request.args.get('include_stats') or '').lower() == 'true'
    query = Gravacao.query
    if not is_admin:
        query = query.filter_by(user_id=user_id)

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
    
    # Enriquecer metadados com dados reais do arquivo (duração, tamanho, status)
    gravacoes = [hydrate_gravacao_metadata(g, autocommit=True) for g in gravacoes]

    payload = [g.to_dict(include_radio=True) for g in gravacoes]

    if include_stats:
        stats = {
            'totalGravacoes': len(gravacoes),
            'totalDuration': sum((g.duracao_segundos or 0) or ((g.duracao_minutos or 0) * 60) for g in gravacoes),
            'totalSize': sum(g.tamanho_mb or 0 for g in gravacoes),
            'uniqueRadios': len(set(g.radio_id for g in gravacoes)),
        }
        return jsonify({'items': payload, 'stats': stats}), 200

    return jsonify(payload), 200


@bp.route('/ongoing', methods=['GET'])
@token_required
def get_ongoing():
    """Retorna gravações em andamento (gravando/iniciando/processando). Admin vê todas."""
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    query = Gravacao.query.filter(Gravacao.status.in_(('iniciando', 'gravando', 'processando')))
    if not is_admin:
        query = query.filter_by(user_id=user_id)


    gravacoes = query.order_by(Gravacao.criado_em.desc()).all()
    gravacoes = [hydrate_gravacao_metadata(g, autocommit=True) for g in gravacoes]
    return jsonify([g.to_dict(include_radio=True) for g in gravacoes]), 200

@bp.route('/<gravacao_id>', methods=['GET'])
@token_required
def get_gravacao(gravacao_id):
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    gravacao = Gravacao.query.filter_by(id=gravacao_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    if not is_admin and not _gravacao_access_allowed(gravacao, ctx):
        return jsonify({'error': 'Gravacao not found'}), 404
    gravacao = hydrate_gravacao_metadata(gravacao, autocommit=True)
    return jsonify(gravacao.to_dict(include_radio=True)), 200

@bp.route('/<gravacao_id>', methods=['DELETE'])
@token_required
def delete_gravacao(gravacao_id):
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    gravacao = Gravacao.query.filter_by(id=gravacao_id).first()
    if not gravacao:
        return jsonify({'error': 'Gravacao not found'}), 404
    if not is_admin and not _gravacao_access_allowed(gravacao, ctx):
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
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    data = request.get_json()
    gravacao_ids = data.get('gravacao_ids', [])
    
    if not gravacao_ids:
        return jsonify({'error': 'No gravacao IDs provided'}), 400
    
    gravacoes = Gravacao.query.filter(Gravacao.id.in_(gravacao_ids))
    if not is_admin:
        gravacoes = gravacoes.filter(Gravacao.user_id == user_id)

    gravacoes = gravacoes.all()
    
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
    ctx = get_user_ctx()
    user_id = ctx.get('user_id')
    is_admin = ctx.get('is_admin', False)
    if is_admin:
        gravacoes = Gravacao.query.all()
    else:
        gravacoes = Gravacao.query.filter_by(user_id=user_id).all()


    # Garantir que duração/tamanho reflitam o arquivo salvo
    gravacoes = [hydrate_gravacao_metadata(g, autocommit=True) for g in gravacoes]
    
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


@bp.route('/admin/quick-stats', methods=['GET'])
@token_required
def admin_quick_stats():
    """Retorna indicadores rápidos para admins."""
    ctx = get_user_ctx()
    if not ctx.get('is_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    # Base de gravações válidas (ignora erros)
    duration_expr = db.func.coalesce(Gravacao.duracao_segundos, Gravacao.duracao_minutos * 60)
    base_grav = Gravacao.query.filter(Gravacao.status != 'erro')

    total_duration_seconds = (
        base_grav.with_entities(db.func.coalesce(db.func.sum(duration_expr), 0)).scalar() or 0
    )
    total_users = db.session.query(User).count()

    # Usuário que mais agendou
    top_scheduler_row = (
        db.session.query(Agendamento.user_id, db.func.count(Agendamento.id).label('total'))
        .group_by(Agendamento.user_id)
        .order_by(desc('total'))
        .first()
    )
    top_scheduler = None
    if top_scheduler_row:
        user = User.query.get(top_scheduler_row.user_id)
        if user:
            top_scheduler = {
                'id': user.id,
                'nome': user.nome or user.email,
                'email': user.email,
                'total_agendamentos': int(top_scheduler_row.total or 0),
            }

    # Rádio com mais tempo gravado
    top_radio_row = (
        base_grav.with_entities(
            Gravacao.radio_id,
            db.func.coalesce(db.func.sum(duration_expr), 0).label('total_dur')
        )
        .group_by(Gravacao.radio_id)
        .order_by(desc('total_dur'))
        .first()
    )
    top_radio = None
    if top_radio_row:
        radio = Radio.query.get(top_radio_row.radio_id)
        if radio:
            top_radio = {
                'id': radio.id,
                'nome': radio.nome,
                'total_duration_seconds': int(top_radio_row.total_dur or 0),
            }

    return jsonify({
        'total_duration_seconds': int(total_duration_seconds),
        'total_duration_hours': round((total_duration_seconds or 0) / 3600, 2),
        'total_users': total_users,
        'top_scheduler': top_scheduler,
        'top_radio': top_radio,
    }), 200
