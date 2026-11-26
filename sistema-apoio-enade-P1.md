# Sistema de Apoio ao ENADE
## Elicitação de Requisitos e Modelagem Inicial

**Disciplina:** Requisitos e Modelagem de Sistemas
**Atividade:** Trabalho P1 — Sprint 1 / Milestone M1
**Período:** 20/10/2026 a 02/11/2026

---

## 1. Documento de Visão

### 1.1 Introdução

O ENADE (Exame Nacional de Desempenho dos Estudantes) é componente curricular obrigatório dos cursos de graduação e um dos indicadores usados pelo MEC para avaliar a qualidade do ensino superior. Apesar disso, boa parte dos estudantes chega à prova sem ter tido contato com o formato das questões, sem ter feito uma prova completa dentro do tempo e sem saber em quais conteúdos tem mais dificuldade.

Este projeto especifica um sistema web e mobile para apoiar essa preparação, reunindo em um só lugar questões de edições anteriores, simulados cronometrados, gabaritos comentados, acompanhamento de desempenho e discussão entre estudantes.

### 1.2 Contexto: estrutura da prova

A especificação considera a estrutura usual do ENADE:

| Componente | Questões objetivas | Questões discursivas | Total |
|---|---:|---:|---:|
| Formação Geral | 8 | 2 | 10 |
| Componente Específico (por curso) | 27 | 3 | 30 |
| **Total** | **35** | **5** | **40** |

A prova tem duração de 4 horas. Questões podem ser anuladas pelo INEP após a aplicação, o que precisa ser tratado pelo sistema.

### 1.3 Problema

Hoje o estudante que quer se preparar precisa procurar provas antigas em PDF no site do INEP, conferir gabaritos em documentos separados e não tem como saber, de forma organizada, em que áreas está errando mais. Não existe um ambiente que junte questões, explicação das respostas, prática em condição de prova e acompanhamento da evolução.

### 1.4 Objetivo do sistema

Oferecer ao estudante de graduação um ambiente de estudo para o ENADE em que ele possa praticar questões de edições anteriores, simular a prova no tempo real, entender seus erros e acompanhar seu desempenho por área de conhecimento.

### 1.5 Objetivos específicos

- Disponibilizar um banco de questões de edições anteriores, classificado por ano, curso, componente (formação geral ou específico) e área de conhecimento.
- Permitir simulados cronometrados, completos ou parciais.
- Apresentar gabarito comentado para questões objetivas e padrão de resposta para questões discursivas.
- Mostrar o desempenho do estudante por área e ao longo do tempo.
- Oferecer um espaço de discussão por questão.
- Garantir acesso individual e proteção dos dados pessoais.

### 1.6 Público-alvo

- **Estudantes de graduação** que farão o ENADE: usuários principais.
- **Professores:** podem contribuir com comentários de questões e usar o sistema como apoio em aula.
- **Coordenações de curso:** interessadas em acompanhar, de forma agregada, o nível de preparação das turmas.

### 1.7 Escopo

| Módulo | Descrição |
|---|---|
| Banco de questões | Consulta e filtro de questões por ano, curso, componente e área |
| Modo estudo | Resolução de questões avulsas com correção imediata |
| Simulados | Prova cronometrada, completa ou parcial, com correção ao final |
| Gabarito comentado | Explicação da resposta correta e padrão de resposta das discursivas |
| Desempenho | Estatísticas por área, gráficos e histórico |
| Fórum | Discussão vinculada a cada questão, com moderação |
| Acesso | Cadastro, autenticação e recuperação de senha |
| Administração | Gestão do banco de questões e moderação |

### 1.8 Fora do escopo

- Implementação do sistema (esta etapa é de especificação).
- Correção automática de questões discursivas.
- Produção de conteúdo inédito (o banco se limita a questões de edições anteriores).
- Integração com sistemas acadêmicos da universidade.

---

## 2. Stakeholders

| Stakeholder | Interesse | Influência | Papel |
|---|---|:---:|---|
| Estudante | Praticar, simular a prova e acompanhar a evolução | Alta | Usuário principal |
| Administrador | Manter o banco de questões, moderar o fórum e gerenciar usuários e perfis | Alta | Usuário administrativo |
| Professor | Revisar comentários das questões da sua área e usar o sistema em aula | Média | Usuário colaborador (validado nas entrevistas) |
| Coordenação de curso | Acompanhar a preparação das turmas | Média/Alta | Consumidor de relatórios (validado parcialmente; sem entrevista com coordenador) |
| Universidade | Melhorar o desempenho institucional no ENADE | Alta | Patrocinador |
| Equipe de desenvolvimento | Especificar e implementar a solução | Média | Equipe técnica |
| Professor da disciplina | Avaliar e validar os entregáveis | Alta | Validador |

