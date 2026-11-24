# SAFIRA 3.1 - Sapphire Tech Finance

Assinatura: azul-safira sobre superfícies profundas; violeta e ciano em visualização, nunca como ruído permanente. Motor financeiro e esquema inalterados.

## Tokens

Fonte autoritativa: `safira/ui/tokens.py`. Background #090F1B; sidebar #0D1424; surface #121C2D; elevação #19253A; hover #22334D; separadores #27354B. Primário #3478FF, bright #4C8DFF, violeta #8665FF e ciano #27C9EF. Positivo #22D3A0, negativo #FF6078, atenção #F5B942. Texto #F3F7FF, secundário #9BAEC8, discreto #7185A2.

Espaçamento baseado em 8 px, raios de 18 para cards, 16 para KPIs, 11 para campos/botões, cápsulas de 10 para estados. Superfícies selecionadas usam #182E53; nenhuma grade branca ou neon contínuo.

## Tipografia

Segoe UI para títulos/corpo e Consolas para dinheiro, ambas fontes do sistema Windows, sem redistribuir arquivos proprietários nem baixar fontes em runtime. Título 28, saudação/login 26–36, saldo principal 38, estatísticas 23, seção 14–18, corpo 12–13 e metadados 9–11. Os valores usam formatação BRL existente no domínio. Não há nova implementação de cálculo monetário na UI.

## Composição

Sidebar por visão financeira, organização e perspectivas; configurações e sessão no rodapé. Texto e seta de Movimentações têm comandos separados. Item ativo: indicador lateral, ícone e superfície azul suave; inativos sem retângulos repetidos.

Home: saldo disponível destacado, previsto secundário, KPIs compactos, evolução do caixa, distribuição, atividade recente e radar. Relatórios: síntese do período, gráficos e grade completa. Cartões: contexto e abas cartão/compra. Planejamento: real e projetado separados. Configurações: painéis por finalidade. Cadastros compartilham linguagem, não o dashboard inteiro.

## Componentes / interação

Primário cria/confirma; secundário navega/consulta; terciário reduz peso; destrutivo discreto. Hover 150 ms; foco azul visível; pressionado mais escuro; desabilitado não responde; operações demoradas têm progresso e bloqueio de duplicação. Mensagens de validação explicam o erro em texto.

Ícones lineares originais em Python/Pillow, mesma espessura, cache limitado e escala 3x. Não há emojis como ícones nem logo inventada. Marca visual fornecida pelo proprietário em safira-kit.zip (09/11/2026), preservada sem redesenho; assets em assets/brand.

Sombra difusa em RGBA com Pillow, cache LRU de 32 dimensões, atualização com debounce e compensação de DPI. Aplicada ao destaque principal, sem desenhar imagens de toda a interface.

## Acessibilidade e responsividade

Teclado: Tab, Enter, Escape; grade: setas, Home/End e PageUp/PageDown. Estados têm texto além de cor. Linhas monetárias alinham à direita. Grade adapta colunas e mantém rolagem horizontal quando necessário; nenhum registro é descartado. Janela inicial considera escala real do Windows para caber no monitor.

Preferência de reduzir movimento respeita `SPI_GETCLIENTAREAANIMATION` quando disponível. Usuário pode escolher depois em Configurações. Escala de widget 90–150%. Testes lógicos de tamanho e escala não substituem homologação em monitores físicos/DPI diferentes.

Limite: Canvas e CustomTkinter têm exposição limitada a leitores de tela via UI Automation. Não se afirma conformidade completa com tecnologias assistivas; navegação por teclado foi exercitada.
