# Motion System

`safira/ui/motion.py` usa `after(16, ...)` e relógio monotônico. Uma cadeia de callbacks por canal/componente; iniciar outra animação no mesmo canal cancela a anterior. Nenhuma thread ou sleep para animação. Threads existentes são somente para operações de trabalho, não para desenho.

Ease-out cúbico: 1 - (1-t)^3. Hover 150 ms; sidebar 180 ms; submenu 200 ms; entrada de títulos 250 ms; modal 220 ms; saída 130 ms; atualização de card 240 ms; gráficos 480 ms; toast 220 ms e expiração após 4 s.

O movimento muda apenas o elemento necessário: cor, altura do submenu, alpha da janela, progressão de curva/barra/anel, realce do card ou posição do toast. Não há redesenho da aplicação inteira a cada quadro. Dashboard conserva seus widgets entre atualizações.

Destroy cancela canais agendados. Toast cancela seu temporizador. Sombras usam debounce e cancelamento. O modo reduzido aplica o estado final imediatamente, sem agendar quadros; animações já iniciadas terminam no próximo quadro. Gráficos em zero/sem dados apresentam estado vazio real.

Preferência: Configurações → Personalizar interface → Movimento. Inicialmente consulta a opção de animação da área cliente do Windows quando possível; a escolha explícita é persistida em `ui-preferences.json`.

QA: alternância rápida de telas, abertura/fechamento de modal, validação, calendário, seletor, bloqueio, zero jobs pendentes após bloqueio e modo reduzido sem chamada a after. Os callbacks de progresso de operações demoradas continuam existindo por serem feedback operacional, não ornamentação.
