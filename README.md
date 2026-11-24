# SAFIRA 3.1.0 - Sapphire Tech Finance

Redesign desktop em CustomTkinter, com funcionalidades e motor financeiro preservados da V3.0.0. Desenvolvimento exclusivamente nesta pasta; versões anteriores e bancos originais não foram alterados.

## Executar

Abra `Iniciar-SAFIRA.cmd` ou `dist/3.1.0/SAFIRA/SAFIRA.exe`. Mantenha toda a pasta do executável, incluindo `_internal`. O launcher usa o código-fonte se o build novo ainda não existir; não executa o binário antigo copiado em dist/SAFIRA.

```powershell
cd J:\PROJETOS\PROJETO-SAPPHIRE\SF-V3.1.0
.\.venv\Scripts\python.exe main.py
```

Ambiente novo: Python 3.12 x64, `py -3.12 -m venv .venv`, seguido de `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`. Pillow é dependência explícita para ícones e sombras; não há fontes ou assets baixados em tempo de execução.

## O que mudou

- Design System com azul-safira, superfícies profundas e acentos violeta/ciano.
- Sidebar com grupos, ícones lineares e seleção lateral; texto e seta independentes.
- Home recomposta: saldo real, KPIs, linha de evolução, distribuição, atividade e radar.
- Treeview removido: grade Canvas virtualizada, seleção por identidade, teclado, badges e alinhamento monetário.
- Filtros integrados, calendário, menus próprios, foco e ações habilitadas conforme seleção.
- Cards, formulários, confirmações, detalhes e toasts personalizados.
- Animações controladas, preferência de reduzir movimento e escala 90–150%.
- Configurações em painéis, cartões/compras em abas e relatórios com composição própria.

Contas, categorias, métodos, receitas/despesas, transferências, cartões/faturas, pagamentos, recorrências, investimentos, planejamento, notificações, PDF e backup/restauração continuam consumindo os mesmos serviços. Nenhum dado de demonstração é inserido na base de uso.

## Dados existentes

Padrão Windows: `%LOCALAPPDATA%\SAFIRA\safira.sqlite`, exatamente como na V3.0.0. `SAFIRA_DATA_DIR` continua disponível para diretório explícito. Esquema e motor não foram modificados; a compatibilidade é conferida por hashes e regressão. O mesmo lock impede duas versões abertas no mesmo diretório. Não foi necessário importar, copiar ou sobrescrever o banco pessoal durante o desenvolvimento.

As preferências visuais ficam em `ui-preferences.json` ao lado da base. Esse arquivo guarda apenas escala e movimento, é opcional e não faz parte do backup financeiro SQLite. Senha continua Argon2id; o banco e os backups continuam sem criptografia em repouso.

## Testes

```powershell
.\scripts\test.ps1
.\.venv\Scripts\python.exe tests\ui_smoke.py
.\.venv\Scripts\python.exe tests\ui_redesign_qa.py
```

Testes financeiros usam bases temporárias na nova pasta. O QA visual abre janelas com dados sintéticos e gera `artifacts/ui-qa-metrics.json`. `tests/ui_preview_v31.py` abre uma prévia descartável; não usa senha nem dados pessoais. Resultados e limites efetivamente verificados ficam em `docs/UI_QA_REPORT.md`.

## Build Windows

```powershell
.\scripts\build.ps1
```

Saída: `dist/3.1.0/SAFIRA/SAFIRA.exe`. Cache separado em `build/3.1.0`; builds copiados anteriormente são preservados. Versão 3.1.0 também nos recursos Windows. O pacote é uma distribuição em pasta, sem instalador e sem assinatura digital.

## Limitações explícitas

As duas imagens mencionadas no prompt não estavam anexadas: o redesign segue a direção textual. Marca SAFIRA textual mantida; não foi escolhido arbitrariamente um dos conceitos em ARTES nem gerada outra logo.

Seleção de arquivos e molduras de janela continuam sob controle do Windows. Canvas/CustomTkinter têm limitações de leitores de tela; teclado e foco foram testados, sem alegação de acessibilidade integral. Escalas de widget e tamanhos lógicos foram exercitados; homologação com outros monitores físicos e DPI real ainda é necessária.

Permanecem os limites financeiros da 3.0: sem juros/rotativo automáticos, antecipação de fatura antes do fechamento, estornos após pagamentos ou investimentos fiscais/avaliações históricas. Investimentos usam avaliação manual. Essas regras não foram alteradas para acomodar o redesign.

## Documentação

- `docs/UI_AUDIT_V3.0.0.md`: diagnóstico.
- `docs/SAFIRA_DESIGN_SYSTEM.md`: tokens, tipografia e composição.
- `docs/UI_COMPONENTS.md`: biblioteca e compatibilidade.
- `docs/MOTION_SYSTEM.md`: durações, cancelamento e movimento reduzido.
- `docs/UI_QA_REPORT.md`: testes, desempenho e pendências.
- `docs/USER_GUIDE.md`, `docs/FINANCIAL_RULES.md`: uso e regras preservadas.

Referências de implementação: [CustomTkinter](https://customtkinter.tomschimansky.com/documentation/), [event loop do Tkinter](https://docs.python.org/3.12/library/tkinter.html#threading-model).

## Planejamento funcional adicionado em 05/11/2026

Orçamento mensal por categoria, gráfico Planejado × Realizado na Home e salário recorrente no 5º dia útil de Ariquemes/RO. Cadastros ficam em tabelas adicionais no próprio SQLite e entram no backup completo. Ocorrências de salário são pendentes e precisam de confirmação; orçamento não movimenta saldo. Os nove módulos do baseline financeiro permanecem intactos. Uso, fontes de calendário, limites e migração em `docs/PLANNING_CALENDAR.md`.

### Build por duplo clique no Windows

Execute `build.bat` na raiz desta versão. Requer Python 3.12 x64 com o Python Launcher (`py.exe`). O script cria `.venv` se ela não existir, instala `requirements-dev.txt`, roda os testes e gera `dist/3.1.0/SAFIRA/SAFIRA.exe`, com a logo transparente. Uma venv copiada de outro computador ou do Linux deve ser renomeada antes; o script não apaga ambientes existentes.

O build anterior é movido para `dist/3.1.0/SAFIRA-anterior-<data-id>` antes da geração. Se o empacotamento ou a checagem falhar, a saída incompleta é preservada separadamente e o build anterior retorna à pasta SAFIRA quando possível. Os testes e verificações `--check` usam perfil descartável em `.test-tmp`, sem inicializar o banco pessoal. Distribua a pasta SAFIRA inteira, incluindo `_internal`.

Para usar dependências já instaladas, execute `build.bat -SkipDependencyInstall`. Os testes continuam obrigatórios. Para automação sem pausa final, defina `SAFIRA_BUILD_NO_PAUSE=1` antes de chamar o BAT. Também é possível executar `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1` diretamente. A política de execução é aplicada somente ao processo invocado.
