from app import db

# Tabela de associação muitos-para-muitos entre gravacoes e tags
gravacao_tags = db.Table(
    'gravacoes_tags',
    db.Column('gravacao_id', db.String(36), db.ForeignKey('gravacoes.id'), primary_key=True),
    db.Column('tag_id', db.String(36), db.ForeignKey('tags.id'), primary_key=True)
)

