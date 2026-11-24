# Validação executada - 25/10/2026

Ambiente: Windows 11 x64, CPython 3.12.14, CustomTkinter 6.0.0, pytest 9.1.1, ReportLab 5.1.0 e PyInstaller 6.22.3. Dados sintéticos em SF-V3.0.0/.test-tmp. O legado e seu banco não foram alterados.

| Verificação | Resultado |
|---|---|
| scripts/test.ps1 - última suíte completa | **48 passed**, 35,17 s |
| Dez cenários financeiros obrigatórios | Cobertos e aprovados em tests/test_finance.py |
| Concorrência no pagamento de compromisso | Quatro chamadas, uma operação e um débito |
| Falha na segunda partida de transferência | Rollback integral, sem operação ou saída parcial |
| Edição/cancelamento e datas distintas | Saldos, competência e caixa coerentes; confirmação preservada |
| Migração vazia, reentrada e falha em esquema incompatível | Aprovado; DDL revertido na falha |
| Backup/restauração/reabertura | Relações e valores preservados; corrupção estrutural/semântica rejeitada |
| Autenticação e espera persistente | Setup, alteração, falhas e expiração aprovados |
| Instância única Windows | Segunda aquisição rejeitada e reabertura após liberar aprovada |
| tests/ui_smoke.py | **UI SMOKE PASSED** |
| Navegação | 14 telas construídas e atualizadas sem exceção de callback |
| Formulários reais | Conta, movimentação, cartão, compra débito e pagamento de compromisso persistidos pelos formulários |
| Layout | Navegação em 980×600 e 1440×900; inspeção visual da Home/lista e autenticação no Windows |
| compileall | Sintaxe/importações compiladas sem erro |
| pip check | No broken requirements found |
| scripts/build.ps1 | Build Windows gerado em dist/SAFIRA |
| Código-fonte main.py --check | SAFIRA 3.0.0 OK |
| Executável final --check | Código de saída 0 em diretório de dados descartável |
| Interface do executável | Tela de configuração inicial aberta, inspecionada e encerrada no Windows |
| PDF básico | Teste de exportação aprovado |
| PDF extenso | 50 despesas, totais exatos e 9 páginas; renderização Poppler e inspeção de todas as páginas, cabeçalhos repetidos e rodapés |

## Correções durante a validação

Corrigidos callback de foco de campo destruído e lock Windows. Um teste de espera apresentou flutuação por expiração real de um segundo; passou a usar relógio controlado e verifica também o acesso após expirar. Nenhuma expectativa de saldo foi alterada para acomodar erro financeiro.

O build emitiu avisos de imports opcionais de outras plataformas e fallback de fonte durante a análise do PyInstaller; não impediram geração, execução ou inspeção da interface. Poppler emitiu avisos de fontes opcionais do ambiente; o PDF usa Helvetica e foi renderizado sem texto cortado ou caracteres inválidos.

## Limites da evidência

Os testes de UI exercitam widgets/callbacks reais, sem representar homologação manual exaustiva de todas as entradas e DPI. O teste do executável cobre inicialização e tela inicial; os fluxos financeiros completos foram exercitados pelo código Python e integração SQLite, não todos repetidos manualmente no binário. Não houve teste prolongado, instalação assinada, outras versões do Windows ou medição com milhões de registros.

Reprodução: scripts/test.ps1; tests/ui_smoke.py; tests/pdf_preview.py; scripts/build.ps1. Nunca apontar testes para a base pessoal ou SF-V2.