A elicitação começa pelos estudantes, que usarão a maior parte das funcionalidades. Professores e coordenadores serão consultados para validar as necessidades pedagógicas e definir até onde vai o acesso a dados de desempenho dos alunos.

---

## 3. Técnicas de Elicitação

| Técnica | Objetivo | Público |
|---|---|---|
| Entrevista semiestruturada | Entender hábitos de estudo, dificuldades e expectativas | Estudantes, professores, coordenação |
| Questionário online | Confirmar com mais pessoas as necessidades levantadas nas entrevistas | Estudantes de diferentes cursos |
| Análise documental | Entender a estrutura da prova e os critérios de classificação das questões | Provas, gabaritos e relatórios do INEP |
| Análise de sistemas similares | Identificar funcionalidades esperadas e pontos fracos | QConcursos, Estuda.com |

---

## 4. Roteiros de Entrevista

### 4.1 Estudantes

1. Você já usou alguma plataforma para estudar para provas ou concursos? Qual? O que mais gostou e o que te incomodou nela?
2. No dia a dia, você costuma estudar e resolver exercícios mais pelo computador ou pelo celular?
3. Se fosse estudar para o ENADE hoje, onde procuraria questões antigas e como organizaria esse estudo?
4. Qual é a sua maior dificuldade na hora de se preparar para esse tipo de prova?
5. Como o ENADE não reprova diretamente, o que realmente faria você levar a preparação a sério e usar a plataforma com frequência?
6. Se tivesse um banco com milhares de questões do ENADE, como você gostaria de buscar ou filtrar o que quer estudar?
7. Você faria uma prova completa de 4 horas no sistema ou preferiria simulados mais curtos e focados? Por quê?
8. Logo depois de marcar uma alternativa, o que você espera que apareça na tela?
9. Como você costuma estudar e corrigir suas respostas nas questões discursivas hoje?
10. Você participaria de fóruns ou comentários para discutir a resolução das questões com outros alunos?
11. Que tipo de informação sobre o seu próprio desempenho te ajudaria a saber se você está evoluindo?
12. Você se incomodaria se a coordenação do curso tivesse acesso aos seus resultados individuais? E se fossem apenas dados gerais/agregados da turma?

### 4.2 Professores e coordenação

1. Na sua visão, quais são as maiores dificuldades dos alunos na prova do ENADE hoje?
2. Como a preparação para o ENADE é feita atualmente no curso e onde vocês sentem que perdem mais tempo?
3. Você usaria a plataforma apenas como apoio livre para os alunos, ou gostaria de aplicar listas/simulados valendo nota na sua disciplina?
4. Quem você imagina cadastrando as questões e revisando os gabaritos no sistema (professores, monitores, importação das provas do INEP)?
5. Como as questões deveriam ser classificadas para refletir a matriz curricular do curso?
6. Você teria disponibilidade para escrever comentários ou resoluções explicadas nas questões da sua área?
7. Que indicadores ou relatórios ajudariam você a avaliar o nível de preparação da turma antes da prova oficial?
8. Quais cuidados ou restrições o sistema precisa ter em relação ao acesso e à privacidade dos dados de desempenho dos alunos?

---

## 5. Resultados das Entrevistas

Foram realizadas 4 entrevistas semiestruturadas, seguindo os roteiros da seção 4: 3 estudantes (Murilo Enzo, Tainá Souza e Mariana Marques) e 1 professor (Prof. Marcelo). Não foi possível entrevistar um coordenador de curso. As respostas completas estão no documento *Entrevistas de elicitação de requisitos* (P1 / Sprint 1 / Milestone M1).

### 5.1 Resumo por entrevistado

| ID | Perfil / Curso | Necessidade identificada | Problema relatado | Requisito relacionado |
|---|---|---|---|---|
| E01 | Estudante — Murilo Enzo | Filtrar por curso, assunto, ano e tipo e rever as questões que errou; ver o próprio progresso com metas pequenas; simulados curtos no dia a dia e completo perto da prova | Alternar entre PDFs de prova e gabarito no site do INEP é trabalhoso; explicações superficiais em outras plataformas; não sabe o que faltou na discursiva | RF04, RF08, RF09, RF15, RF16, RF07, N08 |
| E02 | Estudante — Tainá Souza | Filtrar por área, componente e ano; gabarito com explicação objetiva no modo estudo e só no final do simulado; histórico por área ao longo das semanas; plano de preparação | Dificuldade de achar conteúdos específicos em outras plataformas; entender o estilo das questões e administrar o tempo | RF04, RF08, RN04, RF09–RF12, RF16, N08 |
| E03 | Estudante — Mariana Marques | Estudar em poucos minutos pelo celular; simulados de 10 a 15 questões; indicação clara de acerto e explicação curta; comparar a discursiva com os pontos esperados pelo INEP | Conciliar a preparação com a graduação; interfaces carregadas; dificuldade de avaliar a própria resposta discursiva | RNF02, RF09, RF06, RF08, RF07, RF15, RF16, N07 |
| E04 | Professor — Prof. Marcelo | Usar como apoio livre (listas avaliativas no futuro); importar provas oficiais; administradores organizam o banco e professores revisam comentários da sua área; relatórios agregados por área, de participação e de conteúdos difíceis | Buscar, selecionar e organizar material de provas anteriores consome tempo; risco de identificar alunos em grupos pequenos | RNF10, RF19, RF20, RN11, RF21, RN12, RNF04 |
| E05 | Coordenador — | *Entrevista não realizada.* | — | RF21 (validação parcial) |

