from app import db
from datetime import datetime
import uuid
import json

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('usuarios.id'), nullable=False, index=True)
    radio_id = db.Column(db.String(36), db.ForeignKey('radios.id'), nullable=False, index=True)
    data_inicio = db.Column(db.DateTime, nullable=False, index=True)
    duracao_minutos = db.Column(db.Integer, nullable=False)
    tipo_recorrencia = db.Column(db.String(50), default='none')  # none, daily, weekly, monthly
    dias_semana = db.Column(db.String(100))  # JSON array ou string separada por vírgula
    status = db.Column(db.String(50), default='agendado')  # agendado, concluido, em_execucao, erro, inativo
    palavras_chave = db.Column(db.Text)  # JSON array ou string separada por vírgula
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_dias_semana_list(self):
        """Retorna lista de dias da semana"""
        if not self.dias_semana:
            return []
        try:
            return json.loads(self.dias_semana)
        except:
            return [d.strip() for d in self.dias_semana.split(',') if d.strip()]
    
    def set_dias_semana_list(self, dias):
        """Define lista de dias da semana"""
        self.dias_semana = json.dumps(dias) if isinstance(dias, list) else dias
    
    def get_palavras_chave_list(self):
        """Retorna lista de palavras-chave"""
        if not self.palavras_chave:
            return []
        try:
            return json.loads(self.palavras_chave)
        except:
            return [p.strip() for p in self.palavras_chave.split(',') if p.strip()]
    
    def set_palavras_chave_list(self, palavras):
        """Define lista de palavras-chave"""
        self.palavras_chave = json.dumps(palavras) if isinstance(palavras, list) else palavras
    
    def to_dict(self, include_radio=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'radio_id': self.radio_id,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'duracao_minutos': self.duracao_minutos,
            'tipo_recorrencia': self.tipo_recorrencia,
            'dias_semana': self.get_dias_semana_list(),
            'status': self.status,
            'palavras_chave': self.get_palavras_chave_list(),
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
        
        if include_radio and self.radio:
            data['radios'] = {
                'nome': self.radio.nome
            }
        
        return data

