from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy.orm import validates
from app.extensions import db, bcrypt

def utc_now():
    return datetime.now(timezone.utc)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(128), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=True)
    perfil = db.Column(db.String(20), default='estudante', nullable=False)  # 'estudante' | 'admin'
    criado_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    curso = db.relationship('Curso', back_populates='usuarios')
    tokens_recuperacao = db.relationship(
        'TokenRecuperacao',
        back_populates='usuario',
        cascade='all, delete-orphan'
    )
    respostas_estudo = db.relationship(
        'RespostaEstudo',
        back_populates='usuario',
        cascade='all, delete-orphan'
    )
    simulados = db.relationship(
        'Simulado',
        back_populates='usuario',
        cascade='all, delete-orphan'
    )

    def set_senha(self, senha: str):
        self.senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    def verificar_senha(self, senha: str) -> bool:
        if not self.senha_hash:
            return False
        return bcrypt.check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.id}: {self.email} ({self.perfil})>"


class Curso(db.Model):
    __tablename__ = 'curso'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)

    usuarios = db.relationship('Usuario', back_populates='curso')
    questoes = db.relationship('Questao', back_populates='curso')

    def __repr__(self):
        return f"<Curso {self.id}: {self.nome}>"


class Questao(db.Model):
    __tablename__ = 'questao'

    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=True)
    numero = db.Column(db.Integer, nullable=False)
    componente = db.Column(db.String(50), nullable=False)  # 'formacao_geral' | 'especifico'
    area = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'objetiva' | 'discursiva'
    enunciado = db.Column(db.Text, nullable=False)
    imagem_placeholder = db.Column(db.String(200), nullable=True)
    imagem_arquivo = db.Column(db.String(255), nullable=True)
    imagem_descricao = db.Column(db.String(255), nullable=True)
    gabarito_oficial = db.Column(db.String(10), nullable=False)
    comentario_correta = db.Column(db.Text, nullable=True)
    padrao_resposta = db.Column(db.Text, nullable=True)
    anulada = db.Column(db.Boolean, default=False, nullable=False)

    # Metadados de Comentário e Auditoria
    comentario_status = db.Column(db.String(20), default='rascunho', nullable=False)  # 'rascunho' | 'publicado'
    comentario_fonte = db.Column(db.String(255), nullable=True)
    comentario_atualizado_em = db.Column(db.DateTime, nullable=True)
    comentario_atualizado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    criada_em = db.Column(db.DateTime, default=utc_now, nullable=False)
    atualizada_em = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('ano', 'curso_id', 'numero', name='uq_questao_ano_curso_numero'),
    )

    curso = db.relationship('Curso', back_populates='questoes')
    autor_comentario = db.relationship('Usuario', foreign_keys=[comentario_atualizado_por])
    alternativas = db.relationship(
        'Alternativa',
        back_populates='questao',
        cascade='all, delete-orphan',
        order_by='Alternativa.letra'
    )
    respostas_estudo = db.relationship(
        'RespostaEstudo',
        back_populates='questao',
        cascade='all, delete-orphan'
    )

    # RN02: toda questão tem ano, componente, área, tipo e gabarito oficial.
    # Curso é obrigatório somente para o Componente Específico (FG é comum a todos os cursos).
    @validates('ano')
    def validate_ano(self, key, value):
        if not value or not isinstance(value, int) or value < 2000:
            raise ValueError("O ano da questão é obrigatório e deve ser válido.")
        return value

    @validates('curso_id')
    def validate_curso_id(self, key, value):
        if getattr(self, 'componente', None) == 'especifico' and not value:
            raise ValueError("O curso da questão é obrigatório para o Componente Específico.")
        return value

    @validates('componente')
    def validate_componente(self, key, value):
        if value not in ('formacao_geral', 'especifico'):
            raise ValueError("Componente deve ser 'formacao_geral' ou 'especifico'.")
        return value

    @validates('area')
    def validate_area(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("A área de conhecimento é obrigatória.")
        return str(value).strip()

    @validates('tipo')
    def validate_tipo(self, key, value):
        if value not in ('objetiva', 'discursiva'):
            raise ValueError("Tipo deve ser 'objetiva' ou 'discursiva'.")
        return value

    @validates('gabarito_oficial')
    def validate_gabarito_oficial(self, key, value):
        if not value or not str(value).strip():
            raise ValueError("O gabarito oficial da questão é obrigatório.")
        return str(value).strip().upper()

    def __repr__(self):
        return f"<Questao {self.id}: ENADE {self.ano} Q{self.numero} ({self.componente})>"


class Alternativa(db.Model):
    __tablename__ = 'alternativa'

    id = db.Column(db.Integer, primary_key=True)
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'), nullable=False)
    letra = db.Column(db.String(2), nullable=False)  # 'A', 'B', 'C', 'D', 'E'
    texto = db.Column(db.Text, nullable=False)
    comentario_erro = db.Column(db.Text, nullable=True)

    questao = db.relationship('Questao', back_populates='alternativas')

    def __repr__(self):
        return f"<Alternativa {self.letra} (Questao {self.questao_id})>"


class TokenRecuperacao(db.Model):
    __tablename__ = 'token_recuperacao'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)

    usuario = db.relationship('Usuario', back_populates='tokens_recuperacao')

    def is_valido(self) -> bool:
        if self.usado:
            return False
        agora = datetime.now(timezone.utc)
        exp = self.expira_em
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return agora <= exp

    def __repr__(self):
        return f"<TokenRecuperacao {self.token[:8]}... (Usuario {self.usuario_id})>"


