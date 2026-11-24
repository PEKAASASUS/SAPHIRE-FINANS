# Componentes SAFIRA 3.1

| Componente | Responsabilidade |
|---|---|
| tokens.py | Cores semânticas, fontes, durações e interpolação |
| motion.Motion | Canal de animação por componente com cancelamento e movimento reduzido |
| SapphireButton | Primário/secundário/terciário/destrutivo/ícone, hover/pressão/foco/disabled |
| SapphireInput | Campo consistente com borda de foco e placeholder |
| SapphireSelect / Popover | Menu próprio, sem menu nativo do OptionMenu; valores preservados |
| SapphireDatePicker | Digitação DD/MM/AAAA e calendário mensal local, conversão para ISO ao fornecer o valor aos serviços; setas, seleção, Escape |
| SapphireTabs | Alternância de categorias/estados e cartões/compras |
| SapphireModal / Form | Foco, grab, rolagem, entrada/saída e validação real dos serviços |
| Message / MessageBox | Confirmações, erros e avisos próprios |
| Toast | Feedback após conclusão, entrada breve, fechamento e expiração |
| show_details | Detalhes persistentes em texto selecionável |
| SapphireDataGrid | Canvas virtualizado, identidade estável, seleção/hover/teclado, menu contextual e scrollbar CTk |
| SapphireCard / StatCard | Superfícies e números tabulares, sombra opcional e atualização sem reconstrução |
| Chart | Linha suave, barras arredondadas, anel e tooltip; dados reais fornecidos pelos serviços |
| Period | Dois calendários com ação Aplicar |
| Sidebar / SidebarItem | Agrupamento, ícones, seleção animada e submenu separado |
| Preferences | JSON de apresentação ao lado da base, escrita atômica, sem alteração de esquema |

## Grade

Os registros são mantidos no modelo em memória já retornado pelos serviços. Somente linhas que cruzam o viewport, com pequena margem, são desenhadas. Custo de desenho proporcional às linhas visíveis, não ao total. Não são criados milhares de widgets. `selected()`, `selection_set()` e `see()` preservam os contratos consumidos pelas telas.

Recarga mantém identidade por id, ou origem/id quando necessário; remover por filtro limpa seleção com segurança. Cabeçalho e scroll horizontal ficam sincronizados. Valores monetários à direita; estados em badges textuais; receitas/despesas com indicação cromática e linear. Nenhum limite de registros na tela de Movimentações ou Relatórios. As cinco linhas da Home são uma prévia explicitamente vinculada à listagem completa.

## Limites nativos preservados

`SapphireScrollbar` evita a chamada síncrona a `update_idletasks` do desenho do CTk 6, somente na instância do Canvas. O loop normal do Tk mantém o desenho; isso evita reentrada durante mudanças de escala. `SapphireScrollFrame` remove suas próprias inscrições globais de roda/Shift ao destruir. Botões e labels liberam callbacks de imagens compartilhadas no cache. Não há edição da biblioteca instalada nem alteração global do CTk.

Seletores de arquivos permanecem os diálogos do sistema operacional por integração com filesystem e acessibilidade. Moldura/título de janelas também é administrada pelo Windows. Todo conteúdo de formulários, confirmações e popovers usa o tema SAFIRA. A mensagem fatal de inicialização mantém fallback Tk caso a própria interface não possa iniciar.

## Dados e compatibilidade

Nada de SQL nos componentes. Os nove módulos financeiros/infraestrutura listados em FINANCIAL_ENGINE_BASELINE.json são byte a byte iguais à V3.0.0. `reports.py` altera somente a identificação impressa da versão. `ui-preferences.json` armazena movimento e escala; não é registro financeiro, não muda o local de armazenamento e não participa do backup SQLite. A base, esquema e lock são compartilhados de forma compatível com 3.0; as duas versões não abrem a mesma base simultaneamente.

## Identidade fornecida pelo proprietário (09/11/2026)

`safira/branding.py` resolve assets em fonte e PyInstaller, mantém a proporção da marca horizontal e fornece ícones PNG/ICO para as janelas. Arquivos em `assets/brand` são cópias exatas do kit recebido, com hashes e origem no README da pasta. Login e sidebar usam imagens CTk compartilhadas com liberação dos callbacks pelos labels. A marca também aparece no cabeçalho do PDF e o spec inclui os assets/ícone no próximo build. Fundo opaco faz parte dos originais; não houve redesenho nem remoção de fundo.

Atualização do kit em 09/11/2026: os assets ativos passam a ser as variantes transparentes fornecidas no segundo ZIP. As imagens originais com fundo ficam apenas como referência. PDF mantém base escura para legibilidade da escrita branca.
