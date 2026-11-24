# SAFIRA 3.1.0 — relatório de entrega e QA

Data: 26/10/2026. Desenvolvimento em `SF-V3.1.0`; base funcional consultada em `SF-V3.0.0`. Testes somente com perfis sintéticos. Nenhuma credencial pessoal utilizada.

## Diagnóstico e resultado

A versão anterior repetia tabelas/toolbar e controles padrão, com pouca hierarquia entre cadastro, dashboard e relatórios. A reconstrução inclui shell, login, sidebar agrupada, Home com composição própria e biblioteca visual compartilhada. Azul-safira, violeta/ciano, superfícies profundas, cores semânticas, Segoe UI e números monetários Consolas estão centralizados em tokens.

As 14 telas integradas são Home, Contas, Categorias, Métodos, Movimentações, Transferências, Cartões, Faturas, Compromissos, Investimentos, Planejamento, Notificações, Relatórios e Configurações. Cartões/compras usam abas; configurações usam painéis por finalidade. Home e Relatórios têm composições distintas e consomem os serviços existentes.

Botões, campos, seletores, calendário, menus, grade Canvas, cards, gráficos, modais, mensagens, detalhes e toasts compartilham o tema. Treeview e menus/confirmacões destoantes foram substituídos. Seletores de arquivos e molduras de janelas permanecem do Windows. Movimento inclui hover, seleção, submenu, títulos, modais, cards, gráficos e toasts, com cancelamento e modo reduzido persistente. Documentação técnica: SAFIRA_DESIGN_SYSTEM.md, UI_COMPONENTS.md e MOTION_SYSTEM.md.

## Evidência de verificação

| Verificação | Resultado |
|---|---|
| `python -B -m pytest -q` | 53 testes aprovados em 11,24 s na execução final |
| Preservação do motor | Hashes dos nove módulos financeiros/infraestrutura idênticos à base; teste incluído nos 53 |
| `tests/ui_smoke.py` com exceções do guard propagadas | PASS: 14 telas, cadastro de conta, movimentação, cartão de débito, compra, compromisso e pagamento; duas geometrias |
| `tests/ui_redesign_qa.py` | PASS: 14 telas, nove combinações de geometria/escala, 80 alternâncias rápidas, submenu, formulário inválido, calendário, seletor, teclado/seleção da grade, vazio, preferência e bloqueio |
| Geometrias/escala do stress | 1366×768, 1600×900 e 1920×1080 com widgets em 100%, 125% e 150% |
| Grade com 10.000 registros sintéticos | 305,99 ms para carregar/desenhar; 110 itens Canvas; sem milhares de widgets |
| Callbacks/animações | Zero exceções capturadas e zero jobs Motion após bloqueio |
| Fonte `main.py --check` | PASS em perfil descartável |
| Executável `SAFIRA.exe --check` | Exit code 0 em perfil descartável |
| PyInstaller final | Build concluído em `dist/3.1.0/SAFIRA` |

A medição de grade cobre o modelo em memória e desenho inicial; não mede consulta SQLite, importação, tempo de toda a aplicação nem FPS. Pode variar com carga e disco. Métricas brutas em `artifacts/ui-qa-metrics.json`. O stress usa movimento reduzido durante a bateria de escalas para isolar layout, e reativa movimento na navegação rápida. Dumps periódicos do faulthandler são diagnósticos de progresso, não falhas de asserção; a execução final terminou com PASS.

Inspeção visual interativa realizada durante o desenvolvimento em Windows 11 com DPI físico de 125%, em Home, Movimentações e formulário. Corrigidos overflow inicial da janela/modal, colunas monetárias fora do viewport e geometria de popovers. O desktop ficou bloqueado pelo Windows na tentativa de captura final adicional; não foi tentado desbloqueá-lo. A inicialização empacotada foi validada por `--check`, sem nova inspeção interativa do executável final.

## Problemas corrigidos

