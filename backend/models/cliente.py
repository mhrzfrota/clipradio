from app import db
from datetime import datetime
import uuid


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(255), nullable=False)
    cidade = db.Column(db.String(255))
    estado = db.Column(db.String(2))
    user_id = db.Column(db.String(36), db.ForeignKey('usuarios.id'), index=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cidade': self.cidade,
            'estado': self.estado,
            'user_id': self.user_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
