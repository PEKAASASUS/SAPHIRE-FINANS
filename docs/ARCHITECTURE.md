# Arquitetura V3

Python 3.12; CustomTkinter; SQLite; Argon2id; ReportLab; pytest; PyInstaller. Um perfil local.

Camadas: ui (widgets e navegação), controllers (coordenação), services (casos de uso), domain (dinheiro/datas), persistence (conexão, migrações e repositório), infrastructure (segurança, backup, caminhos e logs). UI não executa SQL.

Operações financeiras possuem duas ou mais partidas de caixa quando necessário; saldos são derivados das partidas confirmadas, nunca caches. Transferências, pagamento de compromisso e fatura gravam dentro de BEGIN IMMEDIATE. Chaves únicas e vínculos impedem repetições. Compras de crédito geram parcelas e consumo, não partidas bancárias; pagamentos geram caixa, não novo consumo.

Conexões curtas por operação e WAL. Migrações versionadas com transação explícita. Valores inteiros, datas ISO e arquivos locais. Dados em LOCALAPPDATA/SAFIRA; SAFIRA_DATA_DIR permite diretório explícito para testes e modo portátil. Executável nunca usa a pasta de extração como armazenamento.

Senha Argon2id (64 MiB, 3 iterações, paralelismo 4); banco sem criptografia. Tentativas inválidas têm atraso progressivo persistido. Backup SQLite consistente e restauração validada antes de substituição, mantendo cópia anterior. Nenhuma telemetria.

## Extensão de planejamento (05/11/2026)

`planning_service.FinancialPlanning` implementa migração independente e transacional `planning_migrations=2`, sem alterar a versão do esquema original. Orçamentos, cadastros salariais, vínculos mensais e exceções de calendário são tabelas no mesmo SQLite, incluídas pelo backup completo. Receitas previstas reutilizam o escritor/validador financeiro original e uma operação pendente por cadastro/mês. As telas acessam o serviço, sem SQL. `business_calendar` fornece regras offline de Ariquemes/RO; detalhes em PLANNING_CALENDAR.md. Inicialização é idempotente inclusive após restauração de backup antigo.

Limites recorrentes usam planning_budget_rules como revisões efetivas por mês; alterações substituem o calendário futuro da categoria sem reescrever meses anteriores. A migração 2 preserva snapshots mensais da versão 1 e os backups continuam completos.
