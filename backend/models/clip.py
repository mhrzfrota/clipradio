from app import db
from datetime import datetime
import uuid

class Clip(db.Model):
    __tablename__ = 'clips'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gravacao_id = db.Column(db.String(36), db.ForeignKey('gravacoes.id'), nullable=False, index=True)
    palavra_chave = db.Column(db.String(255), nullable=False)
    inicio_segundos = db.Column(db.Integer, nullable=False)
    fim_segundos = db.Column(db.Integer, nullable=False)
    arquivo_url = db.Column(db.String(500))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'gravacao_id': self.gravacao_id,
            'palavra_chave': self.palavra_chave,
            'inicio_segundos': self.inicio_segundos,
            'fim_segundos': self.fim_segundos,
            'arquivo_url': self.arquivo_url,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