- Colisão de atributo `_hover` com o CTkButton: animação agora usa método próprio.
- Reentrada de layout durante DPI: adaptador local de scrollbar evita flush síncrono do CTk 6, sem modificar dependência instalada.
- Seleção por posição, colunas e scroll: identidade estável, larguras responsivas, seleção filtrada segura e rolagem horizontal no tamanho mínimo.
- Reconstrução excessiva: dashboard conserva widgets; sidebar só anima itens que mudaram; frações de scroll repetidas não redesenham.
- Ciclo de vida: cancelamento Motion, callbacks de imagem e inscrições globais do scroll liberados ao destruir componentes.
- Uma cópia de arquivo de timezone falhou pontualmente no primeiro build final; repetição da etapa de distribuição concluiu e o pacote passou `--check`.

## Limites e pendências reais

As duas imagens de referência citadas no briefing não foram anexadas. Mantida marca textual SAFIRA, sem escolher arbitrariamente uma logo de ARTES. Homologação em outros monitores físicos/DPI e avaliação completa com leitores de tela continuam pendentes. As geometrias do stress são lógicas; o Windows pode limitar a janela ao monitor disponível. Canvas/CustomTkinter não expõem toda a semântica necessária a leitores de tela; não se declara acessibilidade integral. Não foi realizado ensaio prolongado em máquina de baixa capacidade nem teste de instalação em Windows limpo.

Não houve alteração de esquema, cálculos, contratos ou diretório padrão financeiro. `reports.py` muda somente a versão do rodapé. Preferências de apresentação usam JSON separado. Os limites financeiros da V3.0 continuam descritos em README/FINANCIAL_RULES. Pacote em pasta, sem instalador ou assinatura digital.

## Executar e gerar build

Abrir `Iniciar-SAFIRA.cmd` ou `dist/3.1.0/SAFIRA/SAFIRA.exe`, mantendo `_internal` junto ao executável. Por fonte: `.\.venv\Scripts\python.exe main.py`. Build: `.\scripts\build.ps1`, a partir de `J:\PROJETOS\PROJETO-SAPPHIRE\SF-V3.1.0`. Instruções de ambiente e dados existentes no README.

## Ajuste de navegação — 04/11/2026

Transferências movida para o submenu de Movimentações, antes de Categorias e Métodos. Altura expandida ajustada para três itens; selecionar Transferências também expande o submenu automaticamente.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/sidebar-transfer-20261104`: **53 testes aprovados em 7,92 s**, incluindo hashes do motor contra FINANCIAL_ENGINE_BASELINE.json. Execução em Linux com Python 3.13.5; não substitui homologação no Python 3.12/Windows exigido pelo projeto. Tentativa de conferir o widget real bloqueada por `TclError: couldn't connect to display ":0"`; layout e interação visual desta alteração permanecem sem validação gráfica nesta sessão.

## Remoção da faixa superior — 04/11/2026

Removido do shell compartilhado o cabeçalho com “Seu espaço / …” e data. O conteúdo de todas as páginas passa a ocupar diretamente o topo, mantendo o título e o espaçamento próprio da tela. Removida também a atualização do breadcrumb na navegação.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/header-removal-20261104`: **53 testes aprovados em 7,22 s**, incluindo comparação dos hashes financeiros com o baseline. Ambiente Linux/Python 3.13.5; validação no Python 3.12/Windows e inspeção visual continuam pendentes. Não houve nova validação gráfica nesta sessão (display indisponível na tentativa anterior).

## Grupos expansíveis da sidebar — 04/11/2026

Organização e Perspectivas passam de títulos estáticos a menus expansíveis com seta, seguindo a hierarquia visual de Movimentações. Organização contém Cartões, Faturas, Compromissos e Investimentos; Perspectivas contém Planejamento, Notificações e Relatórios. Ambos começam recolhidos, abrem pelo título ou seta e expandem automaticamente ao navegar para uma página interna. O grupo da página ativa recebe destaque. Widgets são criados uma vez; animações usam canais independentes do Motion e respeitam movimento reduzido.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/sidebar-groups-20261104`: **53 testes aprovados em 7,38 s**, incluindo os hashes do baseline financeiro. Linux/Python 3.13.5; homologação em Python 3.12/Windows e inspeção visual dos grupos permanecem pendentes por indisponibilidade de display nesta sessão.

## Categorias por tipo — 04/11/2026

Adicionado seletor Despesas/Receitas à direita da linha de filtros de Categorias. Inicia em Despesas e filtra os registros recebidos do serviço, combinando com Ativos/Inativos/Todos. Novo cadastro sugere o tipo da aba selecionada. Métodos mantém a listagem existente. Grade e serviços financeiros preservam seus contratos.

