# SAFIRA 3.1.0 - plano de UI/UX

- [x] A: leitura do briefing, auditoria das telas/componentes e confirmação de base idêntica.
- [x] B: tokens, tipografia do sistema, geometria, superfícies, semântica e acessibilidade.
- [x] C: controles, calendário, seletor, grade virtualizada, cards, gráficos, modais e feedback.
- [x] D: shell, sidebar agrupada, indicador, submenu e sessão.
- [x] E: Home recomposta com widgets persistentes e dados dos serviços existentes.
- [x] F: Movimentações, filtros, valores visíveis, seleção estável, contexto e teclado.
- [x] G: demais módulos integrados aos componentes; cartões com abas e configurações por finalidade.
- [x] H: animações canceláveis e movimento reduzido persistente, sem threads por animação.
- [x] I: regressão original e testes novos de design aprovados; smoke de telas/formulários aprovado.
- [x] I complementar: stress final aprovado em nove combinações de escala/geometria e dez mil linhas.
- [x] J: QA documentado, build recompilado e fonte/executável aprovados em --check; limites de inspeção final registrados em UI_QA_REPORT.md.

Versão funcional original preservada. Sem migração de esquema. Preferências UI separadas do banco. Distribuição nova em dist/3.1.0, sem sobrescrever o build copiado.

Pendências de produto fora desta entrega: asset oficial de marca, duas imagens citadas no prompt não anexadas, homologação em outros monitores/DPI físicos e melhorias de leitores de tela devido aos limites de Canvas/Tk.