### 5.2 Achados consolidados

| Achado | Frequência | Efeito na especificação |
|---|:---:|---|
| Filtros por curso, área, ano, componente e tipo | 3 de 3 estudantes | Confirma RF04 |
| Rever as questões que errou | 1 de 3 | Confirma RF04 (filtro por situação) |
| Correção imediata com explicação de cada alternativa no modo estudo; gabarito só no final do simulado | 3 de 3 | Confirma RF06, RF08 e RN04 |
| Explicação objetiva, sem textos longos | 2 de 3 | Orientação para o conteúdo dos comentários (RF20) |
| Simulados curtos no dia a dia e prova completa perto do exame | 3 de 3 | Confirma RF09 (completo e parcial) |
| Estuda principalmente pelo celular; computador para simulados longos e discursivas | 2 de 3 | Reforça RNF02; gera N07 |
| Dificuldade de autoavaliar a discursiva; quer comparar com os pontos esperados pelo INEP | 3 de 3 | Reforça RF07; padrão de resposta deve ser apresentado em pontos |
| Ver a evolução ao longo do tempo e comparar os últimos simulados | 3 de 3 | Reforça RF16 |
| Metas, plano de estudo ou indicação do que revisar como motivação para voltar | 3 de 3 | Gera N08 |
| Participaria do fórum mais para ler do que para escrever | 3 de 3 | Confirma RF17; prioridade é consultar dúvidas existentes |
| Resultados individuais privados; dados agregados da turma aceitáveis | 4 de 4 | Confirma RNF04, RF21 e RN12 |
| Professor revisa comentários apenas da sua área, com processo simples | Professor | Valida o ator Professor em RF20 e RN11, restrito à área |
| Importação das provas oficiais como ponto de partida | Professor | Confirma RNF10 e RF19 |
| Relatório com média por área, participação em simulados e conteúdos com maior dificuldade | Professor | Valida RF21 e acrescenta o indicador de participação |

### 5.3 Necessidades levantadas

**Na análise documental**

| ID | Necessidade |
|---|---|
| N01 | Encontrar questões anteriores organizadas e fáceis de filtrar |
| N02 | Praticar em condição parecida com a da prova real (tempo e quantidade) |
| N03 | Entender por que errou cada questão |
| N04 | Saber em quais áreas precisa estudar mais |
| N05 | Tirar dúvidas e discutir questões com outras pessoas |
| N06 | Ter os próprios dados protegidos e acessíveis só para si |

**Nas entrevistas**

| ID | Necessidade | Origem |
|---|---|---|
| N07 | Estudar em sessões curtas, inclusive pelo celular | E01, E02, E03 |
| N08 | Manter a rotina de estudo com metas, plano ou indicação clara do que revisar | E01, E02, E03 |
| N09 | Professores contribuírem com comentários da sua área por um processo simples e com responsabilidades divididas | E04 |

### 5.4 Situação dos itens "a validar"

| Item | Antes | Depois das entrevistas |
|---|---|---|
| RF13 — Retomada de simulado | Média (a validar) | **Validado.** Estudantes conciliam o estudo com a graduação e usam o celular, o que torna interrupções frequentes |
| RF20 / Professor | Participação de professores a validar | **Validado com restrição:** o professor revisa comentários apenas das áreas sob sua responsabilidade |
| RF21 / Coordenador | Baixa (a validar) | **Validado parcialmente:** a necessidade e as regras de privacidade foram confirmadas por estudantes e professor, mas nenhum coordenador foi entrevistado. Prioridade continua Baixa |

### 5.5 Limitações

A amostra é pequena (3 estudantes e 1 professor), os cursos dos estudantes não foram registrados e não houve entrevista com coordenação. Recomenda-se aplicar o questionário online previsto na seção 3 para confirmar N07 e N08 com mais estudantes e entrevistar ao menos um coordenador antes de especificar o relatório agregado (RF21).

---

## 6. Requisitos Funcionais

### Acesso

**RF01 — Cadastro de estudante**
O sistema deve permitir que o estudante crie uma conta informando nome, e-mail, senha e curso.
Prioridade: Alta

