# Regras financeiras

- Dinheiro: centavos inteiros, entrada Decimal com ROUND_HALF_UP; float rejeitado. Datas locais ISO.
- Saldo inicial separado das receitas. Saldo = inicial + partidas confirmadas até a data consultada. Contas arquivadas preservam patrimônio e histórico.
- Disponível: bancos e carteiras ativos/arquivados; reservas e corretoras separados. Patrimônio bruto = caixa de todas as contas + posições investidas. Patrimônio líquido desconta dívida de crédito.
- Receita/despesa operacional exclui transferências, aportes, resgates e pagamento de fatura. Consumo inclui parcelas de crédito pela competência. Caixa inclui pagamentos efetivos, sem antecipar compras de crédito.
- Compra no fechamento pertence ao ciclo seguinte. Vencimento após fechamento; dia inexistente é ajustado ao último dia do mês. Datas de fatura são congeladas na criação. Parcelas distribuem resto de centavos das primeiras para as últimas.
- Pagamento parcial não pode superar o restante; não gera juros automáticos. Cancelamento de compra só antes de qualquer pagamento nas faturas envolvidas; compras pagas exigem estorno conciliado externo (limitação explícita).
- Compromissos recorrentes geram ocorrências únicas por série e mês, preservando dia original em meses curtos. Pagar é idempotente. Editar/adiar uma ocorrência não altera a série; ignorar não gera caixa.
- Projeção parte do caixa real e inclui pendências, ocorrências abertas e saldo remanescente de faturas elegíveis. Não altera saldo real. Atrasados são incluídos como obrigações ainda abertas. Não prevê juros, inflação ou rendimentos.
- Categorias padrão somente desativam/reativam. Nomes únicos por tipo sem diferença de caixa. Histórico usa referências preservadas. Registros financeiros são cancelados, não apagados.