Validação: 53 testes aprovados em 6,20 s com `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/category-kind-20261104`, incluindo baseline financeiro. Verificação adicional de Catalog.refresh com dados sintéticos em memória: separação dos dois tipos, manutenção do parâmetro de estado e ausência de filtro de tipo em Métodos aprovadas. Linux/Python 3.13.5; inspeção visual e homologação Python 3.12/Windows pendentes, display indisponível nesta sessão.

## Categoria dependente do tipo na nova movimentação — 04/11/2026

Nova movimentação inicia com “Selecione Despesa ou Receita”, sem categoria visível. Ao escolher o tipo, o campo Categoria aparece com apenas categorias ativas daquele tipo. Trocar o tipo limpa a categoria anterior e atualiza as opções; retornar ao placeholder oculta o campo. Form passa a guardar referências aos rótulos para controlar a visibilidade sem reconstruir os widgets. Transferências e edição de operações mantêm seus formulários.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/movement-category-20261104`: **53 testes aprovados em 6,96 s**, incluindo hashes financeiros. Linux/Python 3.13.5. A suíte não comprova visualmente o novo fluxo dependente; inspeção gráfica e homologação Python 3.12/Windows seguem pendentes por indisponibilidade do display nesta sessão.

## Cliques nos seletores dentro de formulários — 04/11/2026

Identificado Popover sem grab próprio enquanto o formulário pai mantém grab modal. O popup agora assume grab e foco ao ser mapeado (com verificação after_idle para janela já mapeada), permitindo receber os cliques em suas opções. O fechamento continua restaurando o grab anterior. Correção compartilhada pelos seletores e calendários.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/popover-grab-final-20261104`: **54 testes aprovados em 6,24 s**, incluindo baseline financeiro e novo teste da ativação do grab/foco, ignorando eventos Map de widgets filhos. O teste usa objetos simulados; clique real na janela ainda não foi validado nesta sessão sem display acessível. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Fundos de controles arredondados — 04/11/2026

Sidebar: superfície da linha e botão de expansão acompanham o estado selecionado, eliminando o bloco escuro atrás da seta. Indicador usa o fundo da linha. Popover: removida a base retangular na cor BORDER; agora resolve a superfície opaca do contêiner de origem para compor o entorno do conteúdo arredondado, tanto nos seletores quanto no calendário. A janela nativa continua retangular: trata-se de composição por cor, não transparência/recorte nativo, e fundos heterogêneos sob o popup ainda exigem inspeção gráfica.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/rounded-surfaces-20261104`: **54 testes aprovados em 7,94 s**, incluindo baseline financeiro. Linux/Python 3.13.5; não houve inspeção visual por indisponibilidade do display. Homologação Python 3.12/Windows pendente.

## Revisão do arredondamento após retorno visual — 04/11/2026

A captura do usuário mostrou que combinar cores não resolveu: janela de popup continuava retangular e a seta cobria a borda do item. Retirado o preenchimento adicional da linha da sidebar e recuada a seta para dentro do botão. Adicionado window_shape.py para recortar efetivamente a janela sem moldura: região arredondada via SetWindowRgn no Windows e X Shape no Linux/X11, atualizada com a geometria do popup. Raio convertido pela escala real da janela. Sem X Shape disponível, mantém a composição por cor existente.

A validação gráfica do recorte nativo permanece pendente: esta sessão não tem display acessível. Não considerar a aparência corrigida como homologada somente pela suíte Python. Testes da suíte cobrem regressões existentes, não o resultado do compositor nativo.

Suíte: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/native-round-20261104`: **54 testes aprovados em 6,51 s**, incluindo hashes financeiros. Linux/Python 3.13.5; Python 3.12/Windows pendente.

## Hover unificado da linha e seta — 04/11/2026

Captura do usuário isolou a diferença entre hover do título e o fundo retangular da seta sobreposta. SidebarButton agora delega hover/pressão à linha SidebarItem; uma única animação por canal pinta simultaneamente o botão principal e fg/bg/borda da seta. Ao cruzar do título para a seta, a saída consulta a posição do ponteiro na linha antes de remover hover. Aplica-se a Movimentações, Organização e Perspectivas. A seta mantém comando próprio e não recebe borda de foco retangular (border_width=0); o botão principal mantém o comportamento de foco existente.