**RF02 — Autenticação**
O sistema deve permitir que o usuário entre com e-mail e senha e encerre a sessão quando quiser.
Prioridade: Alta

**RF03 — Recuperação de senha**
O sistema deve permitir que o usuário redefina a senha por meio de um link enviado ao e-mail cadastrado.
Prioridade: Alta

### Banco de questões e modo estudo

**RF04 — Consulta e filtro de questões**
O sistema deve permitir consultar questões filtrando por ano, curso, componente (formação geral ou específico), área de conhecimento e tipo (objetiva ou discursiva).
Prioridade: Alta

**RF05 — Visualização de questão**
O sistema deve exibir o enunciado completo da questão, incluindo textos de apoio, imagens e tabelas, e as alternativas, quando houver.
Prioridade: Alta

**RF06 — Resposta de questão objetiva**
No modo estudo, o estudante deve poder marcar uma alternativa e confirmar a resposta, recebendo a indicação de acerto ou erro.
Prioridade: Alta

**RF07 — Resposta de questão discursiva**
O estudante deve poder escrever sua resposta em campo de texto e, depois de confirmar, ver o padrão de resposta divulgado pelo INEP para fazer a autoavaliação. Sempre que possível, o padrão deve ser apresentado como uma lista dos pontos esperados, para facilitar a comparação (entrevistas E01–E03).
Prioridade: Média

**RF08 — Gabarito comentado**
Depois que o estudante responde, o sistema deve mostrar a alternativa correta e um comentário explicando por que ela está certa e por que as outras estão erradas.
Prioridade: Alta

### Simulados

**RF09 — Montagem de simulado**
O estudante deve poder escolher entre uma prova completa (40 questões, 4 horas) ou um simulado parcial, definindo componente, área e quantidade de questões.
Prioridade: Alta

**RF10 — Cronômetro**
Durante o simulado, o sistema deve exibir o tempo restante o tempo todo.
Prioridade: Alta

**RF11 — Navegação no simulado**
O estudante deve poder avançar, voltar, deixar questões em branco e alterar respostas enquanto o simulado estiver em andamento.
Prioridade: Alta

**RF12 — Finalização do simulado**
O simulado deve ser finalizado quando o estudante confirmar a entrega ou quando o tempo acabar, o que ocorrer primeiro.
Prioridade: Alta

**RF13 — Retomada de simulado**
Se o estudante sair ou perder a conexão, o sistema deve permitir retomar o simulado de onde parou, com as respostas já marcadas.
Prioridade: Média (validada nas entrevistas)

**RF14 — Resultado do simulado**
Após a finalização, o sistema deve mostrar acertos, erros, questões em branco, tempo utilizado e o gabarito comentado de cada questão.
Prioridade: Alta

### Desempenho

**RF15 — Painel de desempenho**
O sistema deve mostrar o percentual de acertos do estudante, no geral e por área de conhecimento, com gráficos.
Prioridade: Alta

**RF16 — Histórico**
O sistema deve mostrar o histórico de simulados realizados e a evolução do percentual de acertos ao longo do tempo, geral e por área, permitindo comparar os últimos simulados (entrevistas E01–E03).
Prioridade: Média

### Fórum

**RF17 — Fórum por questão**
Cada questão deve ter um espaço de discussão em que usuários autenticados podem ler e publicar mensagens.
Prioridade: Média

**RF18 — Denúncia e moderação**
Usuários devem poder denunciar mensagens impróprias, e o administrador deve poder ocultar ou remover mensagens.
Prioridade: Média

### Administração

**RF19 — Gestão do banco de questões**
O administrador deve poder cadastrar, editar, classificar e remover questões, além de marcar questões anuladas pelo INEP.
Prioridade: Alta

**RF20 — Cadastro de comentários de gabarito**
Administradores devem poder cadastrar e editar os comentários de qualquer questão. Professores autorizados devem poder cadastrar e editar os comentários das questões das áreas sob sua responsabilidade.
Prioridade: Alta (participação de professores validada na entrevista E04)

**RF21 — Relatório agregado por curso**
A coordenação deve poder consultar, sem identificação individual, o desempenho médio dos estudantes do curso por área, a participação nos simulados e os conteúdos com maior dificuldade.
Prioridade: Baixa (validada parcialmente: falta entrevista com coordenação)

**RF22 — Gestão de usuários e perfis**
O administrador deve poder listar e buscar usuários, criar contas (a pessoa define a própria senha por um link enviado ao e-mail), alterar o perfil (Estudante, Professor ou Administrador), definir as áreas de cada professor e desativar ou reativar contas. Toda alteração fica registrada em um histórico com autor, data e motivo.
Prioridade: Média (decorre de RF20, RN11 e da entrevista E04)

---

## 7. Requisitos Não Funcionais

