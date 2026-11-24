# Planejamento, orçamento e salário recorrente

Implementação autorizada em 05/11/2026. Evolução funcional com tabelas adicionais no mesmo SQLite; não é preferência visual. Os nove módulos de FINANCIAL_ENGINE_BASELINE.json permanecem intactos.

## Uso

Em Perspectivas → Planejamento:

- **Orçamento por categoria:** escolha o mês e defina/edite um limite para uma categoria de despesa. Zero é um limite explícito; sem cadastro significa sem limite. Remover limite não remove despesas. Limites são mensais e gerais, sem vínculo com conta, e repetem a partir do mês escolhido. Uma alteração vale daquele mês em diante e substitui alterações futuras já programadas para a categoria; meses anteriores preservam o valor vigente. Remover encerra o limite a partir do mês escolhido, sem apagar o histórico.
- **Receitas recorrentes:** cadastre descrição, conta de destino, categoria de receita, valor mensal estimado e primeiro mês. A data informada seleciona o mês; o dia é calculado. A regra é o 5º dia útil de Ariquemes/RO, excluindo sábados e domingos conforme pedido do proprietário. O cadastro não contém valor ou conta fictícios; exige preenchimento do usuário.
- **Recebimentos:** escolha uma ocorrência pendente e confirme o valor/data reais. A operação só altera o saldo real após confirmação. Também pode ser ajustada/cancelada em Movimentações, pois usa os contratos já existentes. Cancelar uma ocorrência não a recria. Parar um cadastro interrompe novas ocorrências e cancela as futuras pendentes; recebimentos concluídos e atrasados são preservados. Para alterar permanentemente valor/conta/regra, pare o cadastro anterior e crie um novo, evitando sobreposição.
- **Calendário Ariquemes/RO:** adicione/substitua uma data excepcional como útil ou não útil, conforme o expediente do empregador. Exceções afetam apenas previsões ainda não geradas. Ajuste previsões existentes em Movimentações se houver mudança de calendário.

As previsões são geradas para o mês atual e os onze seguintes ao consultar a Home, Planejamento ou Movimentações. Períodos maiores aplicados em Home/Movimentações ou exportados estendem a geração até a data consultada, limitado a 100 anos por cadastro. Não há serviço externo nem execução com o programa fechado. Cadastros cuja conta ou categoria foi desativada não geram novas ocorrências até reativação. Recebimentos anteriores à abertura da conta não são gerados.

O gráfico **Planejado × Realizado** substitui o saldo mensal na primeira linha da Home. Azul é o orçamento; a segunda barra é o realizado, vermelho quando ultrapassa um limite definido. Usa o mês da data final do filtro, com realizado desde o início desse mês até a data final. As despesas realizadas vêm dos serviços existentes por competência, incluindo consumo no crédito; pendências e cancelamentos não viram gastos realizados. Categorias com gastos sem orçamento aparecem como “Sem limite”. Todas as categorias ficam acessíveis pela rolagem. O gráfico mensal de saldo permanece abaixo.

O filtro de contas da Home afeta o realizado; o limite continua sendo o orçamento geral da categoria, como informa a legenda. Limites não são somados aos compromissos nem alteram saldo ou previsão de caixa. Salários gerados são operações pendentes já consideradas pela previsão original, sem nova soma separada. Confirmação substitui a ocorrência pendente, sem criar uma segunda receita.

## Calendário offline e fontes

Consultado em 05/11/2026:

- [Portal da Transparência de Rondônia — feriados](https://transparencia.ro.gov.br/feriados).
- [TJRO — calendário oficial de 2026, texto compilado](https://atos.tjro.jus.br/files/compilado152025202606126a2c5bf933d1c.pdf).
- [Governo federal — calendário de 2026](https://agenciagov.ebc.com.br/noticias/202512/confira-o-calendario-oficial-de-feriados-nacionais-e-pontos-facultativos-em-2026).

Regras recorrentes usadas: 01/01, 21/04, 01/05, 07/09, 12/10, 02/11, 15/11, 20/11 e 25/12; Sexta-feira da Paixão calculada pela Páscoa; 04/01 em Rondônia; 04/10 e 11/10 em Ariquemes. Não se importam recessos judiciais, folgas administrativas ou pontos facultativos como se fossem feriados gerais do empregador. Carnaval, Corpus Christi e expedientes excepcionais podem ser cadastrados pelo usuário quando aplicáveis. A regra sem sábados é a escolha do proprietário, não uma afirmação sobre a definição legal de dia útil salarial. Regras anuais podem mudar: não há atualização automática de feriados pela internet. As projeções futuras são estimativas e permanecem ajustáveis antes da confirmação.

## Persistência e compatibilidade

`FinancialPlanning` aplica migração independente `planning_migrations` versão 2, transacional e idempotente, criando `planning_budgets`, `planning_salaries`, `planning_salary_months`, `planning_calendar` e `planning_budget_rules`. Preserva schema_migrations=1 e todas as tabelas originais. Não há SQL nas telas. Valores financeiros são centavos inteiros, validados pelo domínio. Geração de salário usa o escritor/validador original dentro da mesma transação do vínculo mensal e tem chave única cadastro/mês. A interface não marca recebimentos como confirmados automaticamente.

Os dados ficam no banco financeiro atual e entram no backup SQLite completo existente. A restauração de um backup antigo recria a extensão vazia na próxima consulta, sem inventar orçamento ou salário. ui-preferences.json não armazena esses dados. Backup antigo naturalmente não contém configurações criadas depois dele. Nenhum banco pessoal foi usado durante desenvolvimento ou QA.

### Histórico dos limites fixos

A versão 2 guarda revisões por categoria e mês de início em planning_budget_rules. Valor nulo encerra o limite; zero continua sendo um limite explícito. O valor vigente é a última revisão anterior ou igual ao mês consultado. Cadastros mensais antigos permanecem como snapshots históricos exatos. Na migração, o último limite conhecido passa a ser recorrente a partir do mês atual, respeitando alterações futuras já cadastradas. Meses históricos sem cadastro não são preenchidos retroativamente. Ao salvar uma nova alteração, revisões futuras são substituídas, sem mudar revisões/snapshots anteriores ao mês escolhido. Tudo continua no mesmo backup SQLite.
