# Apoio ENADE — Sistema de Preparação para o ENADE

Sistema web de apoio ao estudante para preparação ao ENADE, reunindo banco de questões de edições anteriores, simulados cronometrados e gabaritos comentados.

---

## 📌 Funcionalidades Implementadas

### Etapa 1: Base do Projeto e Telas de Acesso (T01 a T04)
- **T01 — Landing Page (`/`):** Apresentação, espaço de ilustração, seção `#como-funciona` com cards e links de navegação. Usuário logado é redirecionado automaticamente para `/inicio`.
- **T02 — Login (`/entrar` - RF02 / US02):** Formulário em duas colunas, link para recuperação de senha e erro genérico ("E-mail ou senha incorretos.") para não expor a existência de contas.
- **T03 — Cadastro (`/cadastro` - RF01 / US01):** Cadastro de estudante com nome, e-mail, senha (mínimo de 8 caracteres), curso e consentimento da LGPD / Termos de Uso (RNF04). Impede e-mails duplicados com mensagem direta e atalhos para Entrar/Recuperar senha. Login automático pós-cadastro.
- **T04 — Recuperação de Senha (`/recuperar-senha` e `/redefinir-senha/<token>` - RF03 / US03):** Solicitação de redefinição com link de uso único e validade de 1 hora. Serviço de e-mail simulado (`app/services/email.py`) imprimindo no console. Tratamento de token expirado com botão para pedir novo link.
- **Encerramento de sessão (`POST /sair`):** Logout seguro com invalidação da sessão e proteção CSRF.

### Etapa 2: Início Completo, Banco de Questões e Modo Estudo (T05, T06, T07)
- **Novo Modelo `RespostaEstudo`:** Registra respostas do modo estudo (usuario_id, questao_id, alternativa_marcada, texto_resposta, correta, respondida_em). Permite respostas repetidas, considerando a mais recente para o status e cálculos.
- **T05 — Início Completo (`/inicio` - RNF01, RN08, RN03):**
  - Saudação personalizada e curso do estudante.
  - Faixa "Você tem um simulado em andamento" pronta para receber dados da próxima etapa.
  - Cards de acesso rápido: "Fazer um simulado", "Estudar questões" e "Seu desempenho".
  - Diagnóstico de desempenho no modo estudo: % de acerto geral (objetivas corretas ÷ objetivas respondidas, excluindo questões anuladas - RN03/RN08) e as 2 áreas prioritárias para revisão com barras de progresso ("Revisar primeiro"). Se não houver respostas, convite amigável para começar.
  - Navegação rápida para simulado em até 3 cliques (RNF01).
- **T06 — Banco de Questões (`/questoes` - RF04, US04, RN01):**
  - Acesso público para visitantes e estudantes (RN01).
  - Barra lateral com filtros combinados na query string: Curso (padrão do cadastro se logado), Ano, Componente, Área de conhecimento, Tipo e Situação (Não respondidas / Errei, exclusivo para autenticados).
  - Busca textual no enunciado e ordenação (Mais recentes / Número da questão).
  - Resumo de resultados com filtros ativos: "N questões encontradas · ...".
  - Itens com número, etiquetas (ano, componente, área, tipo), etiqueta preta "Anulada pelo INEP" (RN03) e status do estudante (Não respondida / Acertou / Errou / Respondida).
  - Paginação de 10 em 10.
- **T07a — Questão em Modo Estudo (`/questoes/<id>` - RF05, RF06, US05):**
  - Trilha de navegação com breadcrumbs.
  - Enunciado completo, imagem/diagrama placeholder e alternativas A–E como botões de rádio acessíveis com realce da opção selecionada.
  - Discursivas com campo de texto e envio de autoavaliação (RF07).
  - Navegação entre Anterior e Próxima questão preservando o conjunto filtrado atual.
  - Botão de envio desabilitado até selecionar uma alternativa (US05). Visitantes são encaminhados para o login preservando o retorno para a questão.