| ID | Categoria | Requisito | Como verificar |
|---|---|---|---|
| RNF01 | Usabilidade | Um novo usuário deve conseguir iniciar um simulado em até 3 cliques a partir da tela inicial | Teste com usuários |
| RNF02 | Responsividade | A interface deve funcionar em telas a partir de 360 px de largura, com prioridade para o modo estudo e os simulados parciais, que os estudantes usam pelo celular (N07) | Teste em dispositivos e emuladores |
| RNF03 | Segurança | Senhas devem ser armazenadas com hash (bcrypt ou Argon2), e toda comunicação deve usar HTTPS | Revisão de código e configuração |
| RNF04 | Privacidade | O tratamento de dados pessoais deve seguir a LGPD; os resultados individuais só são visíveis para o próprio estudante | Revisão de regras de acesso |
| RNF05 | Desempenho | 95% das requisições devem responder em até 2 segundos com até 500 usuários simultâneos | Teste de carga |
| RNF06 | Disponibilidade | Disponibilidade mínima de 99% ao mês, com manutenções fora do horário das 8h às 23h | Monitoramento |
| RNF07 | Confiabilidade | As respostas de um simulado em andamento devem ser salvas a cada alteração, sem perda em caso de queda de conexão | Teste de falha de rede |
| RNF08 | Compatibilidade | A versão web deve funcionar nas duas últimas versões de Chrome, Firefox, Edge e Safari; o app, em Android 10+ e iOS 15+ | Teste de compatibilidade |
| RNF09 | Acessibilidade | A interface deve atender ao nível AA da WCAG 2.1 | Ferramenta de auditoria e revisão manual |
| RNF10 | Manutenibilidade | O cadastro de uma nova edição da prova não deve exigir alteração de código | Teste do fluxo de importação |

---

## 8. Regras de Negócio

| ID | Regra |
|---|---|
| RN01 | Apenas usuários autenticados podem responder questões, fazer simulados, ver desempenho e publicar no fórum. A consulta de questões pode ser feita sem login. |
| RN02 | Toda questão deve ter ano, componente, área de conhecimento, tipo e gabarito oficial (ou padrão de resposta, nas discursivas). Questões do Componente Específico também devem ter curso; as de Formação Geral são comuns a todos os cursos da mesma edição. |
| RN03 | Questões anuladas pelo INEP continuam visíveis para estudo, mas não entram em simulados nem no cálculo de desempenho. |
| RN04 | No simulado, o gabarito só é exibido depois da finalização. |
| RN05 | O tempo do simulado continua correndo mesmo se o estudante sair da tela. Ao zerar, o simulado é finalizado automaticamente com as respostas já marcadas. |
| RN06 | O tempo da prova completa é de 4 horas. No simulado parcial, o tempo é proporcional: 6 minutos por questão. |
| RN07 | Depois de finalizado, um simulado não pode ter as respostas alteradas. O estudante pode fazer um novo simulado. |
| RN08 | Percentual de acertos = questões objetivas corretas ÷ questões objetivas respondidas. Questões em branco aparecem à parte, e discursivas não entram no cálculo. |
| RN09 | O desempenho por área considera a área de conhecimento cadastrada em cada questão. |
| RN10 | Toda mensagem do fórum fica vinculada a uma questão e ao autor. Mensagens com 3 ou mais denúncias ficam ocultas até a análise do administrador. |
| RN11 | Apenas administradores podem cadastrar, editar ou remover questões. Professores só podem editar comentários de gabarito das questões das áreas sob sua responsabilidade. |
| RN12 | Relatórios para a coordenação só mostram dados agregados de grupos com pelo menos 5 estudantes. |
| RN13 | Todo cadastro feito pela tela pública cria um usuário com perfil Estudante. O perfil nunca é escolhido no cadastro público. |
| RN14 | Apenas um Administrador pode alterar perfis, áreas de professor ou status de contas. |
| RN15 | O sistema impede que o último Administrador ativo seja rebaixado ou desativado. |
| RN16 | Um administrador não pode alterar o próprio perfil nem desativar a própria conta. |
| RN17 | Contas não são apagadas pela interface, apenas desativadas. Uma conta desativada não consegue entrar, mas seus dados e respostas continuam no histórico. |
| RN18 | A gestão de usuários exibe apenas dados cadastrais (nome, e-mail, curso, perfil, áreas, status e datas), nunca respostas, simulados ou desempenho. |
| RN19 | Um professor precisa ter pelo menos uma área atribuída. Sem área, ele não acessa nenhum comentário. |
| RN20 | Um comentário de gabarito só é exibido ao estudante depois de publicado. Enquanto estiver em rascunho, o estudante vê "Comentário em elaboração". |
| RN21 | Uma questão que já foi respondida por estudantes (no modo estudo ou em simulados) não pode ser removida, apenas anulada, para preservar o histórico. |

---

## 9. Backlog Priorizado