class RespostaEstudo(db.Model):
    __tablename__ = 'resposta_estudo'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'), nullable=False)
    alternativa_marcada = db.Column(db.String(2), nullable=True)  # 'A'-'E' para objetivas
    texto_resposta = db.Column(db.Text, nullable=True)  # texto para discursivas
    correta = db.Column(db.Boolean, nullable=True)  # bool para objetivas, null para discursivas
    respondida_em = db.Column(db.DateTime, default=utc_now, nullable=False)

    usuario = db.relationship('Usuario', back_populates='respostas_estudo')
    questao = db.relationship('Questao', back_populates='respostas_estudo')

    def __repr__(self):
        return f"<RespostaEstudo {self.id}: Usuario {self.usuario_id} - Questao {self.questao_id} (Correta: {self.correta})>"


class Simulado(db.Model):
    __tablename__ = 'simulado'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'completo' | 'parcial'
    edicao_ano = db.Column(db.Integer, nullable=True)  # se completo
    componente = db.Column(db.String(50), nullable=True)  # se parcial ('especifico' | 'formacao_geral' | 'ambos')
    area = db.Column(db.String(100), nullable=True)  # se parcial
    iniciado_em = db.Column(db.DateTime, default=utc_now, nullable=False)
    duracao_segundos = db.Column(db.Integer, nullable=False)
    finalizado_em = db.Column(db.DateTime, nullable=True)
    finalizado_por = db.Column(db.String(20), nullable=True)  # 'entrega' | 'tempo'

    usuario = db.relationship('Usuario', back_populates='simulados')
    questoes_assoc = db.relationship(
        'SimuladoQuestao',
        back_populates='simulado',
        cascade='all, delete-orphan',
        order_by='SimuladoQuestao.ordem'
    )
    respostas = db.relationship(
        'SimuladoResposta',
        back_populates='simulado',
        cascade='all, delete-orphan'
    )

    def get_tempo_restante_segundos(self) -> int:
        if self.finalizado_em:
            return 0
        agora = datetime.now(timezone.utc)
        iniciado = self.iniciado_em
        if iniciado.tzinfo is None:
            iniciado = iniciado.replace(tzinfo=timezone.utc)
        decorrido = int((agora - iniciado).total_seconds())
        restante = self.duracao_segundos - decorrido
        return max(0, restante)

    def is_expirado(self) -> bool:
        return self.get_tempo_restante_segundos() == 0 and self.finalizado_em is None

    def finalizar(self, motivo: str = 'entrega'):
        if not self.finalizado_em:
            self.finalizado_em = utc_now()
            self.finalizado_por = motivo

    def __repr__(self):
        return f"<Simulado {self.id}: Usuario {self.usuario_id} ({self.tipo}, finalizado: {self.finalizado_em is not None})>"


class SimuladoQuestao(db.Model):
    __tablename__ = 'simulado_questao'

    id = db.Column(db.Integer, primary_key=True)
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'), nullable=False)
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)

    simulado = db.relationship('Simulado', back_populates='questoes_assoc')
    questao = db.relationship('Questao')

    def __repr__(self):
        return f"<SimuladoQuestao {self.id}: Simulado {self.simulado_id} - Questao {self.questao_id} (Ordem: {self.ordem})>"


class SimuladoResposta(db.Model):
    __tablename__ = 'simulado_resposta'

    id = db.Column(db.Integer, primary_key=True)
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'), nullable=False)
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'), nullable=False)
    alternativa_marcada = db.Column(db.String(2), nullable=True)  # 'A'-'E' para objetivas
    texto_resposta = db.Column(db.Text, nullable=True)  # texto para discursivas
    atualizada_em = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    simulado = db.relationship('Simulado', back_populates='respostas')
    questao = db.relationship('Questao')

    __table_args__ = (
        db.UniqueConstraint('simulado_id', 'questao_id', name='uq_simulado_questao_resposta'),
    )

    def __repr__(self):
        return f"<SimuladoResposta {self.id}: Simulado {self.simulado_id} - Questao {self.questao_id}>"


