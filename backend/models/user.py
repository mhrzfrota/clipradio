from app import db
from datetime import datetime
import bcrypt
import uuid

class User(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    radios = db.relationship('Radio', backref='usuario', lazy=True, cascade='all, delete-orphan')
    gravacoes = db.relationship('Gravacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    agendamentos = db.relationship('Agendamento', backref='usuario', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'ativo': self.ativo,
            'is_admin': self.is_admin,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