- **T07b — Correção Comentada (mesma página após responder - RF08, US06):**
  - Envio assíncrono com `fetch` (JSON + CSRF) via `/api/questoes/<id>/responder` com transição imediata para a tela de correção sem recarregar (além de suporte a fallback com formulário tradicional).
  - Faixa de resultado com ícone e texto: "Você acertou!" ou "Você errou. Sua resposta: X · Alternativa correta: Y".
  - Alternativas bloqueadas: correta destacada com ✓ e texto "Correta"; alternativa do usuário com borda tracejada e ✗ "Sua resposta".
  - Enunciado recolhido no `<details>` "Ver enunciado".
  - Bloco "Gabarito comentado": explicação detalhada da alternativa correta e erros das demais; ou estado "Comentário em elaboração" com link para a discussão da questão (`/questoes/<id>/discussao`).
  - Para discursivas: comparação da resposta do estudante com o padrão oficial do INEP.

### Etapa 4: Área do Administrador (T13 a T15 e Importação CSV)
- **Controle de Acesso (RN11):**
  - Novo blueprint `admin` com rotas prefixadas em `/admin/...` e decorator flexível `@requer_perfil('admin', 'professor')`.
  - Tentativas de acesso de visitantes são direcionadas ao login com retorno preservado (`next`); usuários sem perfil recebem página HTTP 403 Forbidden ("Você não tem permissão para acessar esta página").
  - Redirecionamento automático pós-login do admin diretamente para `/admin/questoes` e link "Administração" exibido no cabeçalho.
- **Template `base_admin.html`:**
  - Cabeçalho administrativo com fundo `#f5f5f5`, logo, etiqueta preta "Administração", navegação (Questões, Comentários, Moderação "(em breve)", atalho "Ver como estudante ›") e menu do usuário.
- **Modelos e Auditoria:**
  - `Questao`: campos `imagem_arquivo`, `imagem_descricao`, `comentario_status` (`rascunho` | `publicado`), `comentario_fonte`, `comentario_atualizado_em`, `comentario_atualizado_por`, `criada_em`, `atualizada_em` e restrição de unicidade `UniqueConstraint('ano', 'curso_id', 'numero')`.
  - Sigilo de comentários não publicados: o estudante só visualiza o gabarito comentado no modo estudo e revisão de simulados quando `comentario_status == 'publicado'`. Fora isso, é mantido o estado "Comentário em elaboração". Justificativas de alternativas erradas vazias são omitidas.
- **T13 — Lista de Questões (`/admin/questoes` - RF19, US10):**
  - Cabeçalho com resumo em tempo real: total de cadastradas, total de anuladas e total sem comentário.
  - Filtros cumulativos na query string (busca por número/enunciado, curso, ano, área e situação: Todas, Ativas, Anuladas, Sem comentário).
  - Tabela completa de questões com status pills e menu de ações em dropdown acessível (tecla Esc e clique fora):
    - "Editar" e "Comentário";
    - "Marcar como anulada" / "Desmarcar anulação" (POST imediato);
    - "Duplicar como nova";
    - "Remover": modal `<dialog>` de confirmação nativo com verificação prévia no servidor. Caso a questão já possua respostas de estudantes (em `RespostaEstudo`, `SimuladoQuestao` ou `SimuladoResposta`), a remoção é estritamente bloqueada e o sistema orienta a anulação. Questões sem respostas podem ser removidas definitivamente.
  - Paginação de 20 em 20 itens.
- **T14 — Formulário de Questão (`/admin/questoes/nova` e `/admin/questoes/<id>/editar` - RF19, US10, RN02):**
  - Seções estruturadas: Classificação, Enunciado/Mídia, Tipo/Respostas e Situação.
  - Sugestões dinâmicas de área de conhecimento adaptadas ao componente selecionado (Formação Geral ou Componente Específico).
  - Suporte a upload de imagem (PNG ou JPG até 2MB) salva em `instance/uploads`, com visualização de prévia e campo obrigatório de descrição para acessibilidade (WCAG AA).
  - Alternância interativa entre questão objetiva (5 alternativas e seleção do gabarito oficial) e discursiva (padrão de resposta do INEP).
  - Checklist lateral em tempo real validando as regras de RN02 via JavaScript puro.
  - Validação no servidor com banner `role="alert"` no topo contendo links âncora navegáveis para os campos com erro.
