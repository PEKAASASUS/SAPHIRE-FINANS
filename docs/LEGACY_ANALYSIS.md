# Análise do legado

Fonte: SF-V2_1_0/SF-V2_1_0/safira_v2, incluindo leitura integral de SAFIRA_PROJECT_CONTEXT.md. Legado preservado somente para leitura.

Implementado: autenticação PBKDF2, bloqueio, contas, categorias, métodos e resumo. Parcial: modelos de movimentação e investimentos. Ausente: fluxos completos de cartões, transferências, recorrência, planejamento e PDF. Foram encontrados 101 testes, sem execução no legado.

Divergências: categorias padrão editáveis apesar da documentação; conversão remove o ponto decimal; edição remove sinal negativo; cards aponta para accounts_old removida; tabelas futuras ainda usam REAL; documentação de versão desatualizada; menu Movimentações não separa texto e seta. Criptografia Fernet existe, mas não cifra os dados financeiros.

V3 adota novo esquema, sem importar o banco legado. Não há logo oficial nos assets recebidos: marca textual SAFIRA até fornecimento do asset. Requisitos do novo prompt prevalecem: armazenamento persistente do sistema operacional, Argon2id e reconstrução independente.