**P1:** essencial para o MVP · **P2:** importante · **P3:** evolução

| ID | História | Prioridade | RF |
|---|---|:---:|---|
| US01 | Como estudante, quero criar minha conta para salvar meu progresso | P1 | RF01 |
| US02 | Como usuário, quero entrar e sair da minha conta | P1 | RF02 |
| US03 | Como usuário, quero recuperar minha senha quando esquecê-la | P1 | RF03 |
| US04 | Como estudante, quero filtrar questões por curso e área para estudar o que preciso | P1 | RF04, RF05 |
| US05 | Como estudante, quero responder uma questão e saber na hora se acertei | P1 | RF06 |
| US06 | Como estudante, quero ler o comentário da questão para entender meu erro | P1 | RF08 |
| US07 | Como estudante, quero fazer um simulado cronometrado para treinar no tempo da prova | P1 | RF09, RF10, RF11, RF12 |
| US08 | Como estudante, quero ver o resultado do simulado com a correção | P1 | RF14 |
| US09 | Como estudante, quero ver meu desempenho por área para saber o que revisar | P1 | RF15 |
| US10 | Como administrador, quero cadastrar e classificar questões para alimentar o banco | P1 | RF19 |
| US11 | Como administrador, quero cadastrar comentários das questões | P1 | RF20 |
| US12 | Como estudante, quero retomar um simulado interrompido | P2 | RF13 |
| US13 | Como estudante, quero ver a evolução das minhas notas | P2 | RF16 |
| US14 | Como estudante, quero discutir uma questão com outros estudantes | P2 | RF17 |
| US15 | Como administrador, quero moderar mensagens denunciadas | P2 | RF18 |
| US16 | Como estudante, quero responder discursivas e comparar com o padrão de resposta | P2 | RF07 |
| US17 | Como coordenador, quero ver o desempenho médio do curso por área | P3 | RF21 |
| US18 | Como administrador, quero gerenciar usuários, perfis e as áreas dos professores para controlar quem pode fazer o quê no sistema | P2 | RF22 |

### 9.1 Critérios de aceitação (histórias P1)

**US01 — Criar conta**
- Dado que informei nome, e-mail válido, senha com pelo menos 8 caracteres e curso, quando confirmo o cadastro, então a conta é criada e eu entro no sistema.
- Dado que o e-mail já está cadastrado, quando tento me cadastrar, então vejo a mensagem "E-mail já cadastrado" e a conta não é criada.

**US02 — Entrar e sair**
- Dado que informei e-mail e senha corretos, quando clico em Entrar, então acesso a tela inicial.
- Dado que errei a senha, quando clico em Entrar, então vejo uma mensagem de erro que não diz qual dos dois campos está errado.

**US03 — Recuperar senha**
- Dado que informei um e-mail cadastrado, quando solicito a recuperação, então recebo um link válido por 1 hora.
- Dado que o link expirou, quando tento usá-lo, então sou orientado a pedir um novo.

**US04 — Filtrar questões**
- Dado que selecionei curso e área, quando aplico o filtro, então só aparecem questões que atendem aos dois critérios.
- Dado que nenhuma questão atende ao filtro, então vejo a mensagem "Nenhuma questão encontrada".

**US05 — Responder questão**
- Dado que marquei uma alternativa, quando confirmo, então vejo se acertei e qual é a alternativa correta.
- Dado que não marquei nenhuma alternativa, então o botão Confirmar fica desabilitado.

**US06 — Ler comentário**
- Dado que respondi a questão, então o comentário aparece abaixo da correção.
- Dado que a questão ainda não tem comentário, então vejo "Comentário em elaboração" e o link para o fórum.

**US07 — Simulado cronometrado**
- Dado que escolhi a prova completa, quando inicio, então o cronômetro começa em 4h00 e aparecem 40 questões.
- Dado que o tempo zerou, então o simulado é finalizado automaticamente e sou levado ao resultado.
- Dado que estou no meio do simulado, então não consigo ver o gabarito de nenhuma questão.

**US08 — Resultado do simulado**
- Dado que finalizei o simulado, então vejo acertos, erros, questões em branco e tempo utilizado.
- Dado que estou no resultado, quando clico em uma questão, então vejo minha resposta, o gabarito e o comentário.

**US09 — Desempenho por área**
- Dado que respondi questões de pelo menos uma área, então vejo meu percentual de acertos por área em um gráfico.
- Dado que ainda não respondi nenhuma questão, então vejo um convite para começar a estudar.

**US10 — Cadastrar questões**
- Dado que sou administrador, quando cadastro uma questão sem área ou sem gabarito, então o sistema não permite salvar.
- Dado que marquei uma questão como anulada, então ela deixa de aparecer em novos simulados.

**US11 — Cadastrar comentários**
- Dado que sou administrador, quando salvo um comentário, então ele passa a aparecer para os estudantes após a resposta.

