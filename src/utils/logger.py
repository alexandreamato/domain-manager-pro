"""Sistema de logging para o Domain Manager Pro"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name='domain_manager', log_dir='logs'):
    """
    Configura o sistema de logging

    Args:
        name: Nome do logger
        log_dir: Diretório para salvar logs

    Returns:
        Logger configurado
    """
    # Cria diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo de log com data
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    # Configuração do logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove handlers existentes
    logger.handlers = []

    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
