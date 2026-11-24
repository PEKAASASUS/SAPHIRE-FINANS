# Esquema SQLite - versão 1

Implementação autoritativa: `safira/persistence.py`. Dinheiro em centavos INTEGER; tabelas com CHECK de tipo nas colunas operacionais, FKs habilitadas por conexão e exclusão restrita dos cadastros referenciados. Um perfil local por base.

| Tabela | Finalidade / vínculos |
|---|---|
| schema_migrations | Versões aplicadas, transação explícita por evolução |
| profile | id=1, verificador Argon2id, falhas e instante mínimo de nova tentativa |
| settings | Preferências reais: auto_lock e scale |
| accounts | Nome único, tipo, abertura, saldo inicial e ativo |
| categories | Nome/tipo únicos, padrão, ativo; sem subcategorias |
| methods | Nome único, padrão e ativo; sem cartão genérico |
| operations | Token único, tipo, origem, descrição, valor, operação, competência, confirmação, estado, categoria e método |
| entries | Operação → conta e delta; combinação operação/conta única |
| positions | Corretora, posição, custo e avaliação atual |
| cards | Crédito/débito, conta opcional, limite, fechamento/vencimento e ativo |
| purchases | Token único, cartão, descrição, data, total, categoria e cancelamento; operação vinculada para débito |
| invoices | Cartão, fechamento e vencimento congelados; unicidade cartão/fechamento |
| installments | Compra → fatura, número, valor e competência; compra/número únicos |
| invoice_payments | Fatura → operação de caixa, operação única |
| series | Definição mensal, início, conta, categoria, valor e ativo |
| commitments | Ocorrência individual, série/mês únicos, vencimento original/atual, estado e operação de pagamento única |

## Integridade

Toda operação manual tem uma partida; transferência tem duas partidas opostas do mesmo valor. Compra no crédito não cria partida de caixa. Pagamento de fatura tem uma partida negativa e vínculo em invoice_payments. Pagamento de compromisso tem uma partida negativa e vínculo único em commitments. Operações de investimento são apartadas dos resultados operacionais.

Saldo = saldo inicial elegível pela abertura + partidas confirmadas até a data de confirmação. Estado cancelado neutraliza o efeito sem remover o registro. Saldo não é armazenado como total mutável.

Regras compostas são verificadas pelos serviços dentro de BEGIN IMMEDIATE. SQLite impõe também unicidade, referências e restrições locais. Backup verifica integridade física/referencial e invariantes financeiras principais antes de restaurar. Não há suporte a edição direta do banco por outros programas.

WAL em execução normal; API sqlite3.Connection.backup para exportar. Restauração prepara um arquivo candidato validado no mesmo volume, preserva base anterior, faz checkpoint e substituição atômica. A conexão não fica aberta entre operações. Instância única protege substituições concorrentes pelo app.

Evolução: adicionar migração nova, nunca reescrever uma migração distribuída. Nenhuma migração importa ou toca o banco da SF-V2.
