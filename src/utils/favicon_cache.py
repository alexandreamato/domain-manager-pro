"""
Cache de favicons dos domínios
"""
import os
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
import logging

logger = logging.getLogger(__name__)

class FaviconCache:
    """Gerencia o cache de favicons"""

    def __init__(self, cache_dir='data/favicons'):
        """
        Inicializa o cache de favicons

        Args:
            cache_dir: Diretório para armazenar favicons
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache em memória de PhotoImage
        self._photo_cache = {}

        # Favicon padrão (ícone genérico)
        self._default_icon = None

    def get_favicon(self, domain, size=16):
        """
        Obtém o favicon de um domínio

        Args:
            domain: Nome do domínio
            size: Tamanho do ícone (16, 32, 64, etc)

        Returns:
            PhotoImage do favicon ou None
        """
        # Remove protocolo se houver
        domain = domain.replace('http://', '').replace('https://', '').split('/')[0]

        # Chave do cache
        cache_key = f"{domain}_{size}"

        # Verifica cache em memória
        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]

        # Caminho do arquivo
        filepath = self.cache_dir / f"{domain}.png"

        # Tenta carregar do disco
        if filepath.exists():
            try:
                image = Image.open(filepath)
                image = image.resize((size, size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self._photo_cache[cache_key] = photo
                return photo
            except Exception as e:
                logger.warning(f"Erro ao carregar favicon de {domain}: {e}")

        # Baixa o favicon
        if self._download_favicon(domain, filepath):
            return self.get_favicon(domain, size)  # Tenta novamente após download

        # Retorna ícone padrão
        return self._get_default_icon(size)

    def _download_favicon(self, domain, filepath):
        """
        Baixa o favicon de um domínio usando Google Favicon API

        Args:
            domain: Nome do domínio
            filepath: Caminho para salvar o arquivo

        Returns:
            True se baixou com sucesso, False caso contrário
        """
        try:
            # Usa Google Favicon API (mais confiável)
            url = f"https://www.google.com/s2/favicons?domain={urllib.parse.quote(domain)}&sz=32"

            # Baixa com timeout curto
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            with urllib.request.urlopen(req, timeout=3) as response:
                data = response.read()

                # Salva o arquivo
                with open(filepath, 'wb') as f:
                    f.write(data)

                logger.debug(f"Favicon baixado: {domain}")
                return True

        except Exception as e:
            logger.debug(f"Erro ao baixar favicon de {domain}: {e}")
            return False

    def _get_default_icon(self, size=16):
        """Retorna um ícone padrão"""
        cache_key = f"_default_{size}"

        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]

        try:
            # Cria um ícone cinza simples
            image = Image.new('RGB', (size, size), color='#555555')
            photo = ImageTk.PhotoImage(image)
            self._photo_cache[cache_key] = photo
            return photo
        except:
            return None

    def prefetch_favicons(self, domains):
        """
        Pré-carrega favicons de vários domínios em background

        Args:
            domains: Lista de domínios
        """
        import threading

        def _prefetch():
            for domain in domains:
                self.get_favicon(domain)

        thread = threading.Thread(target=_prefetch, daemon=True)
        thread.start()

    def clear_cache(self):
        """Limpa o cache de favicons"""
        # Limpa memória
        self._photo_cache.clear()

        # Limpa disco
        try:
            for file in self.cache_dir.glob('*.png'):
                file.unlink()
            logger.info("Cache de favicons limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
