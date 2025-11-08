#!/usr/bin/env python3
"""
Domain Manager Pro - Sistema de gerenciamento e monitoramento de domínios

Autor: Domain Manager Pro Team
Versão: 1.0.0
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.ui.main_window import MainWindow


def main():
    """Função principal"""
    # Configura logging
    logger = setup_logger()
    logger.info("="*60)
    logger.info("Domain Manager Pro v1.0.0")
    logger.info("="*60)

    try:
        # Cria e executa a aplicação
        app = MainWindow()
        app.run()

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