Validação: suíte completa existente **54 aprovados em 6,56 s**, baseline financeiro incluído (`--basetemp=.test-tmp/sidebar-hover-20261104`). Após adicionar regressão da pintura sincronizada, `tests/test_ui_design.py`: **7 aprovados em 0,08 s**. Teste confirma fg/bg/borda da seta iguais à superfície principal para cores distintas, sem comprovar renderização nativa. Linux/Python 3.13.5; inspeção visual e homologação Python 3.12/Windows pendentes por display indisponível.

## Fechar seletores ao clicar fora — 04/11/2026

Popover passa a tratar ButtonPress-1 comparando coordenadas de tela com os limites reais da janela. Clique externo fecha somente o popup e consome o evento; não confirma seleção nem aciona controles atrás. O fechamento restaura o grab anterior, mantendo formulários como Nova movimentação abertos. Clique interno mantém seleção normal. Aplica-se aos menus e calendários que compartilham Popover.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/popover-dismiss-20261104`: **56 testes aprovados em 7,57 s**, incluindo baseline financeiro e regressão para cliques internos e externos nas quatro bordas. Teste com coordenadas simuladas; interação gráfica real pendente por display indisponível. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Movimentações em duas tabelas — 04/11/2026

Listagem de Movimentações separada verticalmente em Receitas e Despesas, identificadas por títulos. Coluna Tipo removida. As duas grades compartilham os filtros e preservam virtualização, identidade e navegação/rolagem independentes. Selecionar registro de uma grade limpa a seleção da outra e direciona Editar, Cancelar e Detalhes à grade ativa. Transferências mantém grade única, também sem a coluna redundante Tipo. Widgets criados uma vez; refresh apenas particiona os registros retornados pelo serviço.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/split-movements-final-20261104`: **57 testes aprovados em 4,88 s**, incluindo baseline financeiro e regressão de seleção exclusiva/direcionamento da grade ativa. Inspeção gráfica, altura das duas tabelas em diferentes geometrias e interação real permanecem pendentes (display indisponível nesta sessão). Ambiente Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Direção das setas dos indicadores — 04/11/2026

Corrigida a associação dos ícones nos cards da Home: Receitas usa up (verde) e Despesas usa down (vermelho), conforme solicitado. Valores e cálculos não alterados.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/kpi-arrows-20261104`: **57 testes aprovados em 4,51 s**, incluindo baseline financeiro. Inspeção visual pendente nesta sessão sem display. Ambiente Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Título do gráfico de saldo — 04/11/2026

Título alterado de “Evolução do caixa” para “Saldo por mês (mês atual até hoje)”, explicitando a granularidade mensal e o mês corrente parcial. Alteração apenas textual, sem mudança de dados ou cálculos. Conferido no código; suíte não repetida para esta troca de texto. Inspeção visual pendente nesta sessão.

## Escopo de contas na Home — 04/11/2026

Adicionado seletor Somente contas ativas / Todas as contas abaixo do período da Home, iniciando em ativas. O escopo afeta indicadores, saldo disponível, patrimônio, previsão, gráfico mensal, categorias, caixa, atividade recente e radar. A seleção é mantida enquanto a tela existe; não altera preferências persistidas, contas, operações ou esquema. Aviso visível esclarece que Relatórios e PDF continuam incluindo todas as contas.

Nova camada safira/dashboard_view.py fornece fontes de leitura por conta ativa usando CTEs locais à consulta, sem criar views persistentes. Reutiliza Analytics e Finance existentes; os módulos do baseline não foram editados. Cartões são associados à conta de vínculo. Pagamentos de faturas continuam completos mesmo quando feitos por uma conta posteriormente arquivada, evitando inflar a dívida de cartões ainda no escopo. Transferências mantêm o efeito na conta ativa remanescente e continuam fora de receitas/despesas. Geração de recorrências permanece a chamada já utilizada pela previsão existente.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/dashboard-scope-final-20261104`: **60 testes aprovados em 6,06 s**, incluindo hashes do baseline. Novos testes com bancos sintéticos conferem exclusão de saldos/movimentações/categorias/obrigações arquivadas, saldo mensal e previsão, visão completa preservada, nenhuma conta ativa, transferência entre conta ativa e arquivada, consumo e dívida de cartão com pagamento por conta arquivada. Testes não acessam banco pessoal. Inspeção gráfica e homologação Python 3.12/Windows pendentes; execução Linux/Python 3.13.5, sem display acessível nesta sessão.

