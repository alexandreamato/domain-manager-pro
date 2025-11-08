"""Coletor de informações de SEO para domínios"""

import requests
import re
import logging
from urllib.parse import quote
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SEOCollector:
    """Coleta métricas de SEO de APIs públicas e gratuitas"""

    def __init__(self, timeout=10):
        """
        Inicializa o coletor de SEO

        Args:
            timeout: Timeout para requisições em segundos
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_google_index_count(self, domain):
        """
        Estima quantas páginas estão indexadas no Google

        Args:
            domain: Nome do domínio

        Returns:
            Número estimado de páginas ou None
        """
        try:
            # Busca no Google por site:domain.com
            url = f"https://www.google.com/search?q=site:{quote(domain)}"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                # Tenta extrair o número de resultados
                match = re.search(r'About ([\d,]+) results', response.text)
                if match:
                    count_str = match.group(1).replace(',', '')
                    return int(count_str)

                # Alternativa: busca outro padrão
                match = re.search(r'Cerca de ([\d.]+) resultados', response.text)
                if match:
                    count_str = match.group(1).replace('.', '')
                    return int(count_str)

        except Exception as e:
            logger.error(f"Erro ao buscar índice do Google para {domain}: {e}")

        return None

    def check_robots_txt(self, domain):
        """
        Verifica se o domínio tem robots.txt e analisa

        Args:
            domain: Nome do domínio

        Returns:
            Dicionário com informações do robots.txt
        """
        info = {
            'has_robots': False,
            'allows_indexing': True,
            'has_sitemap': False,
            'sitemap_url': None
        }

        try:
            url = f"https://{domain}/robots.txt"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                info['has_robots'] = True
                content = response.text.lower()

                # Verifica se bloqueia indexação
                if 'disallow: /' in content and 'user-agent: *' in content:
                    info['allows_indexing'] = False

                # Busca sitemap
                sitemap_match = re.search(r'sitemap:\s*(.+)', content, re.IGNORECASE)
                if sitemap_match:
                    info['has_sitemap'] = True
                    info['sitemap_url'] = sitemap_match.group(1).strip()

        except Exception as e:
            logger.error(f"Erro ao verificar robots.txt de {domain}: {e}")

        return info

    def get_page_metrics(self, domain):
        """
        Obtém métricas básicas da página inicial

        Args:
            domain: Nome do domínio

        Returns:
            Dicionário com métricas
        """
        metrics = {
            'page_size_kb': None,
            'load_time_ms': None,
            'has_meta_description': False,
            'has_title': False,
            'title_length': 0,
            'meta_description_length': 0,
            'h1_count': 0,
            'images_count': 0,
            'links_count': 0
        }

        try:
            import time
            url = f"https://{domain}"

            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout)
            load_time = (time.time() - start_time) * 1000  # em ms

            metrics['load_time_ms'] = int(load_time)
            metrics['page_size_kb'] = len(response.content) / 1024

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Title
            title = soup.find('title')
            if title:
                metrics['has_title'] = True
                metrics['title_length'] = len(title.get_text().strip())

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metrics['has_meta_description'] = True
                metrics['meta_description_length'] = len(meta_desc.get('content').strip())

            # H1 tags
            metrics['h1_count'] = len(soup.find_all('h1'))

            # Images
            metrics['images_count'] = len(soup.find_all('img'))

            # Links
            metrics['links_count'] = len(soup.find_all('a'))

        except Exception as e:
            logger.error(f"Erro ao obter métricas de página de {domain}: {e}")

        return metrics

    def check_ssl_score(self, domain):
        """
        Verifica configuração SSL básica

        Args:
            domain: Nome do domínio

        Returns:
            Dicionário com score SSL
        """
        score = {
            'has_https': False,
            'redirects_to_https': False,
            'hsts_enabled': False
        }

        try:
            # Tenta HTTPS
            https_url = f"https://{domain}"
            response = self.session.get(https_url, timeout=self.timeout, allow_redirects=False)

            if response.status_code == 200:
                score['has_https'] = True

                # Verifica HSTS
                if 'strict-transport-security' in response.headers:
                    score['hsts_enabled'] = True

            # Verifica redirect de HTTP para HTTPS
            http_url = f"http://{domain}"
            response = self.session.get(http_url, timeout=self.timeout, allow_redirects=True)

            if response.url.startswith('https://'):
                score['redirects_to_https'] = True

        except Exception as e:
            logger.error(f"Erro ao verificar SSL de {domain}: {e}")

        return score

    def estimate_domain_value(self, domain, traffic_estimate=None, revenue_estimate=None):
        """
        Estima valor de mercado do domínio usando múltiplos fatores

        Args:
            domain: Nome do domínio
            traffic_estimate: Estimativa de tráfego mensal
            revenue_estimate: Estimativa de receita mensal

        Returns:
            Valor estimado em USD
        """
        # Fatores de valor base
        base_value = 100  # $100 mínimo

        # TLD premium
        tld = domain.split('.')[-1].lower()
        tld_multipliers = {
            'com': 3.0,
            'net': 2.0,
            'org': 2.0,
            'io': 2.5,
            'ai': 4.0,
            'co': 2.0,
            'app': 2.5,
            'dev': 2.0
        }

        value = base_value * tld_multipliers.get(tld, 1.0)

        # Comprimento do domínio (mais curto = mais valioso)
        domain_name = domain.split('.')[0]
        length = len(domain_name)

        if length <= 3:
            value *= 50  # Muito valioso
        elif length <= 5:
            value *= 20
        elif length <= 7:
            value *= 5
        elif length <= 10:
            value *= 2

        # Tráfego (se fornecido)
        if traffic_estimate:
            # Regra simples: $1 por 100 visitantes/mês
            value += (traffic_estimate / 100)

        # Receita (se fornecido)
        if revenue_estimate:
            # Múltiplo de 12-24x receita anual
            annual_revenue = revenue_estimate * 12
            value += (annual_revenue * 18)  # Média de 18x

        # Keywords valiosas
        valuable_keywords = [
            'insurance', 'lawyer', 'attorney', 'loan', 'credit', 'mortgage',
            'trading', 'forex', 'crypto', 'bitcoin', 'invest', 'finance',
            'health', 'medical', 'doctor', 'clinic', 'hospital',
            'hotel', 'travel', 'flight', 'car', 'real', 'estate',
            'casino', 'bet', 'poker', 'game'
        ]

        for keyword in valuable_keywords:
            if keyword in domain_name.lower():
                value *= 3
                break

        # Arredonda para múltiplo de 100
        value = round(value / 100) * 100

        return max(100, min(value, 1000000))  # Entre $100 e $1M

    def collect_all_seo_info(self, domain):
        """
        Coleta todas as informações de SEO

        Args:
            domain: Nome do domínio

        Returns:
            Dicionário com todas as métricas de SEO
        """
        logger.info(f"Coletando informações de SEO para {domain}")

        result = {
            'google_indexed_pages': None,
            'robots_info': {},
            'page_metrics': {},
            'ssl_score': {},
            'estimated_domain_value': None,
            'seo_score': 0
        }

        try:
            # Google index
            result['google_indexed_pages'] = self.get_google_index_count(domain)
        except:
            pass

        try:
            # Robots.txt
            result['robots_info'] = self.check_robots_txt(domain)
        except:
            pass

        try:
            # Métricas de página
            result['page_metrics'] = self.get_page_metrics(domain)
        except:
            pass

        try:
            # SSL
            result['ssl_score'] = self.check_ssl_score(domain)
        except:
            pass

        try:
            # Valor estimado
            result['estimated_domain_value'] = self.estimate_domain_value(
                domain,
                traffic_estimate=result.get('google_indexed_pages'),
                revenue_estimate=None
            )
        except:
            pass

        # Calcula SEO Score (0-100)
        result['seo_score'] = self._calculate_seo_score(result)

        logger.info(f"Informações de SEO coletadas para {domain}")

        return result

    def _calculate_seo_score(self, seo_data):
        """
        Calcula um score geral de SEO (0-100)

        Args:
            seo_data: Dicionário com dados de SEO

        Returns:
            Score de 0 a 100
        """
        score = 0

        # Páginas indexadas (até 20 pontos)
        indexed = seo_data.get('google_indexed_pages', 0) or 0
        if indexed > 0:
            score += min(20, indexed / 10)

        # Robots.txt (até 15 pontos)
        robots = seo_data.get('robots_info', {})
        if robots.get('has_robots'):
            score += 5
        if robots.get('allows_indexing'):
            score += 5
        if robots.get('has_sitemap'):
            score += 5

        # Métricas de página (até 35 pontos)
        metrics = seo_data.get('page_metrics', {})
        if metrics.get('has_title'):
            score += 5
        if metrics.get('has_meta_description'):
            score += 5
        if 30 <= metrics.get('title_length', 0) <= 60:
            score += 5
        if 120 <= metrics.get('meta_description_length', 0) <= 160:
            score += 5
        if metrics.get('h1_count', 0) >= 1:
            score += 5
        if metrics.get('load_time_ms', 9999) < 3000:
            score += 5
        if metrics.get('page_size_kb', 9999) < 2000:
            score += 5

        # SSL (até 30 pontos)
        ssl = seo_data.get('ssl_score', {})
        if ssl.get('has_https'):
            score += 10
        if ssl.get('redirects_to_https'):
            score += 10
        if ssl.get('hsts_enabled'):
            score += 10

        return min(100, int(score))