- **T15 — Fila e Editor de Comentário (`/admin/comentarios` e `/admin/questoes/<id>/comentario` - RF20, US11):**
  - Fila de priorização listando questões sem comentário publicado.
  - Editor com cabeçalho contextual e enunciado recolhível com `<details>`.
  - Campos para explicação da alternativa correta (ou padrão de resposta), justificativas opcionais de erro para cada alternativa incorreta, fonte/referência e rádio de status (Rascunho / Publicado).
  - Pré-visualização em tempo real sincronizada (split screen) utilizando o mesmo visual e partial (`partials/gabarito_comentado.html`) exibido para o estudante.
- **Importação de Edição em CSV (`/admin/questoes/importar` - RNF10):**
  - Rota para download de CSV modelo de exemplo (`/admin/questoes/exemplo.csv`).
  - Fluxo em duas etapas com validação atômica:
    - Etapa 1: Leitura e validação rigorosa de todas as linhas contra as regras de RN02 e unicidade `(ano, curso, numero)`. Havendo erros, uma tabela exibe as linhas inválidas e os motivos detalhados, sem salvar nada no banco. Estando todas válidas, exibe tabela de pré-visualização.
    - Etapa 2: Confirmação e gravação atômica (tudo ou nada) em transação única, atribuindo status inicial de rascunho.
- **Moderação do Fórum (`/admin/moderacao` - US15 P2):**
  - Item "Moderação (em breve)" com página de placeholder semântica "Em construção".

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.12+ com Flask (Application Factory `create_app` e Blueprints).
- **Banco de Dados:** SQLite com Flask-SQLAlchemy.
- **Segurança:**
  - Hash de senhas com **bcrypt** (RNF03).
  - Gestão de sessão com **Flask-Login** e decorator `@login_required` com parâmetro `?next=<url>`.
  - Proteção CSRF em formulários e requisições assíncronas via **Flask-WTF**.
- **Frontend:**
  - Renderização no servidor via **Jinja2** com templates base (`base.html`, `base_publica.html`, `base_app.html`).
  - **CSS puro** em `static/css/style.css` com paleta em tons de cinza (`#1a1a1a`, `#555`, `#fff`, `#f0f0f0`), destaque em azul (`#1F4FD8`), botões com altura mínima de 44px e raio de 8px.
  - **JavaScript puro** (Vanilla, um arquivo por tela em `static/js/`).
  - Acessibilidade **WCAG 2.1 nível AA** (RNF09): labels semânticos em todos os campos, foco visível, contraste superior a 4.5:1 e `role="status"` / `role="alert"`.

---

## 📂 Estrutura do Projeto

```text
/
├── app/
│   ├── __init__.py           # Application Factory (create_app), extensões e blueprints
│   ├── extensions.py         # Instâncias do db, bcrypt, login_manager e csrf
│   ├── models.py             # Modelos: Usuario, Curso, Questao, Alternativa, TokenRecuperacao, RespostaEstudo, Simulado, SimuladoQuestao, SimuladoResposta
│   ├── seed.py               # Comandos CLI (flask init-db e flask seed)
│   ├── auth/                 # Blueprint de autenticação (rotas, formulários e decorators)
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── main/                 # Blueprint principal
│   │   ├── __init__.py
│   │   └── routes.py         # /, /inicio, /questoes, /simulados, /desempenho e APIs
│   ├── admin/                # Blueprint da área administrativa (RN11, T13 a T15, CSV)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/
│   │   └── email.py          # Serviço simulado de envio de e-mail (imprime no console)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Estilização completa e responsiva
│   │   ├── js/               # JavaScript vanilla por tela
│   │   │   ├── landing.js
│   │   │   ├── login.js
│   │   │   ├── cadastro.js
│   │   │   ├── recuperar_senha.js
│   │   │   ├── redefinir_senha.js
│   │   │   ├── inicio.js
│   │   │   ├── questoes.js
│   │   │   ├── questao.js
│   │   │   ├── simulado_novo.js
│   │   │   ├── simulado.js
│   │   │   ├── resultado.js
│   │   │   ├── desempenho.js
│   │   │   ├── admin_questoes.js
│   │   │   ├── admin_questao_form.js
│   │   │   └── admin_comentario.js
│   │   └── img/
│   │       └── logo.svg      # Logo oficial em SVG
│   └── templates/
│       ├── base.html, base_publica.html, base_app.html, base_admin.html
│       ├── auth/             # Login, cadastro, recuperação, nova senha e 403 Forbidden
│       ├── main/             # Landing, início, banco de questões, questão, simulados, resultado, revisão e desempenho
│       ├── admin/            # Lista de questões (T13), formulário (T14), comentários (T15), importação CSV e moderação
│       └── partials/         # Componentes compartilhados (ex: gabarito_comentado.html)
├── config.py                 # Configurações de desenvolvimento e testes
├── requirements.txt          # Dependências do projeto
├── README.md                 # Documentação e instruções de execução
└── tests/                    # Suíte com 63 testes automatizados (pytest e E2E)
```