## Reposicionamento do filtro da Home — 04/11/2026

Seletor de contas movido para dentro da barra de período, alinhado à direita com margem de 16 unidades CTk. Removida a linha explicativa externa, eliminando as duas linhas adicionais acima dos cards. Comportamento do filtro e abrangência de Relatórios/PDF mantidos.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/home-filter-position-20261104`: **60 testes aprovados em 7,28 s**, incluindo baseline financeiro. Inspeção visual do alinhamento e largura em janelas menores permanece pendente por indisponibilidade do display. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Cabeçalho e alinhamento da Home — 04/11/2026

Exportar PDF e Nova movimentação movidos para a direita da linha do título da Home. Toolbar vazia deixa de ocupar a linha abaixo do subtítulo, subindo período e dashboard. Card de saldo usa SapphireCard sem a margem interna reservada à sombra, alinhando a superfície esquerda e o topo aos demais cards/gráfico. Removida a margem inferior da última linha de indicadores para alinhar sua base à do card de saldo. Relatórios mantém seu cabeçalho próprio.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/home-header-align-20261104`: **60 testes aprovados em 7,99 s**, incluindo baseline financeiro. Sem inspeção visual nesta sessão (display indisponível); alinhamento real e escalas ainda requerem conferência gráfica. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente. Nenhum acesso ao banco pessoal nesta alteração.

## Datas no padrão brasileiro — 04/11/2026

Campos compartilhados exibem e aceitam DD/MM/AAAA; calendário preenche o mesmo formato. SapphireDatePicker.get mantém o contrato ISO para serviços e comparações; insert converte defaults ISO para apresentação. Campo vazio mantém o comportamento anterior. Dia de vencimento de cartão (inteiro 1–31) usa entrada numérica textual, sem ser confundido com data completa. Erros ao ler datas são capturados pelo formulário, exibindo orientação e reabilitando Confirmar.

Movimentações, compras, faturas, compromissos, planejamento, notificações, radar, detalhes de operações e pagamentos exibem datas brasileiras. Rótulos e tooltips de gráficos mensais usam MM/AAAA. Exportação PDF formata período, operações, consumo, previsão, compromissos e faturas sem alterar os dados recebidos. Guia de uso e documentação do componente atualizados. Banco e módulos do baseline não modificados.

Validação: `.venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/dates-br-verified-20261104`: **72 testes aprovados em 5,62 s**, incluindo baseline financeiro. Casos novos: data ambígua dia/mês, ano bissexto, datas inexistentes, contrato ISO do campo, preenchimento brasileiro, campo vazio e recuperação do formulário após erro de data.

PDF sintético em `.test-tmp/dates-br-pdf-20261104/datas-br.pdf`: três páginas renderizadas com pdftoppm e inspecionadas visualmente, datas legíveis sem cortes/sobreposição. Texto extraído por pdftotext confirma período e datas de todas as seções em DD/MM/AAAA, sem datas ISO visíveis. Bases exclusivamente sintéticas em .test-tmp; nenhum acesso ao banco pessoal. Interface gráfica interativa continua sem homologação nesta sessão por display indisponível. Ambiente Linux/Python 3.13.5; homologação Python 3.12/Windows pendente.

## Fundo atrás dos cantos do card de saldo — 05/11/2026

