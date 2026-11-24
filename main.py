"""SAFIRA 3.1.0 Windows desktop entry point."""
import argparse
import sys
from pathlib import Path
from safira.infrastructure import data_dir,configure_logging,InstanceLock
from safira.controller import Controller


def main():
    parser=argparse.ArgumentParser(description='SAFIRA 3.1.0')
    parser.add_argument('--check',action='store_true',help='Validate imports/schema without GUI')
    args=parser.parse_args()
    folder=data_dir()
    logger=configure_logging(folder/'logs')
    try:
        with InstanceLock(folder):
            controller=Controller(folder/'safira.sqlite')
            from safira.ui.app import App
            if args.check:
                print('SAFIRA 3.1.0 OK | '+str(controller.store.path))
                return
            window=App(controller)
            logger.info('SAFIRA 3.1.0 iniciado')
            window.mainloop()
            logger.info('SAFIRA encerrado')
    except Exception as exc:
        logger.error('Falha de inicialização: %s',type(exc).__name__)
        if args.check: raise
        from tkinter import messagebox
        messagebox.showerror('SAFIRA','Não foi possível iniciar o SAFIRA. Verifique permissões e dependências.\nLog: '+str(folder/'logs'/'safira.log'))
        raise


if __name__=='__main__':
    main()
