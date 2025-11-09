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
from src.collectors.cms_detector import CMSDetector
from src.collectors.whois_collector import WhoisCollector
from src.collectors.dns_collector import DNSCollector
from src.collectors.ssl_collector import SSLCollector
from src.collectors.security_collector import SecurityCollector
from src.collectors.performance_collector import PerformanceCollector
from src.collectors.geolocation_collector import GeolocationCollector

logger = logging.getLogger(__name__)


class DomainCollector:
    """Coleta informações completas de um domínio"""

    def __init__(self, timeout=5, max_workers=10, collect_web_seo=False, semrush_api_key=None, moz_api_key=None, wappalyzer_key=None, whatcms_key=None, virustotal_api_key=None, google_safe_browsing_key=None, pagespeed_api_key=None):
        """
        Inicializa o coletor

        Args:
            timeout: Timeout para requisições HTTP em segundos
            max_workers: Número máximo de threads paralelas
            collect_web_seo: Se True, coleta SEO da web (mais lento)
            semrush_api_key: API key do SEMRush (opcional)
            moz_api_key: API key do MOZ (opcional)
            wappalyzer_key: API key do Wappalyzer (opcional)
            whatcms_key: API key do WhatCMS (opcional)
            virustotal_api_key: API key do VirusTotal (opcional)
            google_safe_browsing_key: API key do Google Safe Browsing (opcional)
            pagespeed_api_key: API key do Google PageSpeed Insights (opcional)
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.collect_web_seo = collect_web_seo
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Inicializa CMS detector
        self.cms_detector = CMSDetector(
            timeout=timeout,
            wappalyzer_key=wappalyzer_key,
            whatcms_key=whatcms_key
        )
        logger.info("CMS Detector inicializado")

        # Inicializa WHOIS collector
        self.whois_collector = WhoisCollector(timeout=timeout)
        logger.info("WHOIS Collector inicializado")

        # Inicializa DNS collector
        self.dns_collector = DNSCollector(timeout=timeout)
        logger.info("DNS Collector inicializado")

        # Inicializa SSL collector
        self.ssl_collector = SSLCollector(timeout=timeout)
        logger.info("SSL Collector inicializado")

        # Inicializa Security collector
        self.security_collector = SecurityCollector(
            timeout=timeout,
            virustotal_api_key=virustotal_api_key,
            google_safe_browsing_key=google_safe_browsing_key
        )
        logger.info("Security Collector inicializado")

        # Inicializa Performance collector
        self.performance_collector = PerformanceCollector(
            timeout=timeout * 3,  # PageSpeed pode ser lento
            pagespeed_api_key=pagespeed_api_key
        )
        logger.info("Performance Collector inicializado")

        # Inicializa Geolocation collector
        self.geolocation_collector = GeolocationCollector(timeout=timeout)
        logger.info("Geolocation Collector inicializado")

        # Inicializa web SEO collector se necessário
        self.web_seo_collector = None
        if self.collect_web_seo:
            try:
                from src.collectors.web_seo_collector import WebSEOCollector
                self.web_seo_collector = WebSEOCollector(
                    timeout=timeout * 2,
                    semrush_api_key=semrush_api_key,
                    moz_api_key=moz_api_key
                )
                logger.info("Web SEO collector ativado")
            except Exception as e:
                logger.warning(f"Não foi possível ativar Web SEO collector: {e}")
                self.collect_web_seo = False

    def normalize_domain(self, domain, keep_subdomain=True, keep_path=False):
        """
        Normaliza o domínio/URL

        Args:
            domain: Domínio ou URL a ser normalizado
            keep_subdomain: Se True, mantém subdomínios (blog.site.com)
            keep_path: Se True, mantém o path completo

        Returns:
            Domínio/URL normalizado
        """
        # Remove espaços
        domain = domain.strip()

        # Adiciona protocolo se não tiver
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain

        # Parse URL
        parsed = urlparse(domain)
        hostname = parsed.netloc or parsed.path.split('/')[0]

        # Remove porta se tiver
        hostname = hostname.split(':')[0]

        # Remove www apenas se keep_subdomain for False
        if not keep_subdomain:
            hostname = re.sub(r'^www\.', '', hostname)

        result = hostname.lower()

        # Adiciona path se solicitado
        if keep_path and parsed.path and parsed.path != '/':
            result = result + parsed.path

        return result

    def collect_http_info(self, domain):
        """
        Coleta informações HTTP do domínio

        Args:
            domain: Domínio a ser analisado

        Returns:
            Dicionário com informações HTTP e response
        """
        info = {
            'status_code': None,
            'server': None,
            'cloud_provider': None,
            'raw_headers': {},
            'redirect_count': 0
        }

        try:
            # Tenta HTTPS primeiro
            url = f"https://{domain}"
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            info['status_code'] = response.status_code
            info['raw_headers'] = dict(response.headers)

            # Conta redirects
            info['redirect_count'] = len(response.history)

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
        Detecta o CMS usado pelo site usando Wappalyzer, WhatCMS e fallbacks

        Args:
            response: Resposta HTTP
            domain: Domínio

        Returns:
            Tuple (cms_name, cms_version)
        """
        if not response:
            return None, None

        try:
            # Usa o novo CMSDetector que tenta Wappalyzer -> WhatCMS -> HTML analysis
            html_content = response.text if response else None
            cms_info = self.cms_detector.detect_cms(domain, html_content=html_content)

            return cms_info['name'], cms_info['version']

        except Exception as e:
            logger.error(f"Erro ao detectar CMS para {domain}: {e}")
            return None, None

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

    def _whois_query_socket(self, server, query, port=43, timeout=10):
        """
        Faz consulta WHOIS via socket direto

        Args:
            server: Servidor WHOIS
            query: Domínio para consultar
            port: Porta (padrão 43)
            timeout: Timeout em segundos

        Returns:
            Texto da resposta WHOIS
        """
        # Validação de entrada
        if not server or not query:
            logger.warning(f"Servidor ou query vazios: server={server}, query={query}")
            return ""

        if not isinstance(server, str) or not isinstance(query, str):
            logger.warning(f"Servidor ou query com tipo inválido: server={type(server)}, query={type(query)}")
            return ""

        server = server.strip()
        query = query.strip()

        if not server or not query:
            logger.warning(f"Servidor ou query vazios após strip: server={server}, query={query}")
            return ""

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((server, port))
            s.send((query + "\r\n").encode())
            resp = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                resp += data
            s.close()
            return resp.decode(errors="ignore")
        except socket.gaierror as e:
            logger.warning(f"Servidor WHOIS não encontrado ou inválido: {server} - {e}")
            return ""
        except socket.timeout:
            logger.warning(f"Timeout na consulta WHOIS para {query} em {server}")
            return ""
        except Exception as e:
            logger.warning(f"Erro na consulta socket WHOIS para {query} em {server}: {e}")
            return ""

    def _find_whois_server(self, domain):
        """
        Descobre o servidor WHOIS adequado para o domínio

        Args:
            domain: Domínio

        Returns:
            Servidor WHOIS ou None
        """
        try:
            # Primeiro tenta IANA
            resp = self._whois_query_socket("whois.iana.org", domain)
            for line in resp.splitlines():
                if line.lower().startswith("whois:"):
                    return line.split(":", 1)[1].strip()

            # Fallback baseado na TLD
            tld = domain.split('.')[-1].lower()
            tld_servers = {
                'com': 'whois.verisign-grs.com',
                'net': 'whois.verisign-grs.com',
                'org': 'whois.pir.org',
                'br': 'whois.registro.br',
                'info': 'whois.afilias.net',
                'biz': 'whois.biz',
                'io': 'whois.nic.io',
                'co': 'whois.nic.co',
                'uk': 'whois.nic.uk',
                'us': 'whois.nic.us',
                'ca': 'whois.cira.ca',
                'de': 'whois.denic.de',
                'eu': 'whois.eu',
                'nl': 'whois.domain-registry.nl',
                'fr': 'whois.afnic.fr',
                'au': 'whois.auda.org.au',
                'ru': 'whois.tcinet.ru',
                'cn': 'whois.cnnic.cn',
                'in': 'whois.registry.in',
                'jp': 'whois.jprs.jp',
            }
            return tld_servers.get(tld)

        except Exception as e:
            logger.error(f"Erro ao encontrar servidor WHOIS para {domain}: {e}")
            return None

    def _parse_whois_registrar(self, whois_text, domain):
        """
        Faz parsing do texto WHOIS para extrair o registrar

        Args:
            whois_text: Texto bruto do WHOIS
            domain: Domínio (para contexto de TLD)

        Returns:
            Nome do registrar ou None
        """
        if not whois_text:
            return None

        # Múltiplas estratégias de parsing
        patterns = [
            r'(?:^|\n)registrar:\s*(.+?)(?:\n|$)',  # Padrão comum
            r'(?:^|\n)registrar name:\s*(.+?)(?:\n|$)',  # Variação
            r'(?:^|\n)sponsoring registrar:\s*(.+?)(?:\n|$)',  # .uk e outros
            r'(?:^|\n)registrar organization:\s*(.+?)(?:\n|$)',  # Alguns gTLDs
            r'(?:^|\n)registro criado por:\s*(.+?)(?:\n|$)',  # .br português
            r'(?:^|\n)responsible registrar:\s*(.+?)(?:\n|$)',  # .br inglês
            r'(?:^|\n)registrar whois server:\s*(.+?)(?:\n|$)',  # Informação alternativa
        ]

        text_lower = whois_text.lower()

        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if matches:
                registrar = matches[0].strip()
                if registrar and registrar not in ['not disclosed', 'redacted', 'n/a', 'none']:
                    return registrar

        # Para domínios .br, tenta buscar owner/responsible
        if domain.endswith('.br'):
            br_patterns = [
                r'(?:^|\n)owner:\s*(.+?)(?:\n|$)',
                r'(?:^|\n)responsible:\s*(.+?)(?:\n|$)',
                r'(?:^|\n)owner-c:\s*(.+?)(?:\n|$)',
            ]
            for pattern in br_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                if matches:
                    owner = matches[0].strip()
                    if owner and len(owner) > 3:
                        return f"Owner: {owner}"

        return None

    def _parse_whois_dates(self, whois_text):
        """
        Extrai datas de criação e expiração do texto WHOIS

        Args:
            whois_text: Texto bruto do WHOIS

        Returns:
            Tupla (data_criacao, data_expiracao) em formato 'YYYY-MM-DD' ou None
        """
        created = None
        expires = None

        if not whois_text:
            return created, expires

        # Padrões de data
        date_patterns = {
            'created': [
                r'creation date:\s*(\d{4}-\d{2}-\d{2})',
                r'created:\s*(\d{4}-\d{2}-\d{2})',
                r'created on:\s*(\d{4}-\d{2}-\d{2})',
                r'registration time:\s*(\d{4}-\d{2}-\d{2})',
                r'criado:\s*(\d{8})',  # .br formato YYYYMMDD
            ],
            'expires': [
                r'expir(?:y|ation) date:\s*(\d{4}-\d{2}-\d{2})',
                r'expires:\s*(\d{4}-\d{2}-\d{2})',
                r'expires on:\s*(\d{4}-\d{2}-\d{2})',
                r'expiration time:\s*(\d{4}-\d{2}-\d{2})',
                r'validade:\s*(\d{8})',  # .br formato YYYYMMDD
            ]
        }

        text_lower = whois_text.lower()

        # Busca data de criação
        for pattern in date_patterns['created']:
            matches = re.findall(pattern, text_lower)
            if matches:
                date_str = matches[0]
                # Converte formato YYYYMMDD para YYYY-MM-DD se necessário
                if len(date_str) == 8 and date_str.isdigit():
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                created = date_str
                break

        # Busca data de expiração
        for pattern in date_patterns['expires']:
            matches = re.findall(pattern, text_lower)
            if matches:
                date_str = matches[0]
                # Converte formato YYYYMMDD para YYYY-MM-DD se necessário
                if len(date_str) == 8 and date_str.isdigit():
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                expires = date_str
                break

        return created, expires

    def get_whois_info(self, domain):
        """
        Obtém informações WHOIS com múltiplos fallbacks

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

        # ESTRATÉGIA 1: Biblioteca python-whois (tentativa rápida)
        try:
            w = whois.whois(domain)

            # Tenta extrair registrar
            if hasattr(w, 'registrar') and w.registrar:
                if isinstance(w.registrar, list):
                    info['registrar'] = w.registrar[0] if w.registrar[0] else None
                else:
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

            # Se conseguiu registrar, retorna
            if info['registrar']:
                logger.info(f"WHOIS via biblioteca para {domain}: registrar={info['registrar']}")
                return info

        except Exception as e:
            logger.warning(f"Biblioteca whois falhou para {domain}: {e}")

        # ESTRATÉGIA 2: Consulta via socket com parsing manual
        try:
            logger.info(f"Tentando WHOIS via socket para {domain}")

            # Descobre servidor adequado
            whois_server = self._find_whois_server(domain)

            if whois_server:
                # Faz consulta
                whois_text = self._whois_query_socket(whois_server, domain)

                if whois_text:
                    # Extrai registrar
                    registrar = self._parse_whois_registrar(whois_text, domain)
                    if registrar:
                        info['registrar'] = registrar
                        logger.info(f"WHOIS via socket para {domain}: registrar={registrar}")

                    # Extrai datas se ainda não tem
                    if not info['whois_created'] or not info['whois_expires']:
                        created, expires = self._parse_whois_dates(whois_text)
                        if created:
                            info['whois_created'] = created
                        if expires:
                            info['whois_expires'] = expires

        except Exception as e:
            logger.error(f"Erro WHOIS via socket para {domain}: {e}")

        # ESTRATÉGIA 3: Fallback especial para .br
        if domain.endswith('.br') and not info['registrar']:
            try:
                logger.info(f"Tentando WHOIS específico .br para {domain}")
                whois_text = self._whois_query_socket("whois.registro.br", domain)

                if whois_text:
                    registrar = self._parse_whois_registrar(whois_text, domain)
                    if registrar:
                        info['registrar'] = registrar
                        logger.info(f"WHOIS .br para {domain}: registrar={registrar}")

                    # Tenta datas também
                    if not info['whois_created'] or not info['whois_expires']:
                        created, expires = self._parse_whois_dates(whois_text)
                        if created:
                            info['whois_created'] = created
                        if expires:
                            info['whois_expires'] = expires

            except Exception as e:
                logger.error(f"Erro WHOIS .br para {domain}: {e}")

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

    def _estimate_annual_cost(self, domain):
        """
        Estima o custo anual aproximado do domínio baseado na TLD

        Args:
            domain: Nome do domínio

        Returns:
            Custo estimado em USD ou None
        """
        tld = domain.split('.')[-1].lower()

        # Tabela de custos médios anuais por TLD (em USD)
        tld_costs = {
            'com': 15, 'net': 15, 'org': 15, 'info': 15,
            'br': 20, 'com.br': 20, 'net.br': 20, 'org.br': 20,
            'co': 25, 'io': 40, 'ai': 80, 'app': 18,
            'dev': 15, 'blog': 30, 'shop': 35, 'store': 60,
            'online': 40, 'site': 25, 'website': 25,
            'tech': 55, 'cloud': 25, 'digital': 35,
            'pro': 20, 'biz': 20, 'me': 20, 'tv': 40,
            'cc': 25, 'ws': 10, 'us': 10, 'uk': 10,
            'xyz': 12, 'top': 8, 'club': 15, 'life': 30,
            'live': 25, 'today': 25, 'world': 30,
            'education': 25, 'academy': 35, 'institute': 25,
            'agency': 25, 'studio': 25, 'design': 55,
            'art': 15, 'gallery': 25, 'photo': 35,
            'ninja': 25, 'expert': 55, 'guru': 35,
            'med.br': 30, 'art.br': 20
        }

        return tld_costs.get(tld, 20)  # Default: $20/ano

    def discover_subdomains(self, domain):
        """
        Descobre subdomínios via DNS

        NOTA: Esta função está DESATIVADA por padrão pois pode descobrir
        subdomínios que não pertencem ao usuário (especialmente com TLDs compostos).

        Args:
            domain: Domínio base

        Returns:
            Lista vazia (função desativada)
        """
        # DESATIVADO: Esta função estava descobrindo subdomínios incorretos
        # especialmente para TLDs compostos (.med.br, .com.br, etc)
        # Exemplo: para "exemplo.med.br" estava tentando descobrir "www.med.br"
        logger.debug(f"Descoberta automática de subdomínios desativada para {domain}")
        return []

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
            'raw_metadata': {},
            'redirect_count': 0,
            'discovered_subdomains': [],
            'estimated_annual_cost': None,
            # Novos campos WHOIS
            'whois_updated': None,
            'whois_status': None,
            'whois_nameservers': None,
            'whois_registrant_name': None,
            'whois_registrant_org': None,
            'days_until_expiration': None,
            # Campos DNS
            'dns_a_records': None,
            'dns_mx_records': None,
            'dns_txt_records': None,
            'dns_ns_records': None,
            # Campos email auth
            'spf_record': None,
            'spf_valid': 0,
            'dmarc_record': None,
            'dmarc_policy': None,
            'dkim_configured': 0,
            # Campos SSL
            'ssl_issuer': None,
            'ssl_valid_from': None,
            'ssl_valid_until': None,
            'ssl_san_domains': None,
            'ssl_is_valid': 0,
            'ssl_chain_valid': 0,
            'ssl_signature_algorithm': None,
            # Campos segurança
            'virustotal_malicious': 0,
            'virustotal_suspicious': 0,
            'virustotal_reputation': 0,
            'gsb_is_safe': 1,
            'gsb_threats': None,
            'blacklist_count': 0,
            'reputation_score': 0,
            # Campos IP
            'ip_reverse_dns': None,
            'ip_asn': None,
            'ip_country': None,
            'ip_city': None,
            'ip_latitude': None,
            'ip_longitude': None,
            'ip_timezone': None,
            'ip_isp': None,
            'ip_organization': None,
            # Campos Performance
            'performance_score': None,
            'performance_fcp': None,
            'performance_lcp': None,
            'performance_fid': None,
            'performance_cls': None,
            'performance_ttfb': None,
            'performance_tti': None,
            'performance_tbt': None,
            'performance_speed_index': None
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

        # Descoberta de subdomínios (opcional, pode ser lento)
        try:
            subdomains = self.discover_subdomains(domain)
            result['discovered_subdomains'] = subdomains
        except Exception as e:
            logger.error(f"Erro ao descobrir subdomínios de {domain}: {e}")
            result['discovered_subdomains'] = []

        # Estimativa de custo anual (baseado na TLD)
        try:
            result['estimated_annual_cost'] = self._estimate_annual_cost(domain)
        except:
            result['estimated_annual_cost'] = None

        # Web SEO (opcional, mais lento)
        if self.collect_web_seo and self.web_seo_collector:
            try:
                logger.info(f"Coletando SEO da web para {domain}...")
                web_seo = self.web_seo_collector.collect_all_web_seo(domain, result.get('ip_address'))

                # Mescla resultados
                if web_seo.get('moz_data'):
                    result['domain_authority'] = web_seo['moz_data'].get('domain_authority')
                    result['page_authority'] = web_seo['moz_data'].get('page_authority')

                if web_seo.get('traffic_rank'):
                    result['global_rank'] = web_seo['traffic_rank'].get('global_rank')

                if web_seo.get('domain_age'):
                    result['domain_age_days'] = web_seo['domain_age'].get('age_days')

                result['backlinks_count'] = web_seo.get('backlinks_count')
                result['hosting_provider'] = web_seo.get('hosting_provider')

                logger.info(f"SEO da web coletado para {domain}")
            except Exception as e:
                logger.error(f"Erro ao coletar SEO da web de {domain}: {e}")

        # === NOVOS COLETORES DE MONITORAMENTO ===

        # WHOIS detalhado (usando novo coletor)
        try:
            logger.debug(f"Coletando dados WHOIS detalhados para {domain}...")
            whois_data = self.whois_collector.get_whois_data(domain)
            if whois_data.get('updated_date'):
                result['whois_updated'] = whois_data['updated_date']
            if whois_data.get('status'):
                result['whois_status'] = whois_data['status']
            if whois_data.get('name_servers'):
                result['whois_nameservers'] = whois_data['name_servers']
            if whois_data.get('registrant_name'):
                result['whois_registrant_name'] = whois_data['registrant_name']
            if whois_data.get('registrant_org'):
                result['whois_registrant_org'] = whois_data['registrant_org']
            if whois_data.get('days_until_expiration') is not None:
                result['days_until_expiration'] = whois_data['days_until_expiration']
            if whois_data.get('domain_age_days') is not None:
                result['domain_age_days'] = whois_data['domain_age_days']
        except Exception as e:
            logger.debug(f"Erro ao coletar WHOIS detalhado de {domain}: {e}")

        # DNS records completos
        try:
            logger.debug(f"Coletando registros DNS para {domain}...")
            dns_data = self.dns_collector.get_dns_records(domain)
            import json
            if dns_data.get('a_records'):
                result['dns_a_records'] = json.dumps(dns_data['a_records'])
            if dns_data.get('mx_records'):
                result['dns_mx_records'] = json.dumps(dns_data['mx_records'])
            if dns_data.get('txt_records'):
                result['dns_txt_records'] = json.dumps(dns_data['txt_records'])
            if dns_data.get('ns_records'):
                result['dns_ns_records'] = json.dumps(dns_data['ns_records'])
        except Exception as e:
            logger.debug(f"Erro ao coletar DNS de {domain}: {e}")

        # Autenticação de email (SPF, DMARC, DKIM)
        try:
            logger.debug(f"Verificando autenticação de email para {domain}...")
            email_auth = self.dns_collector.check_email_authentication(domain)

            if email_auth.get('spf', {}).get('configured'):
                result['spf_record'] = email_auth['spf'].get('record')
                result['spf_valid'] = 1 if email_auth['spf'].get('valid') else 0

            if email_auth.get('dmarc', {}).get('configured'):
                result['dmarc_record'] = email_auth['dmarc'].get('record')
                result['dmarc_policy'] = email_auth['dmarc'].get('policy')

            if email_auth.get('dkim', {}).get('configured'):
                result['dkim_configured'] = 1
        except Exception as e:
            logger.debug(f"Erro ao verificar autenticação de email de {domain}: {e}")

        # SSL/TLS detalhado
        try:
            logger.debug(f"Coletando informações SSL detalhadas para {domain}...")
            ssl_data = self.ssl_collector.get_ssl_info(domain)

            if ssl_data.get('has_ssl'):
                result['ssl_issuer'] = ssl_data.get('issuer')
                result['ssl_valid_from'] = ssl_data.get('valid_from')
                result['ssl_valid_until'] = ssl_data.get('valid_until')
                result['ssl_is_valid'] = 1 if ssl_data.get('is_valid') else 0
                result['ssl_signature_algorithm'] = ssl_data.get('signature_algorithm')

                if ssl_data.get('san_domains'):
                    import json
                    result['ssl_san_domains'] = json.dumps(ssl_data['san_domains'])

                # Verifica cadeia SSL
                chain_check = self.ssl_collector.verify_ssl_chain(domain)
                result['ssl_chain_valid'] = 1 if chain_check.get('valid_chain') else 0
        except Exception as e:
            logger.debug(f"Erro ao coletar SSL detalhado de {domain}: {e}")

        # Reverse DNS
        if result.get('ip_address'):
            try:
                reverse_dns = self.dns_collector.get_reverse_dns(result['ip_address'])
                if reverse_dns:
                    result['ip_reverse_dns'] = reverse_dns
            except Exception as e:
                logger.debug(f"Erro ao obter reverse DNS: {e}")

        # Blacklists (VirusTotal, Google Safe Browsing)
        try:
            logger.debug(f"Verificando blacklists e segurança para {domain}...")

            # VirusTotal
            vt_result = self.security_collector.check_virustotal(domain)
            if vt_result.get('scanned'):
                result['virustotal_malicious'] = vt_result.get('malicious_count', 0)
                result['virustotal_suspicious'] = vt_result.get('suspicious_count', 0)
                result['virustotal_reputation'] = vt_result.get('reputation', 0)

            # Google Safe Browsing
            gsb_result = self.security_collector.check_google_safe_browsing(domain)
            if gsb_result.get('scanned'):
                result['gsb_is_safe'] = 1 if gsb_result.get('is_safe') else 0
                if gsb_result.get('threat_types'):
                    import json
                    result['gsb_threats'] = json.dumps(gsb_result['threat_types'])

            # Blacklists públicas (DNSBL) usando IP
            if result.get('ip_address'):
                bl_result = self.security_collector.check_public_blacklists(result['ip_address'])
                if bl_result.get('checked'):
                    result['blacklist_count'] = bl_result.get('total_blacklisted', 0)

            # Score geral de reputação
            reputation = self.security_collector.check_domain_reputation(domain)
            result['reputation_score'] = reputation.get('reputation_score', 0)

        except Exception as e:
            logger.debug(f"Erro ao verificar segurança de {domain}: {e}")

        # Geolocalização (se tiver IP)
        if result.get('ip_address'):
            try:
                logger.debug(f"Obtendo geolocalização do IP {result['ip_address']}...")
                geo_data = self.geolocation_collector.get_ip_geolocation(result['ip_address'])

                if geo_data.get('country'):
                    result['ip_country'] = geo_data.get('country')
                    result['ip_city'] = geo_data.get('city')
                    result['ip_latitude'] = geo_data.get('latitude')
                    result['ip_longitude'] = geo_data.get('longitude')
                    result['ip_timezone'] = geo_data.get('timezone')
                    result['ip_isp'] = geo_data.get('isp')
                    result['ip_organization'] = geo_data.get('organization')

                    # Atualiza ASN se disponível e ainda não temos
                    if geo_data.get('asn') and not result.get('ip_asn'):
                        result['ip_asn'] = geo_data.get('asn')

            except Exception as e:
                logger.debug(f"Erro ao obter geolocalização: {e}")

        # Performance (PageSpeed Insights) - OPCIONAL, pode ser lento
        # Só executa se collect_web_seo estiver ativado para evitar lentidão
        if self.collect_web_seo:
            try:
                logger.debug(f"Obtendo métricas de performance para {domain}...")
                perf_data = self.performance_collector.get_pagespeed_metrics(domain, strategy='mobile')

                if perf_data.get('performance_score') is not None:
                    result['performance_score'] = perf_data.get('performance_score')
                    result['performance_fcp'] = perf_data.get('fcp')
                    result['performance_lcp'] = perf_data.get('lcp')
                    result['performance_fid'] = perf_data.get('fid')
                    result['performance_cls'] = perf_data.get('cls')
                    result['performance_ttfb'] = perf_data.get('ttfb')
                    result['performance_tti'] = perf_data.get('tti')
                    result['performance_tbt'] = perf_data.get('tbt')
                    result['performance_speed_index'] = perf_data.get('speed_index')

            except Exception as e:
                logger.debug(f"Erro ao obter performance de {domain}: {e}")

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
        # Remove duplicatas (mantendo subdomínios e paths únicos)
        unique_domains = list(set([self.normalize_domain(d, keep_subdomain=True, keep_path=False) for d in domains]))

        logger.info(f"Processando {len(unique_domains)} domínios únicos (de {len(domains)} fornecidos)")

        results = []
        total = len(unique_domains)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_domain = {
                executor.submit(self.collect_all_info, domain): domain
                for domain in unique_domains
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