SapphireCard sem sombra tinha um contêiner externo PANEL atrás do conteúdo arredondado SELECTED. O fundo externo era visível nos cantos como um retângulo residual. Contêiner externo sem sombra agora é transparente, permitindo que os cantos do conteúdo usem o fundo da página. Mantidos dimensões, alinhamento, conteúdo e caminho de sombra existente.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q tests/test_ui_design.py --basetemp=.test-tmp/card-corners-focused-20261105`: **9 testes aprovados em 2,60 s**, incluindo comparação do baseline financeiro. Tentativa da suíte completa com autoload padrão teve progresso lento e foi interrompida; não há resultado completo desta execução. Sem inspeção visual interativa nesta sessão. Python 3.12/Windows e resultado gráfico permanecem pendentes. Nenhum acesso ao banco pessoal.

## Nova movimentação compacta em duas colunas — 05/11/2026

Nova movimentação solicita largura de 800 e altura de 710 unidades lógicas, respeitando os limites de tela já calculados por SapphireModal. Layout opcional de Form organiza Conta/Tipo, Valor/Método, Categoria/Estado e Operação/Competência em pares; Descrição e Confirmação ocupam uma linha. Espaçamento vertical menor somente neste layout. Abaixo de 560 unidades CTk de largura útil, campos passam a uma coluna sem recriar widgets. Ordem de criação acompanha a ordem visual. Categoria permanece dependente de Tipo, com ocultação do contêiner e redistribuição da linha. Outros formulários mantêm o layout anterior.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/compact-movement-final-20261105`: **73 testes aprovados em 8,01 s**, incluindo baseline financeiro. Regressão nova verifica pares de campos, descrição em largura total, ocultação/reexibição de categoria e reorganização em largura estreita com widgets simulados. Inspeção gráfica e ensaio em DPI real permanecem pendentes por display indisponível nesta sessão. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente. Banco pessoal não acessado.

## Correção da abertura do formulário compacto — 05/11/2026

Retorno visual do usuário mostrou formulário sem campos e mensagem de erro. Log local consultado apenas nas últimas linhas: AttributeError ao abrir. Revisão da biblioteca confirmou que CTkToplevel inicializa escala de janela, não escala de widget; _layout_fields consultava _get_widget_scaling no modal. Corrigido para obter escala de field_area, o contêiner de widgets. Teste anterior simulava indevidamente escala de widget no modal; ajustado para remover esse atributo e conferir largura física 660 a escala de widget 150%, resultando em 440 unidades lógicas e uma coluna.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/compact-form-scaling-20261105`: **73 testes aprovados em 7,14 s**, incluindo baseline financeiro. Ainda sem validação gráfica interativa; resultado visual precisa ser conferido ao reabrir. Linux/Python 3.13.5; homologação Python 3.12/Windows pendente. Nenhuma alteração/acesso ao conteúdo financeiro do banco pessoal.

## Orçamento, gráfico comparativo e salário recorrente — 05/11/2026

Evolução funcional expressamente solicitada pelo proprietário. Criados calendário offline de Ariquemes/RO, serviço FinancialPlanning e migração aditiva transacional no mesmo SQLite, sem editar os nove módulos do baseline. Orçamento mensal por categoria, cadastro de receita no 5º dia útil sem sábados, domingos e feriados, geração idempotente de operações pendentes e confirmação com valor/data reais. Exceções de expediente configuráveis. Histórico mensal de saldo desceu e a primeira linha da Home recebeu Planejado × Realizado, com escala monetária comum, indicação de excesso e rolagem para todas as categorias. Regras, fontes, limites e comportamento dos backups em PLANNING_CALENDAR.md.

Também corrigido erro preexistente de Notificações: refresh referenciava variável local analytics inexistente. Usa novamente o serviço do controlador. Harness ui_smoke atualizado para escolher o tipo pelo callback do seletor e assim atualizar as categorias dependentes, como na interação real.

### Evidência automatizada

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/planning-final-20261105`: **88 aprovados em 11,78 s**. Inclui preservação dos hashes dos nove módulos, regras do 5º dia útil (feriados nacionais, estaduais, municipais e móvel), exceções, pendências sem alteração de saldo real, confirmação e valor ajustado sem duplicação, geração concorrente e repetida, cancelamento/pausa, conta arquivada, competência e crédito no realizado, ausência de duplicação entre limite e previsão, orçamento zero versus ausência de limite, filtro de contas, migração repetida e roundtrip de backup novo e legado.
- `.venv-linux/bin/python tests/ui_smoke.py` com acesso ao display: **PASS**, navegação nas 14 telas, formulários reais de conta/movimentação/cartão/compra/compromisso/pagamento, redimensionamento e bloqueio.
- `.venv-linux/bin/python tests/ui_planning_qa.py` com acesso ao display: **PASS**, todas as telas, cadastro/edição de limite e criação de salário recorrente pelos formulários, 12 ocorrências pendentes e saldo real inalterado. Verifica cor de excesso no gráfico. Executa geometrias 1000×700/100% e 1280×900/125%, sem exceções de callbacks. Isso não representa mudança física de DPI.

