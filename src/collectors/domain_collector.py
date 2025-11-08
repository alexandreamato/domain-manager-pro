"""Coletor principal de informações de domínios"""

import re
import socket
import ssl
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
import whois
from OpenSSL import crypto

logger = logging.getLogger(__name__)


class DomainCollector:
    """Coleta informações completas de um domínio"""

    def __init__(self, timeout=5, max_workers=10):
        """
        Inicializa o coletor

        Args:
            timeout: Timeout para requisições HTTP em segundos
            max_workers: Número máximo de threads paralelas
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def normalize_domain(self, domain):
        """
        Normaliza o domínio removendo protocolo e paths

        Args:
            domain: Domínio a ser normalizado

        Returns:
            Domínio normalizado
        """
        # Remove protocolo
        domain = re.sub(r'^https?://', '', domain)
        # Remove path
        domain = domain.split('/')[0]
        # Remove www.
        domain = re.sub(r'^www\.', '', domain)
        return domain.strip().lower()

    def collect_http_info(self, domain):
        """
        Coleta informações HTTP do domínio

        Args:
            domain: Domínio a ser analisado

        Returns:
            Dicionário com informações HTTP
        """
        info = {
            'status_code': None,
            'server': None,
            'cloud_provider': None,
            'raw_headers': {}
        }

        try:
            # Tenta HTTPS primeiro
            url = f"https://{domain}"
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            info['status_code'] = response.status_code
            info['raw_headers'] = dict(response.headers)

            # Detecta servidor
            info['server'] = response.headers.get('Server', 'Unknown')

            # Detecta cloud provider
            info['cloud_provider'] = self._detect_cloud_provider(response.headers, domain)

            return info, response

        except requests.exceptions.SSLError:
            # Se HTTPS falhar, tenta HTTP
            try:
                url = f"http://{domain}"
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

                info['status_code'] = response.status_code
                info['raw_headers'] = dict(response.headers)
                info['server'] = response.headers.get('Server', 'Unknown')
                info['cloud_provider'] = self._detect_cloud_provider(response.headers, domain)

                return info, response

            except Exception as e:
                logger.error(f"Erro HTTP para {domain}: {e}")
                info['observations'] = f"Erro HTTP: {str(e)}"
                return info, None

        except Exception as e:
            logger.error(f"Erro HTTP para {domain}: {e}")
            info['observations'] = f"Erro HTTP: {str(e)}"
            return info, None

    def _detect_cloud_provider(self, headers, domain):
        """Detecta o provedor de cloud baseado nos headers"""
        # Cloudflare
        if headers.get('CF-Cache-Status') or headers.get('cf-ray'):
            return 'Cloudflare'

        # AWS CloudFront
        if headers.get('X-Amz-Cf-Id') or headers.get('Via', '').find('CloudFront') != -1:
            return 'AWS CloudFront'

        # Google Cloud
        if headers.get('X-Goog-') or headers.get('Server', '').find('ghs') != -1:
            return 'Google Cloud'

        # Azure
        if headers.get('X-Azure-') or domain.endswith('.azurewebsites.net'):
            return 'Azure'

        # Vercel
        if headers.get('X-Vercel-') or headers.get('Server', '') == 'Vercel':
            return 'Vercel'

        # Netlify
        if headers.get('X-NF-Request-ID') or headers.get('Server', '') == 'Netlify':
            return 'Netlify'

        return None

    def detect_cms(self, response, domain):
        """
        Detecta o CMS usado pelo site

        Args:
            response: Resposta HTTP
            domain: Domínio

        Returns:
            Tuple (cms_name, cms_version)
        """
        if not response:
            return None, None

        html = response.text
        headers = response.headers

        cms = None
        version = None

        # WordPress
        if '/wp-content/' in html or '/wp-includes/' in html:
            cms = 'WordPress'
            # Tenta detectar versão
            version_match = re.search(r'wp-content/.*?ver=([0-9.]+)', html)
            if version_match:
                version = version_match.group(1)

            # Tenta via meta tag
            meta_match = re.search(r'<meta name="generator" content="WordPress ([0-9.]+)"', html)
            if meta_match:
                version = meta_match.group(1)

        # Joomla
        elif '/components/com_' in html or 'Joomla!' in html:
            cms = 'Joomla'
            meta_match = re.search(r'<meta name="generator" content="Joomla! ([0-9.]+)"', html)
            if meta_match:
                version = meta_match.group(1)

        # Drupal
        elif '/sites/default/' in html or '/misc/drupal.js' in html:
            cms = 'Drupal'
            meta_match = re.search(r'<meta name="generator" content="Drupal ([0-9.]+)"', html)
            if meta_match:
                version = meta_match.group(1)

        # Shopify
        elif 'Shopify' in headers.get('X-ShopId', '') or 'cdn.shopify.com' in html:
            cms = 'Shopify'

        # Wix
        elif 'X-Wix-' in str(headers) or 'wix.com' in html:
            cms = 'Wix'

        # Squarespace
        elif 'squarespace' in html.lower():
            cms = 'Squarespace'

        # Webflow
        elif 'webflow' in html.lower():
            cms = 'Webflow'

        # Ghost
        elif 'ghost' in headers.get('X-Powered-By', '').lower():
            cms = 'Ghost'

        # Hugo (gerador estático)
        elif 'hugo' in headers.get('X-Powered-By', '').lower():
            cms = 'Hugo'

        return cms, version

    def detect_analytics(self, response):
        """
        Detecta códigos de analytics e pixels

        Args:
            response: Resposta HTTP

        Returns:
            Dicionário com ga4_code e fb_pixel
        """
        analytics = {
            'ga4_code': None,
            'fb_pixel': None
        }

        if not response:
            return analytics

        html = response.text

        # Google Analytics 4 (GA4)
        ga4_match = re.search(r'G-[A-Z0-9]{10}', html)
        if ga4_match:
            analytics['ga4_code'] = ga4_match.group(0)

        # Google Analytics Universal (antigo)
        if not analytics['ga4_code']:
            ua_match = re.search(r'UA-\d+-\d+', html)
            if ua_match:
                analytics['ga4_code'] = ua_match.group(0)

        # Facebook Pixel
        fb_match = re.search(r'fbq\([\'"]init[\'"]\s*,\s*[\'"](\d+)[\'"]', html)
        if fb_match:
            analytics['fb_pixel'] = fb_match.group(1)

        return analytics

    def get_dns_info(self, domain):
        """
        Obtém informações DNS

        Args:
            domain: Domínio

        Returns:
            Dicionário com ip_address e dns_servers
        """
        info = {
            'ip_address': None,
            'dns_servers': []
        }

        try:
            # IP Address
            info['ip_address'] = socket.gethostbyname(domain)

            # Name servers
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                info['dns_servers'] = [str(ns) for ns in ns_records]
            except:
                pass

        except Exception as e:
            logger.error(f"Erro DNS para {domain}: {e}")

        return info

    def get_whois_info(self, domain):
        """
        Obtém informações WHOIS

        Args:
            domain: Domínio

        Returns:
            Dicionário com registrar, whois_created, whois_expires
        """
        info = {
            'registrar': None,
            'whois_created': None,
            'whois_expires': None
        }

        try:
            w = whois.whois(domain)

            info['registrar'] = w.registrar

            # Data de criação
            if w.creation_date:
                if isinstance(w.creation_date, list):
                    info['whois_created'] = w.creation_date[0].strftime('%Y-%m-%d')
                else:
                    info['whois_created'] = w.creation_date.strftime('%Y-%m-%d')

            # Data de expiração
            if w.expiration_date:
                if isinstance(w.expiration_date, list):
                    info['whois_expires'] = w.expiration_date[0].strftime('%Y-%m-%d')
                else:
                    info['whois_expires'] = w.expiration_date.strftime('%Y-%m-%d')

        except Exception as e:
            logger.error(f"Erro WHOIS para {domain}: {e}")

        return info

    def get_ssl_info(self, domain):
        """
        Obtém informações do certificado SSL

        Args:
            domain: Domínio

        Returns:
            Dias até expiração do SSL
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_bin = ssock.getpeercert(True)
                    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bin)

                    # Data de expiração
                    expires = datetime.strptime(
                        cert.get_notAfter().decode('ascii'),
                        '%Y%m%d%H%M%SZ'
                    )

                    days_left = (expires - datetime.now()).days
                    return days_left

        except Exception as e:
            logger.error(f"Erro SSL para {domain}: {e}")
            return None

    def check_spam_blacklist(self, ip_address):
        """
        Verifica se o IP está em blacklists de spam

        Args:
            ip_address: Endereço IP

        Returns:
            True se está em blacklist, False caso contrário
        """
        if not ip_address:
            return False

        # Lista de DNSBLs conhecidos
        blacklists = [
            'zen.spamhaus.org',
            'bl.spamcop.net',
            'b.barracudacentral.org',
            'dnsbl.sorbs.net'
        ]

        # Inverte o IP para consulta DNSBL
        reversed_ip = '.'.join(reversed(ip_address.split('.')))

        for bl in blacklists:
            try:
                query = f"{reversed_ip}.{bl}"
                socket.gethostbyname(query)
                # Se chegou aqui, está na blacklist
                logger.warning(f"IP {ip_address} encontrado em {bl}")
                return True
            except socket.gaierror:
                # Não está nesta blacklist
                continue
            except Exception as e:
                logger.error(f"Erro ao verificar blacklist {bl}: {e}")

        return False

    def collect_all_info(self, domain):
        """
        Coleta todas as informações de um domínio

        Args:
            domain: Domínio a ser analisado

        Returns:
            Dicionário completo com todas as informações
        """
        domain = self.normalize_domain(domain)

        logger.info(f"Coletando informações de {domain}")

        # Inicializa resultado com TODOS os campos esperados
        result = {
            'domain': domain,
            'status_code': None,
            'server': None,
            'cloud_provider': None,
            'cms_detected': None,
            'cms_version': None,
            'ga4_code': None,
            'fb_pixel': None,
            'ip_address': None,
            'registrar': None,
            'ssl_expires_days': None,
            'dns_servers': [],
            'whois_created': None,
            'whois_expires': None,
            'is_spam': 0,
            'observations': '',
            'raw_headers': {},
            'raw_metadata': {}
        }

        # Coleta HTTP
        http_info, response = self.collect_http_info(domain)
        result.update(http_info)

        # CMS
        cms, cms_version = self.detect_cms(response, domain)
        result['cms_detected'] = cms
        result['cms_version'] = cms_version

        # Analytics
        analytics = self.detect_analytics(response)
        result.update(analytics)

        # DNS
        dns_info = self.get_dns_info(domain)
        result.update(dns_info)

        # WHOIS
        whois_info = self.get_whois_info(domain)
        result.update(whois_info)

        # SSL
        ssl_days = self.get_ssl_info(domain)
        result['ssl_expires_days'] = ssl_days

        # Spam check
        if result.get('ip_address'):
            result['is_spam'] = 1 if self.check_spam_blacklist(result['ip_address']) else 0
        else:
            result['is_spam'] = 0

        logger.info(f"Informações de {domain} coletadas com sucesso")

        return result

    def collect_multiple(self, domains, progress_callback=None):
        """
        Coleta informações de múltiplos domínios em paralelo

        Args:
            domains: Lista de domínios
            progress_callback: Função callback para atualizar progresso

        Returns:
            Lista de dicionários com informações
        """
        results = []
        total = len(domains)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_domain = {
                executor.submit(self.collect_all_info, domain): domain
                for domain in domains
            }

            # Coleta resultados conforme completam
            for i, future in enumerate(as_completed(future_to_domain), 1):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    results.append(result)

                    if progress_callback:
                        progress_callback(i, total, domain)

                except Exception as e:
                    logger.error(f"Erro ao processar {domain}: {e}")
                    results.append({
                        'domain': domain,
                        'observations': f'Erro: {str(e)}'
                    })

                    if progress_callback:
                        progress_callback(i, total, domain)

        return results
