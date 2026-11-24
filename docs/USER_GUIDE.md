# Guia de uso

1. Abra SAFIRA.exe e crie sua senha mestra. A base começa vazia. Datas na interface e nos relatórios usam DD/MM/AAAA (meses nos gráficos: MM/AAAA); valores aceitam `1.250,90` ou `1250.90`.
2. Em Contas, crie banco/carteira/corretora/reserva e informe o saldo inicial na data de abertura. Saldo inicial não é receita. Após haver operações, tipo, abertura e saldo inicial ficam protegidos; ajustes posteriores devem ser operações explícitas.
3. Clique no nome Movimentações para abrir o histórico. A seta ao lado expande Categorias e Métodos. Cadastre itens próprios ou desative padrões sem perder referências.
4. Cadastre receita ou despesa escolhendo conta, tipo, categoria compatível, método, data da operação e competência. Eventos futuros devem ficar pendentes. Pressione Enter após pesquisar ou clique Aplicar nos filtros.
5. Para editar, selecione uma linha e clique Editar. Cancelar neutraliza o efeito e preserva o registro. Operações de cartões/compromissos/investimentos são administradas pelo módulo de origem.
6. Transferências movem o mesmo valor entre duas contas. Para aportar em uma corretora, transfira primeiro o dinheiro para seu caixa e use Aportar na posição. Posição inicial representa patrimônio já existente; não cria saída de caixa.
7. Cartões: informe somente nome/identificação, tipo, conta, limite e dias. Não informe número completo ou CVV. Compras no débito geram despesa na conta associada; compras no crédito geram parcelas/faturas e não debitam o banco imediatamente.
8. Compras na data de fechamento entram no ciclo seguinte. Em Faturas, após o fechamento, pague integralmente ou uma parte, selecionando a conta e a data. Limite disponível reflete o saldo devedor total. Histórico de pagamentos permite conferir cada operação. Juros e estornos após pagamento não são automatizados.
9. Compromissos: selecione valor, conta, categoria, vencimento e recorrência. As ocorrências mensais preservam o dia original em meses curtos. Marcar pago gera exatamente uma despesa; clicar novamente não duplica. Editar/adiar altera somente a ocorrência selecionada; Ignorar não altera o saldo. Parar recorrência impede novas ocorrências sem apagar as existentes.
10. A Home mostra saldo disponível real e patrimônio líquido atual. Indicadores por competência respeitam o período escolhido; fluxo de caixa respeita a data de confirmação/pagamento. Compras de crédito são consumo por competência e pagamento de fatura é saída de caixa, evitando contar despesa duas vezes.
11. Planejamento mostra eventos abertos e projeção. Atrasados entram porque continuam devidos. Não há estimativa de juros/rendimento. Reservas e corretoras ficam fora do dinheiro disponível para gastos.
12. Notificações recalcula alertas e remove os já resolvidos. Abrir item leva à ocorrência/fatura selecionada.
13. Relatórios exporta PDF offline com período, totais, contas, operações, consumo de crédito, compromissos, faturas e projeção. Quando o período termina no passado, a projeção parte do saldo de hoje; patrimônio e dívidas são sempre a posição atual explicitamente rotulada.
14. Configurações permite mudar senha, exportar/restaurar backup, ajustar escala e tempo de bloqueio e ler logs. Restauração exige confirmação, preserva cópia anterior e retorna ao login com a senha do backup.

## Recomendações de operação

Faça backup regularmente pela aplicação. Não altere diretamente o SQLite nem apague arquivos WAL de uma base aberta. Arquivar conta/categoria preserva os valores anteriores; reative para voltar a usá-la em novos registros. Confirme datas e categorias antes de salvar. Sem saldo de demonstração em produção.

O aplicativo aceita saldo negativo para representar cheque especial/conta devedora. Não bloqueia despesas por falta de saldo; não representa autorização bancária e não realiza pagamentos reais.

## Orçamento e salário recorrente

Em **Perspectivas → Planejamento**, use **Orçamento por categoria** para definir limites fixos a partir do mês escolhido (mudanças valem daquele mês em diante e preservam os anteriores) e **Receitas recorrentes** para cadastrar o salário no 5º dia útil de Ariquemes/RO. As próximas ocorrências ficam pendentes; selecione uma em Recebimentos e use **Confirmar recebimento** para informar valor/data reais. Não cadastre a mesma receita manualmente outra vez. Para corrigir uma ocorrência antes da confirmação, use Movimentações.

A Home mostra **Planejado × Realizado** por categoria e mantém o gráfico mensal abaixo. Sem limite definido, a categoria aparece como “Sem limite”; orçamento não é uma despesa nem entra como conta a pagar na previsão. Em **Calendário Ariquemes/RO**, informe folgas excepcionais do empregador quando necessário. Veja [regras e calendário](PLANNING_CALENDAR.md).