### Evidência visual real

Acesso gráfico foi obtido para esta etapa mediante execução do QA com perfil sintético. Capturas finais retidas em `.test-tmp/planning-ui-retained-02fc2ef38f104403a17fbd3b3ab486d4/`. Inspeção de Home, orçamento, lista de salários, Planejamento, calendário e excesso orçamentário: barras comparativas com valores completos, tabela com doze previsões acessíveis por rolagem, datas brasileiras e ações legíveis. Capturas anteriores imediatas continham regiões ainda não redesenhadas pelo compositor; harness corrigido para aguardar o loop de eventos antes de capturar. Evidência final usa as capturas assentadas, não as incompletas.

Os testes e capturas usam exclusivamente bases sintéticas em .test-tmp. Não foi criado salário ou orçamento no perfil pessoal, nem aplicado manualmente o novo esquema ao banco pessoal. A migração ocorrerá ao consultar as novas funcionalidades após iniciar o aplicativo. Execução em Linux/Python 3.13.5. Homologação em Python 3.12/Windows e outros monitores físicos permanece pendente. Não foi gerado executável nesta etapa.

## Limites fixos com vigência e histórico — 05/11/2026

Limites passaram a valer do mês escolhido em diante, sem repetição manual. Uma alteração substitui as revisões futuras da categoria a partir do mês escolhido e mantém as anteriores. Remover limite cria encerramento a partir daquele mês; não apaga o histórico nem confunde ausência de limite com limite zero.

Migração transacional planning_migrations=2 adiciona planning_budget_rules (categoria/mês inicial/valor, nulo para encerramento). Preserva os snapshots mensais originais em planning_budgets. Na migração dos dados antigos, meses históricos mantêm exatamente seus cadastros, inclusive lacunas sem limite. A partir do mês atual adota-se o último valor conhecido, preservando eventuais alterações futuras previamente cadastradas. Os nove módulos do baseline continuam intactos. Interface informa a vigência tanto na descrição quanto no formulário e na confirmação de remoção. Dados continuam no mesmo SQLite e nos backups completos.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/budget-fixed-final-20261105`: **90 aprovados em 11,48 s**. Inclui testes de herança entre anos, limites antes do primeiro cadastro, mudanças futuras, substituição de agenda futura, limite zero, encerramento/retomada, migração da versão 1 preservando meses antigos sem cadastro, repetição de migração e roundtrip dos backups, além do baseline financeiro.

QA gráfico: `.venv-linux/bin/python tests/ui_planning_qa.py` com perfil sintético: PASS. Conferidos edição de limite pela interface, demais telas, geração de salário, cor de orçamento excedido e escalas lógicas. Capturas retidas em `.test-tmp/planning-ui-retained-6100ab06763341508fbd617bc1f6cf26/`; orçamento inspecionado visualmente com o novo texto de vigência, sem corte. Nenhum acesso ao banco pessoal. Linux/Python 3.13.5; homologação Python 3.12/Windows e DPI físico permanece pendente.

## Aplicação do kit de marca fornecido — 09/11/2026

Aplicados os arquivos recebidos em safira-kit.zip: marca horizontal no login, sidebar e PDF; PNG/ICO nas janelas principal e modais, e na janela de evolução da conta. SAFIRA.spec inclui assets/brand e define favicon.ico como ícone do próximo executável. Arquivos copiados byte a byte; SHA-256 conferido contra o ZIP e registrado em assets/brand/README.md. Respeitadas proporções e fundo opaco original. Nenhuma geração ou edição da marca. Resolução central de caminhos funciona em fonte e em _MEIPASS; imagens CTk reutilizadas em cache.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/brand-kit-complete-20261109`: **91 aprovados em 11,77 s**, incluindo baseline financeiro e teste de assets/formato/caminho congelado. QA gráfico `tests/ui_branding_qa.py`: PASS com perfil exclusivamente sintético, navegação nas 14 páginas e abertura de formulário. Capturas em `.test-tmp/branding-ui-retained-383c0831114b4b76be0ddd0bb7660c0f/`; login e sidebar inspecionados visualmente, marca legível e sem cortes. Ícone nativo configurado no Linux; aparência no Windows e ícone de EXE compilado ainda requerem homologação.

