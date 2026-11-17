import sys

def simular_envio_recuperacao(email: str, link_redefinicao: str):
    """
    Simula o envio de e-mail de recuperação de senha, imprimindo no console
    do servidor (conforme RF03/US03).
    """
    mensagem = (
        "\n==================== [SIMULAÇÃO DE E-MAIL] ====================\n"
        f"Para: {email}\n"
        "Assunto: Recuperação de Senha - Apoio ENADE\n"
        "----------------------------------------------------------------\n"
        "Olá! Você solicitou a redefinição da sua senha no Apoio ENADE.\n"
        "Para criar uma nova senha, utilize o link abaixo (válido por 1 hora):\n\n"
        f"  {link_redefinicao}\n\n"
        "Se você não solicitou esta alteração, ignore este e-mail.\n"
        "================================================================\n"
    )
    print(mensagem, file=sys.stdout, flush=True)
