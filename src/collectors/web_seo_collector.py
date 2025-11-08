"""Web scrapers para obter informações de SEO gratuitas"""

import requests
import re
import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class WebSEOCollector:
    """Coleta métricas de SEO de fontes públicas gratuitas na web"""

    def __init__(self, timeout=15, semrush_api_key=None, moz_api_key=None):
        """
        Inicializa o coletor web

        Args:
            timeout: Timeout para requisições
            semrush_api_key: API key do SEMRush (opcional)
            moz_api_key: API key do MOZ (opcional)
        """
        self.timeout = timeout
        self.semrush_api_key = semrush_api_key
        self.moz_api_key = moz_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Log de API keys configuradas
        if self.semrush_api_key:
            logger.info("SEMRush API key configurada")
        if self.moz_api_key:
            logger.info("MOZ API key configurada")

    def get_semrush_data(self, domain):
        """
        Obtém dados do SEMRush via API oficial

        Args:
            domain: Nome do domínio

        Returns:
            Dict com métricas do SEMRush
        """
        result = {
            'organic_keywords': None,
            'organic_traffic': None,
            'organic_cost': None,
            'adwords_keywords': None,
            'adwords_traffic': None,
            'adwords_cost': None
        }

        if not self.semrush_api_key:
            logger.debug(f"SEMRush API key não configurada, pulando para {domain}")
            return result

        try:
            # API do SEMRush - Domain Overview
            url = "https://api.semrush.com/"
            params = {
                'type': 'domain_ranks',
                'key': self.semrush_api_key,
                'export_columns': 'Or,Ot,Oc,Ad,At,Ac',
                'domain': domain,
                'database': 'us'
            }

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                # Parse CSV response
                lines = response.text.strip().split('\n')
                if len(lines) > 1:
                    # Segunda linha contém os dados
                    data = lines[1].split(';')
                    if len(data) >= 6:
                        result['organic_keywords'] = int(data[0]) if data[0].isdigit() else None
                        result['organic_traffic'] = int(data[1]) if data[1].isdigit() else None
                        result['organic_cost'] = float(data[2]) if data[2].replace('.', '').isdigit() else None
                        result['adwords_keywords'] = int(data[3]) if data[3].isdigit() else None
                        result['adwords_traffic'] = int(data[4]) if data[4].isdigit() else None
                        result['adwords_cost'] = float(data[5]) if data[5].replace('.', '').isdigit() else None

                        logger.info(f"SEMRush dados para {domain}: {result['organic_keywords']} keywords orgânicas")
            else:
                logger.warning(f"SEMRush API retornou status {response.status_code} para {domain}")

        except Exception as e:
            logger.error(f"Erro ao buscar dados SEMRush para {domain}: {e}")

        return result

    def get_moz_data_official(self, domain):
        """
        Obtém dados do MOZ via API oficial

        Args:
            domain: Nome do domínio

        Returns:
            Dict com DA, PA, spam score
        """
        result = {
            'domain_authority': None,
            'page_authority': None,
            'spam_score': None,
            'backlinks': None
        }

        if not self.moz_api_key:
            logger.debug(f"MOZ API key não configurada, pulando para {domain}")
            return result

        try:
            # MOZ API v1 (Links API)
            # Nota: MOZ API requer access_id e secret_key separados
            # Aqui assumimos que moz_api_key está no formato "access_id:secret_key"

            if ':' in self.moz_api_key:
                access_id, secret_key = self.moz_api_key.split(':', 1)
            else:
                logger.warning("MOZ API key deve estar no formato 'access_id:secret_key'")
                return result

            import hmac
            import hashlib
            import base64
            import time as time_module

            # Prepara autenticação HMAC
            expires = int(time_module.time()) + 300  # 5 minutos
            string_to_sign = f"{access_id}\n{expires}"

            signature = base64.b64encode(
                hmac.new(
                    secret_key.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha1
                ).digest()
            ).decode('utf-8')

            # URL Metrics API
            url = f"https://lsapi.seomoz.com/v2/url_metrics"

            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{access_id}:{secret_key}".encode()).decode()}'
            }

            payload = {
                'targets': [f'https://{domain}']
            }

            response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    metrics = data['results'][0]

                    result['domain_authority'] = metrics.get('domain_authority')
                    result['page_authority'] = metrics.get('page_authority')
                    result['spam_score'] = metrics.get('spam_score')

                    logger.info(f"MOZ DA para {domain}: {result['domain_authority']}")
            else:
                logger.warning(f"MOZ API retornou status {response.status_code} para {domain}")

        except Exception as e:
            logger.error(f"Erro ao buscar dados MOZ oficiais para {domain}: {e}")

        return result

    def get_moz_rank(self, domain):
        """
        Tenta obter MOZ Domain Authority (tenta API oficial primeiro, depois scraper)

        Args:
            domain: Nome do domínio

        Returns:
            Dict com DA, PA, spam score
        """
        # Tenta API oficial primeiro
        if self.moz_api_key:
            result = self.get_moz_data_official(domain)
            if result['domain_authority'] is not None:
                return result

        # Fallback para scraper público
        result = {
            'domain_authority': None,
            'page_authority': None,
            'spam_score': None,
            'backlinks': None
        }

        try:
            # Usa checker público gratuito
            url = f"https://www.prepostseo.com/checkPageAuthority"

            data = {
                'newtest': domain,
                'check': '1'
            }

            response = self.session.post(url, data=data, timeout=self.timeout)

            if response.status_code == 200:
                # Parse resposta
                soup = BeautifulSoup(response.text, 'html.parser')

                # Tenta extrair DA
                da_elem = soup.find(text=re.compile(r'Domain Authority', re.I))
                if da_elem:
                    parent = da_elem.find_parent()
                    if parent:
                        numbers = re.findall(r'\d+', parent.get_text())
                        if numbers:
                            result['domain_authority'] = int(numbers[0])

                # Tenta extrair PA
                pa_elem = soup.find(text=re.compile(r'Page Authority', re.I))
                if pa_elem:
                    parent = pa_elem.find_parent()
                    if parent:
                        numbers = re.findall(r'\d+', parent.get_text())
                        if numbers:
                            result['page_authority'] = int(numbers[0])

                logger.info(f"MOZ DA para {domain}: {result['domain_authority']}")

        except Exception as e:
            logger.error(f"Erro ao buscar MOZ rank para {domain}: {e}")

        return result

    def get_alexa_rank(self, domain):
        """
        Busca ranking de tráfego (alternativas ao Alexa)

        Args:
            domain: Nome do domínio

        Returns:
            Dict com ranking global e país
        """
        result = {
            'global_rank': None,
            'country_rank': None,
            'country': None
        }

        try:
            # Usa SimilarWeb (dados públicos limitados)
            url = f"https://www.similarweb.com/website/{domain}/"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Busca ranking global
                rank_elem = soup.find(text=re.compile(r'Global Rank', re.I))
                if rank_elem:
                    parent = rank_elem.find_parent()
                    if parent:
                        # Busca número no formato "123,456" ou "#123456"
                        numbers = re.findall(r'[\d,]+', parent.get_text())
                        if numbers:
                            rank_str = numbers[0].replace(',', '')
                            result['global_rank'] = int(rank_str)

                logger.info(f"Ranking global para {domain}: {result['global_rank']}")

        except Exception as e:
            logger.error(f"Erro ao buscar ranking para {domain}: {e}")

        # Pequeno delay para não sobrecarregar
        time.sleep(1)

        return result

    def get_domain_age(self, domain):
        """
        Busca idade do domínio

        Args:
            domain: Nome do domínio

        Returns:
            Dict com data de criação e idade em dias
        """
        result = {
            'creation_date': None,
            'age_days': None
        }

        try:
            # Usa API pública gratuita
            url = f"https://api.domainsdb.info/v1/domains/search?domain={domain}"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if data.get('domains'):
                    first_domain = data['domains'][0]
                    create_date = first_domain.get('create_date')

                    if create_date:
                        result['creation_date'] = create_date

                        # Calcula idade
                        from datetime import datetime
                        created = datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                        age = datetime.now(created.tzinfo) - created
                        result['age_days'] = age.days

                logger.info(f"Idade do domínio {domain}: {result['age_days']} dias")

        except Exception as e:
            logger.error(f"Erro ao buscar idade do domínio {domain}: {e}")

        return result

    def get_backlinks_estimate(self, domain):
        """
        Estima número de backlinks

        Args:
            domain: Nome do domínio

        Returns:
            Estimativa de backlinks
        """
        try:
            # Usa checker público
            url = f"https://www.backlinkwatch.com/index.php"

            data = {
                'url': f"https://{domain}",
                'check': 'Check'
            }

            response = self.session.post(url, data=data, timeout=self.timeout)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Procura por número de backlinks
                text = soup.get_text()
                match = re.search(r'(\d+)\s*backlinks?', text, re.I)
                if match:
                    count = int(match.group(1))
                    logger.info(f"Backlinks para {domain}: {count}")
                    return count

        except Exception as e:
            logger.error(f"Erro ao buscar backlinks para {domain}: {e}")

        return None

    def check_social_presence(self, domain):
        """
        Verifica presença em redes sociais

        Args:
            domain: Nome do domínio

        Returns:
            Dict com shares em redes sociais
        """
        result = {
            'facebook_shares': None,
            'twitter_mentions': None
        }

        try:
            # Facebook share count (API pública)
            fb_url = f"https://graph.facebook.com/?id=https://{domain}"
            response = self.session.get(fb_url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                shares = data.get('share', {}).get('share_count')
                if shares:
                    result['facebook_shares'] = shares
                    logger.info(f"Facebook shares para {domain}: {shares}")

        except Exception as e:
            logger.error(f"Erro ao buscar shares do Facebook para {domain}: {e}")

        return result

    def get_dns_health(self, domain):
        """
        Verifica saúde do DNS

        Args:
            domain: Nome do domínio

        Returns:
            Dict com status DNS
        """
        result = {
            'dns_propagated': False,
            'nameservers_count': 0,
            'has_spf': False,
            'has_dkim': False,
            'has_dmarc': False
        }

        try:
            import dns.resolver

            # Nameservers
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                result['nameservers_count'] = len(list(ns_records))
                result['dns_propagated'] = True
            except:
                pass

            # SPF record
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                for record in txt_records:
                    txt = str(record)
                    if 'v=spf1' in txt.lower():
                        result['has_spf'] = True
                    if 'v=dmarc1' in txt.lower():
                        result['has_dmarc'] = True
            except:
                pass

            logger.info(f"DNS health para {domain}: {result}")

        except Exception as e:
            logger.error(f"Erro ao verificar DNS de {domain}: {e}")

        return result

    def get_hosting_provider(self, ip_address):
        """
        Identifica provedor de hosting pelo IP

        Args:
            ip_address: Endereço IP

        Returns:
            Nome do hosting provider
        """
        if not ip_address:
            return None

        try:
            # Usa API pública de geolocalização/ASN
            url = f"https://ipapi.co/{ip_address}/json/"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # Informações do ASN (Autonomous System)
                org = data.get('org', '')
                asn = data.get('asn', '')

                # Identifica provedores conhecidos
                providers = {
                    'Amazon': 'AWS',
                    'Google': 'Google Cloud',
                    'Microsoft': 'Azure',
                    'DigitalOcean': 'DigitalOcean',
                    'Linode': 'Linode',
                    'OVH': 'OVH',
                    'Hetzner': 'Hetzner',
                    'Cloudflare': 'Cloudflare',
                    'GoDaddy': 'GoDaddy',
                    'Hostinger': 'Hostinger',
                    'Bluehost': 'Bluehost',
                    'SiteGround': 'SiteGround',
                    'DreamHost': 'DreamHost',
                    'HostGator': 'HostGator',
                    'A2 Hosting': 'A2 Hosting'
                }

                for key, value in providers.items():
                    if key.lower() in org.lower():
                        logger.info(f"Hosting provider para {ip_address}: {value}")
                        return value

                # Retorna org name se não identificou provider específico
                if org:
                    return org

        except Exception as e:
            logger.error(f"Erro ao identificar hosting de {ip_address}: {e}")

        return None

    def collect_all_web_seo(self, domain, ip_address=None):
        """
        Coleta todas as métricas de SEO da web

        Args:
            domain: Nome do domínio
            ip_address: IP (opcional, para hosting)

        Returns:
            Dict com todas as métricas
        """
        logger.info(f"Coletando SEO da web para {domain}")

        result = {
            'semrush_data': {},
            'moz_data': {},
            'traffic_rank': {},
            'domain_age': {},
            'backlinks_count': None,
            'social_data': {},
            'dns_health': {},
            'hosting_provider': None
        }

        try:
            # SEMRush metrics (se API key configurada)
            if self.semrush_api_key:
                result['semrush_data'] = self.get_semrush_data(domain)
                time.sleep(1)  # Delay entre requests
        except:
            pass

        try:
            # MOZ metrics (tenta API oficial primeiro)
            result['moz_data'] = self.get_moz_rank(domain)
            time.sleep(2)  # Delay entre requests
        except:
            pass

        try:
            # Traffic rank
            result['traffic_rank'] = self.get_alexa_rank(domain)
            time.sleep(2)
        except:
            pass

        try:
            # Domain age
            result['domain_age'] = self.get_domain_age(domain)
            time.sleep(1)
        except:
            pass

        try:
            # Backlinks
            result['backlinks_count'] = self.get_backlinks_estimate(domain)
            time.sleep(2)
        except:
            pass

        try:
            # Social presence
            result['social_data'] = self.check_social_presence(domain)
            time.sleep(1)
        except:
            pass

        try:
            # DNS health
            result['dns_health'] = self.get_dns_health(domain)
        except:
            pass

        try:
            # Hosting provider
            if ip_address:
                result['hosting_provider'] = self.get_hosting_provider(ip_address)
                time.sleep(1)
        except:
            pass

        logger.info(f"SEO da web coletado para {domain}")

        return result
