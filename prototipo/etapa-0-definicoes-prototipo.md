# Protótipo — Etapa 0: Definições

**Sistema:** Sistema de Apoio ao ENADE
**Base:** `sistema-apoio-enade-P1.md`
**Status:** Rascunho para validação do grupo

---

## 1. Objetivo do protótipo

Tornar visíveis os fluxos do MVP para:

- validar com estudantes, professores e coordenação nas entrevistas (seção 5 do documento, ainda vazia);
- conferir se os critérios de aceitação das histórias P1 (§9.1) são atendidos pelas telas;
- encontrar lacunas nos requisitos antes da implementação.

## 2. Fidelidade

| Item | Decisão |
|---|---|
| Nível | **Baixa fidelidade (rascunho / wireframe)** |
| Cores | Apenas tons de cinza; cor só para indicar estado (acerto/erro), se necessário |
| Tipografia | Uma fonte, 3 tamanhos (título, texto, legenda) |
| Imagens | Caixa com "X" e legenda (ex.: `[imagem do enunciado]`) |
| Textos | Rótulos e mensagens reais em português (ex.: "E-mail já cadastrado"); enunciados com texto fictício resumido |
| Interação | Telas estáticas ligadas por setas no mapa de fluxo; navegação clicável fica para a Etapa 6 |

## 3. Plataforma e tamanhos de tela

| Formato | Largura | Uso |
|---|---|---|
| **Mobile (principal)** | 360 px | Todas as telas (RNF02) |
| Desktop | 1280 px | Apenas telas em que o layout muda bastante: banco de questões, simulado, desempenho, admin |

Abordagem *mobile-first*: desenha-se o mobile e depois a adaptação desktop.

## 4. Escopo

### Dentro (MVP — P1)

| História | Telas previstas |
|---|---|
| US01 Criar conta | Cadastro |
| US02 Entrar e sair | Login, menu com "Sair" |
| US03 Recuperar senha | Solicitar link, link enviado, nova senha, link expirado |
| US04 Filtrar questões | Banco de questões com filtros, lista vazia |
| US05 Responder questão | Questão (modo estudo): sem resposta, alternativa marcada, corrigida |
| US06 Ler comentário | Bloco de comentário; estado "Comentário em elaboração" |
| US07 Simulado | Montar simulado, simulado em andamento, mapa de questões, confirmar entrega, tempo esgotado |
| US08 Resultado | Resultado, revisão de questão |
| US09 Desempenho | Painel por área; estado vazio ("comece a estudar") |
| US10 Cadastrar questões | Admin: lista de questões, formulário de questão |
| US11 Cadastrar comentários | Admin: editor de comentário |

### Incluído de forma mínima (para não quebrar fluxos do P1)

- **Discursivas no simulado completo:** campo de texto na prova e padrão de resposta na revisão (parte de US16).
- **Aviso de simulado em andamento** na tela inicial (base para US12, sem o fluxo completo de retomada).
- **Link "Ver discussão"** na questão, apontando para uma tela de fórum ainda não desenhada (US06 exige o link).

### Fora desta rodada

- Fórum completo, denúncia e moderação (US14, US15)
- Histórico e evolução (US13)
- Relatório da coordenação (US17)
- Perfil Professor

## 5. Perfis representados

| Perfil | O que vê no protótipo |
|---|---|
| **Visitante** (não autenticado) | Landing, banco de questões e leitura de questões. Ao tentar responder, é levado ao login (RN01) |
| **Estudante** | Todas as telas de estudo, simulado e desempenho |
| **Administrador** | Área administrativa de questões e comentários |

> O documento não tem o ator **Visitante** no diagrama de casos de uso, mas a RN01 permite consulta sem login. Sugestão: incluir esse ator no diagrama.

## 6. Premissas para pontos em aberto

Decisões provisórias, apenas para conseguir desenhar. Cada uma deve ser confirmada pelo grupo.

| # | Ponto em aberto | Premissa adotada no rascunho | Requisito |
|---|---|---|---|
| P1 | Prova completa com questão anulada | A prova completa usa uma edição específica, sem as anuladas, e mostra o aviso "Esta edição tem N questões anuladas que não fazem parte do simulado". O tempo continua 4h | RN03, RF09 |
| P2 | Fórum durante o simulado | Fórum e comentários **escondidos** até a finalização | RN04 |
| P3 | Discursivas no resultado | Aparecem separadas ("Discursivas: autoavaliação") e não entram no percentual | RN08, RF07 |
| P4 | Sair no meio do simulado | A tela inicial mostra o card "Simulado em andamento — 2h14 restantes" com o botão "Continuar" | RN05, RNF07, RF13 |
| P5 | Ação de responder como visitante | Botões de alternativa aparecem, mas "Confirmar" leva ao login e depois volta para a mesma questão | RN01 |
| P6 | Início do simulado em até 3 cliques | Início → "Novo simulado" → "Prova completa" → "Iniciar" (3 cliques) | RNF01 |
| P7 | Curso do usuário | O banco de questões abre já filtrado pelo curso do cadastro, e o filtro pode ser alterado | RF01, RF04 |

## 7. Dados fictícios de exemplo

Para que as telas pareçam reais e sejam consistentes entre si:

- **Estudante:** Ana Souza, curso Ciência da Computação
- **Edições:** 2017, 2021, 2023 (rótulos ilustrativos)
- **Áreas (componente específico):** Algoritmos, Estruturas de Dados, Banco de Dados, Redes, Engenharia de Software
- **Formação Geral:** Interpretação de texto, Atualidades, Ética e cidadania
- **Desempenho:** Algoritmos 72%, Estruturas de Dados 65%, Banco de Dados 48%, Redes 40%, Eng. de Software 80%, Formação Geral 70%
- **Resultado de simulado:** 22 acertos, 9 erros, 4 em branco, 2 discursivas respondidas, tempo 3h12

## 8. Convenções do rascunho

- Cada tela tem um **código** (`T01`, `T02`…) e um nome.
- Cada tela tem uma **anotação lateral** com os RF/RN/US que ela atende.
- Estados diferentes da mesma tela ganham sufixo: `T07a` (sem resposta), `T07b` (corrigida).
- Mensagens de erro e estados vazios são desenhados como telas próprias, porque são critérios de aceitação.

## 9. Ferramenta (a definir pelo grupo)

| Opção | Prós | Contras |
|---|---|---|
| Papel + foto | Mais rápido, bom para entrevistas | Difícil de editar e versionar |
| Excalidraw | Estilo de rascunho, gratuito, exporta PNG/SVG para o repositório | Pouca navegação clicável |
| Figma (wireframe kit) | Permite evoluir até o protótipo navegável da Etapa 6 | Curva de aprendizado maior |

Sugestão: **Excalidraw** nas Etapas 1–4 e Figma, ou HTML simples, na Etapa 6.

## 10. Próxima etapa

**Etapa 1 — Mapa de telas:** inventário completo com códigos `T01…Tn` e diagrama de navegação entre elas, por perfil.

### Checklist para fechar a Etapa 0

- [ ] Grupo confirma escopo (seção 4)
- [ ] Grupo confirma ou ajusta premissas P1–P7 (seção 6)
- [ ] Ferramenta escolhida (seção 9)