### 9.2 Critério de priorização

Ficaram como P1 as funcionalidades sem as quais o sistema não cumpre seu objetivo principal: acesso, banco de questões, correção comentada, simulado e desempenho por área. A gestão de questões e de comentários também entrou como P1, porque sem ela o banco não tem conteúdo. Fórum, histórico e discursivas agregam valor, mas o estudante já consegue se preparar sem eles. O relatório para a coordenação ficou como P3 porque depende de uma decisão sobre privacidade que ainda precisa ser validada.

Depois das entrevistas (seção 5), as regras de privacidade do relatório foram confirmadas, mas ele continua P3 até haver entrevista com a coordenação. O histórico de evolução (US13) e a autoavaliação das discursivas (US16) foram pedidos pelos 3 estudantes entrevistados e são os principais candidatos a subir de prioridade na próxima revisão do backlog.

---

## 10. Diagrama de Casos de Uso

```mermaid
flowchart LR
    V(["👤 Visitante"])
    U(["👤 Usuário"])
    E(["👤 Estudante"])
    A(["👤 Administrador"])
    P(["👤 Professor"])
    C(["👤 Coordenador"])

    E ==>|é um| U
    A ==>|é um| U
    P ==>|é um| U
    C ==>|é um| U

    subgraph SIS["Sistema de Apoio ao ENADE"]
        UC01(["Cadastrar-se"])
        UC02(["Autenticar-se"])
        UC03(["Recuperar senha"])

        UC04(["Consultar questões"])
        UC05(["Filtrar questões"])
        UC06(["Responder questão<br/>(modo estudo)"])
        UC07(["Ver gabarito comentado"])

        UC08(["Realizar simulado"])
        UC09(["Montar simulado"])
        UC10(["Finalizar simulado"])
        UC11(["Ver resultado"])
        UC12(["Retomar simulado"])

        UC13(["Consultar desempenho"])
        UC14(["Consultar histórico"])

        UC15(["Visualizar fórum"])
        UC16(["Publicar mensagem"])
        UC17(["Denunciar mensagem"])

        UC18(["Gerenciar questões"])
        UC19(["Moderar fórum"])
        UC20(["Comentar gabarito"])
        UC21(["Consultar relatório<br/>do curso"])
        UC22(["Gerenciar usuários"])
        UC23(["Atribuir áreas<br/>ao professor"])
    end

    V --> UC01
    V --> UC04
    U --> UC02
    E --> UC04
    E --> UC06
    E --> UC08
    E --> UC13
    E --> UC15

    A --> UC18
    A --> UC19
    A --> UC20
    P --> UC20
    C --> UC21
    A --> UC22

    UC03 -.->|"«extend»"| UC02
    UC05 -.->|"«extend»"| UC04
    UC07 -.->|"«extend»"| UC06

    UC08 -.->|"«include»"| UC09
    UC08 -.->|"«include»"| UC10
    UC10 -.->|"«include»"| UC11
    UC12 -.->|"«extend»"| UC08

    UC14 -.->|"«extend»"| UC13

    UC16 -.->|"«extend»"| UC15
    UC17 -.->|"«extend»"| UC15

    UC23 -.->|"«extend»"| UC22
```

> Diagrama em Mermaid, que o GitHub renderiza nativamente. Como o Mermaid não tem notação UML própria para casos de uso, a convenção adotada é: atores e casos de uso em formas arredondadas, generalização com seta grossa (`é um`) e `«include»`/`«extend»` com seta tracejada.

**Observações sobre o modelo**

- O ator **Visitante** representa quem ainda não entrou no sistema: ele consulta questões sem login (RN01) e pode se cadastrar, tornando-se Estudante (RN13).
- O ator **Usuário** generaliza os demais, e por isso "Autenticar-se" fica ligado a ele uma única vez.
- **Ver gabarito comentado** estende **Responder questão** apenas no modo estudo. No simulado, a correção aparece dentro de **Ver resultado**, depois da finalização (RN04).
- O controle de tempo não aparece como caso de uso, porque é um comportamento do sistema e não um objetivo do ator. Ele está descrito em RF10, RF12, RN05 e RN06.
- **Gerenciar usuários** (UC22) é exclusivo do Administrador (RN14). **Atribuir áreas ao professor** (UC23) estende esse caso quando o perfil escolhido é Professor (RN19).
- O ator **Professor** e o caso UC20 foram validados na entrevista E04, com acesso restrito às áreas sob sua responsabilidade. O ator **Coordenador** e o caso UC21 foram validados parcialmente, pois não houve entrevista com coordenação (seção 5.4).

---

## 11. Diagrama de Componentes