---

## 🚀 Como Rodar o Projeto

Siga o passo a passo abaixo no terminal:

### 1. Ativar o ambiente virtual (venv)
No Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```
No Linux / macOS:
```bash
source .venv/bin/activate
```

### 2. Instalar as dependências (caso necessário)
```bash
pip install -r requirements.txt
```

### 3. Inicializar e popular o banco de dados
```bash
flask --app app init-db
flask --app app seed
```

### 4. Executar o servidor web
```bash
flask --app app run
```
Acesse no navegador: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 👥 Credenciais de Teste (Seed)

O comando `flask seed` cadastra automaticamente as seguintes contas para testes:

| Papel | Nome | E-mail | Senha | Curso |
|---|---|---|---|---|
| **Estudante** | Ana Souza | `ana@teste.com` | `12345678` | Ciência da Computação |
| **Professor** | Prof. Marcelo | `marcelo@teste.com` | `prof12345` | Ciência da Computação (Áreas: Banco de Dados, Redes) |
| **Administrador** | Administrador do Sistema | `admin@teste.com` | `admin1234` | Ciência da Computação |

---

## 🛡️ Perfis, Gestão de Usuários e Regras de Negócio (RN11, RN13–RN19)

- **Perfis de acesso:**
  - `estudante` (padrão): acessa simulados, banco de questões e desempenho.
  - `professor`: acessa somente `/admin/comentarios` e o editor de comentário, filtrados pelas áreas atribuídas a ele.
  - `admin`: acesso total (questões, comentários, importação CSV, gestão de usuários e moderação).
- **Comando de emergência (`criar-admin`):**
  ```bash
  flask --app app criar-admin --nome "Nome Completo" --email admin@exemplo.com
  ```
  Cria um administrador (ou promove um usuário existente), registra auditoria com motivo `"via linha de comando"` e imprime o link de definição de senha (validade de 48h).
- **Regras:**
  - **RN11:** Apenas administradores cadastram, editam ou removem questões. Professores só editam comentários de gabarito das questões das áreas sob sua responsabilidade.
  - **RN13:** Todo cadastro feito pela tela pública cria um usuário com perfil Estudante.
  - **RN14:** Apenas um Administrador pode alterar perfis, áreas de professor ou status de contas.
  - **RN15:** O sistema impede que o último Administrador ativo seja rebaixado ou desativado.
  - **RN16:** Um administrador não pode alterar o próprio perfil nem desativar a própria conta.
  - **RN17:** Contas não são apagadas pela interface, só desativadas; seus dados e respostas continuam no histórico.
  - **RN18 (Privacidade / LGPD):** A gestão de usuários exibe apenas dados cadastrais, nunca respostas, simulados ou desempenho.
  - **RN19:** Um professor precisa ter pelo menos uma área atribuída; sem área, vê o aviso *"Nenhuma área atribuída. Procure a administração."* e não acessa comentários.

---

## 🧪 Como Executar os Testes Automatizados

Os testes cobrem todos os critérios de aceitação de **US01, US02, US03, US04, US05 e US06**, além das regras de negócio **RN01, RN02, RN03, RN08 e RNF01**:

```bash
pytest
```
Ou com detalhes:
```bash
pytest -v
```
Para rodar especificamente a validação ponta a ponta com CSRF ativo:
```bash
python tests/test_etapa2_e2e.py
```
