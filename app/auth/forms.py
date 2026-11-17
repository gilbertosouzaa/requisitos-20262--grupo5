from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="Informe um e-mail válido.")
        ],
        render_kw={"placeholder": "seu.email@exemplo.com", "autocomplete": "email"}
    )
    senha = PasswordField(
        'Senha',
        validators=[
            DataRequired(message="Informe sua senha.")
        ],
        render_kw={"placeholder": "••••••••", "autocomplete": "current-password"}
    )
    submit = SubmitField('Entrar')


class CadastroForm(FlaskForm):
    nome = StringField(
        'Nome completo',
        validators=[
            DataRequired(message="Informe seu nome completo.")
        ],
        render_kw={"placeholder": "Ex: Ana Souza", "autocomplete": "name"}
    )
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="Informe um e-mail válido.")
        ],
        render_kw={"placeholder": "seu.email@exemplo.com", "autocomplete": "email"}
    )
    senha = PasswordField(
        'Senha',
        validators=[
            DataRequired(message="Informe uma senha."),
            Length(min=8, message="A senha deve ter no mínimo 8 caracteres.")
        ],
        render_kw={"placeholder": "Mínimo 8 caracteres", "autocomplete": "new-password"}
    )
    curso_id = SelectField(
        'Curso',
        coerce=int,
        validators=[
            DataRequired(message="Selecione o seu curso.")
        ]
    )
    termos = BooleanField(
        'Li e aceito a Política de Privacidade e os Termos de Uso',
        validators=[
            DataRequired(message="Você precisa aceitar a Política de Privacidade e os Termos de Uso.")
        ]
    )
    submit = SubmitField('Criar conta')


class RecuperarSenhaForm(FlaskForm):
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="Informe um e-mail válido.")
        ],
        render_kw={"placeholder": "seu.email@exemplo.com", "autocomplete": "email"}
    )
    submit = SubmitField('Enviar link')


class RedefinirSenhaForm(FlaskForm):
    nova_senha = PasswordField(
        'Nova senha',
        validators=[
            DataRequired(message="Informe a nova senha."),
            Length(min=8, message="A senha deve ter no mínimo 8 caracteres.")
        ],
        render_kw={"placeholder": "Mínimo 8 caracteres", "autocomplete": "new-password"}
    )
    confirma_senha = PasswordField(
        'Confirmação da nova senha',
        validators=[
            DataRequired(message="Confirme a nova senha."),
            EqualTo('nova_senha', message="As senhas digitadas não coincidem.")
        ],
        render_kw={"placeholder": "Repita a nova senha", "autocomplete": "new-password"}
    )
    submit = SubmitField('Salvar nova senha')