```mermaid
flowchart TB
    subgraph CLI["Clientes"]
        WEB["Aplicação Web"]
        APP["Aplicação Mobile"]
    end

    subgraph BACK["Backend"]
        API["API Gateway"]
        AUTH["Autenticação"]
        QST["Questões"]
        SIM["Simulados"]
        DES["Desempenho"]
        FOR["Fórum"]
    end

    DB[("Banco de Dados")]
    MAIL{{"☁️ Serviço de E-mail"}}

    WEB -->|REST/HTTPS| API
    APP -->|REST/HTTPS| API

    API --> AUTH
    API --> QST
    API --> SIM
    API --> DES
    API --> FOR

    SIM -->|obtém questões| QST
    DES -->|lê resultados| SIM
    FOR -->|vincula à questão| QST
    AUTH -->|recuperação de senha| MAIL

    AUTH --> DB
    QST --> DB
    SIM --> DB
    DES --> DB
    FOR --> DB
```

| Componente | Responsabilidade |
|---|---|
| Aplicação Web / Mobile | Interface com o usuário |
| API Gateway | Ponto único de entrada, roteamento e validação do token de acesso |
| Autenticação | Cadastro, login, recuperação de senha e perfis de acesso |
| Questões | Banco de questões, filtros, gabaritos e comentários |
| Simulados | Montagem, cronômetro, salvamento automático e correção |
| Desempenho | Cálculo de estatísticas e histórico |
| Fórum | Mensagens, denúncias e moderação |
| Serviço de E-mail | Serviço externo para envio de e-mails transacionais |
| Banco de Dados | Persistência de todos os dados |

---

## 12. Diagrama de Implantação

```mermaid
flowchart LR
    subgraph DEV["Dispositivo do usuário"]
        subgraph NAV["Navegador"]
            WEB["📄 Aplicação Web (SPA)"]
        end
        subgraph MOB["Android / iOS"]
            APP["📄 App Mobile"]
        end
    end

    subgraph SRV["Servidor de Aplicação"]
        BE["📄 Backend (API + serviços)"]
    end

    subgraph DBS["Servidor de Banco de Dados"]
        DB[("Banco relacional")]
    end

    MAIL{{"☁️ Provedor de E-mail"}}

    WEB -->|HTTPS| BE
    APP -->|HTTPS| BE
    BE -->|"TCP/SQL (rede privada)"| DB
    BE -->|SMTP/TLS| MAIL
```

O cliente (web ou mobile) se comunica com o servidor de aplicação somente por HTTPS. O banco de dados fica em rede privada, acessível apenas pelo servidor de aplicação. O envio de e-mails é feito por um provedor externo. Tecnologias e hospedagem serão definidas nas próximas etapas.

---

## 13. Matriz de Rastreabilidade

| Necessidade | Requisitos | Histórias | Casos de uso |
|---|---|---|---|
| N01 — Encontrar questões organizadas | RF04, RF05, RF19 | US04, US10 | UC04, UC05, UC18 |
| N02 — Praticar em condição de prova | RF09–RF14 | US07, US08, US12 | UC08–UC12 |
| N03 — Entender os erros | RF06, RF07, RF08, RF20 | US05, US06, US11, US16 | UC06, UC07, UC20 |
| N04 — Saber o que estudar | RF15, RF16, RF21 | US09, US13, US17 | UC13, UC14, UC21 |
| N05 — Discutir questões | RF17, RF18 | US14, US15 | UC15–UC17, UC19 |
| N06 — Dados protegidos | RF01–RF03, RF22, RNF03, RNF04, RN12, RN13–RN18 | US01–US03, US18 | UC01–UC03, UC22 |
| N07 — Estudar em sessões curtas e pelo celular | RF09, RF13, RNF02 | US07, US12 | UC08, UC09, UC12 |
| N08 — Manter a rotina e saber o que revisar | RF15, RF16 (metas e plano de estudo ainda a especificar) | US09, US13 | UC13, UC14 |
| N09 — Colaboração docente nos comentários | RF20, RF22, RN11, RN19, RN20 | US11, US18 | UC20, UC22, UC23 |

---

## 14. Conclusão

Esta primeira etapa definiu o problema, os envolvidos, o escopo e um conjunto inicial de requisitos, regras e modelos para o Sistema de Apoio ao ENADE. Considerar desde o início a estrutura real da prova (questões discursivas, tempo de 4 horas e questões anuladas) evitou um modelo que tratasse todas as questões como objetivas.

As entrevistas com 3 estudantes e 1 professor (seção 5) confirmaram a maior parte da especificação, validaram a retomada de simulado e a participação de professores (restrita à sua área) e reforçaram a privacidade dos resultados individuais. Também trouxeram duas necessidades novas, estudo em sessões curtas pelo celular (N07) e apoio à rotina com metas e plano de estudo (N08), e aumentaram a importância do histórico de evolução (RF16) e da autoavaliação das discursivas (RF07). O relatório da coordenação continua dependendo de uma entrevista com coordenação.