PDF sintético em `.test-tmp/branding-pdf-32f56b2eb8b44e38a7e9a4a0eb646277/brand.pdf`: duas páginas renderizadas por pdftoppm e inspecionadas. Logo íntegra e proporcional no cabeçalho da primeira página; tabelas e paginação legíveis, sem sobreposição. PDF é evidência de QA, não contém dados pessoais. Nenhum acesso ao banco pessoal. Executáveis/builds antigos preservados; nenhum build novo foi gerado nesta etapa. Ambiente Linux/Python 3.13.5; Python 3.12/Windows permanece pendente.

## Atualização para o kit transparente — 09/11/2026

Substituídos os assets ativos pelas versões transparentes recebidas em safira-kit-transparente.zip: marca horizontal, ícones PNG e ICO. Aplicação central abrange login, sidebar, janelas e próximo build. Cópias byte a byte verificadas contra o ZIP; imagens anteriores preservadas como referência. Não houve geração/edição da arte. Proporção da marca transparente ajustada no PDF; base escura do cabeçalho é desenhada pelo relatório para manter legível a escrita branca sobre a página clara.

Validação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/brand-transparent-20261109`: **92 aprovados em 11,52 s**, incluindo baseline financeiro, caminho congelado e canais alpha reais dos assets ativos. QA gráfico `tests/ui_branding_qa.py`: PASS nas 14 páginas e abertura de modal; login/sidebar inspecionados visualmente em `.test-tmp/branding-ui-retained-40b904fca00647688090c725311be4e5/`, sem retângulo opaco atrás da marca e sem cortes. PDF sintético de duas páginas em `.test-tmp/branding-transparent-pdf-cf73fb6f82fc46438ee2e6cd6c987b43/`: renderizado e inspecionado, marca legível sobre a base escura e tabelas sem sobreposição. Nenhum acesso ao banco pessoal. Executáveis antigos preservados; novo build/ícone nativo no Windows não homologados. Linux/Python 3.13.5; Python 3.12/Windows pendente.

## Entrada de build para Windows — 09/11/2026

Criado build.bat na raiz (não havia BAT existente), chamando scripts/build.ps1 com caminho relativo à própria pasta, parâmetros encaminhados, código de saída preservado e pausa no duplo clique. BAT/PS1 salvos em ASCII/CRLF. Script valida Windows/Python 3.12 x64, cria .venv somente quando não existe (sem apagar ambientes inválidos), instala requirements-dev.txt por padrão, confere dependências/assets, executa pytest e --check de fonte, empacota com o spec e verifica o EXE por Start-Process -Wait em perfil descartável. SkipDependencyInstall permite uso de dependências locais; não suprime testes. Variáveis de ambiente e diretório original são restaurados.

Build/cache em build/3.1.0 e saída em dist/3.1.0/SAFIRA. Antes de empacotar, build existente é preservado com nome exclusivo. Em falha no empacotamento/checagem, saída incompleta é preservada e build anterior retorna ao local original quando possível. Não há exclusão de builds antigos, bases pessoais ou diretórios de testes. Execuções --check usam SAFIRA_DATA_DIR exclusivo em .test-tmp; não inicializam a base pessoal. README atualizado com uso, opção offline e execução sem pausa.

Verificações locais: codificação/finais de linha e caminho do BAT conferidos; SAFIRA.spec compilado estaticamente por Python; assets transparentes existentes. Suíte da aplicação: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-linux/bin/python -m pytest -q --basetemp=.test-tmp/windows-build-script-20261109`: **92 testes aprovados em 11,30 s**, incluindo baseline financeiro. Estes testes não executam o BAT/PowerShell. Não há PowerShell, Wine nem Windows nesta sessão Linux; execução real do script, bootstrap da venv, restauração do build anterior e geração/checagem do EXE precisam de validação no Windows. Nenhum build foi gerado ou alterado nesta etapa.
