from flask import Blueprint, send_file, jsonify, current_app
from utils.jwt_utils import token_required
import os

bp = Blueprint('files', __name__)

@bp.route('/audio/<filename>', methods=['GET'])
@token_required
def get_audio(filename):
    """Servir arquivo de áudio"""
    audio_path = os.path.join(current_app.config['STORAGE_PATH'], 'audio', filename)
    if not os.path.exists(audio_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(audio_path, mimetype='audio/mpeg')

@bp.route('/clips/<filename>', methods=['GET'])
@token_required
def get_clip(filename):
    """Servir arquivo de clipe"""
    clip_path = os.path.join(current_app.config['STORAGE_PATH'], 'clips', filename)
    if not os.path.exists(clip_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(clip_path, mimetype='audio/mpeg')

