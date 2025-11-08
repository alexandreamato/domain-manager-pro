"""
Coletor de informações de segurança e blacklists
"""
import requests
import logging
import hashlib
from typing import Dict, List
from urllib.parse import quote

logger = logging.getLogger(__name__)


class SecurityCollector:
    """Coleta informações de segurança, blacklists e reputação de domínios"""

    def __init__(self, timeout=15, virustotal_api_key=None, google_safe_browsing_key=None):
        """
        Inicializa o coletor de segurança

        Args:
            timeout: Timeout para requisições
            virustotal_api_key: API key do VirusTotal (opcional)
            google_safe_browsing_key: API key do Google Safe Browsing (opcional)
        """
        self.timeout = timeout
        self.virustotal_api_key = virustotal_api_key
        self.google_safe_browsing_key = google_safe_browsing_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_virustotal(self, domain: str) -> Dict:
        """
        Verifica domínio no VirusTotal

        Args:
            domain: Nome do domínio

        Returns:
            Dict com resultado da análise
        """
        result = {
            'scanned': False,
            'malicious_count': 0,
            'suspicious_count': 0,
            'clean_count': 0,
            'total_scanners': 0,
            'reputation': 0,
            'last_analysis_date': None,
            'categories': [],
            'is_safe': True
        }

        if not self.virustotal_api_key:
            logger.debug("VirusTotal API key não configurada")
            return result

        try:
            domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

            # VirusTotal API v3
            url = f"https://www.virustotal.com/api/v3/domains/{domain_clean}"
            headers = {'x-apikey': self.virustotal_api_key}

            response = self.session.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if 'data' in data and 'attributes' in data['data']:
                    attrs = data['data']['attributes']

                    # Estatísticas de análise
                    if 'last_analysis_stats' in attrs:
                        stats = attrs['last_analysis_stats']
                        result['malicious_count'] = stats.get('malicious', 0)
                        result['suspicious_count'] = stats.get('suspicious', 0)
                        result['clean_count'] = stats.get('harmless', 0) + stats.get('undetected', 0)
                        result['total_scanners'] = sum(stats.values())
                        result['scanned'] = True

                        # Considera não seguro se houver detecções maliciosas
                        if result['malicious_count'] > 0 or result['suspicious_count'] > 2:
                            result['is_safe'] = False

                    # Reputação
                    if 'reputation' in attrs:
                        result['reputation'] = attrs['reputation']

                    # Data da última análise
                    if 'last_analysis_date' in attrs:
                        result['last_analysis_date'] = attrs['last_analysis_date']

                    # Categorias
                    if 'categories' in attrs:
                        result['categories'] = list(attrs['categories'].values())

                    logger.debug(f"VirusTotal: {domain} - {result['malicious_count']} malicious, {result['suspicious_count']} suspicious")

        except Exception as e:
            logger.debug(f"Erro ao verificar VirusTotal para {domain}: {e}")

        return result

    def check_google_safe_browsing(self, domain: str) -> Dict:
        """
        Verifica domínio no Google Safe Browsing

        Args:
            domain: Nome do domínio

        Returns:
            Dict com resultado da verificação
        """
        result = {
            'scanned': False,
            'is_safe': True,
            'threats': [],
            'threat_types': []
        }

        if not self.google_safe_browsing_key:
            logger.debug("Google Safe Browsing API key não configurada")
            return result

        try:
            domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
            url_to_check = f"http://{domain_clean}/"

            # Google Safe Browsing API v4
            api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.google_safe_browsing_key}"

            payload = {
                "client": {
                    "clientId": "domain-manager-pro",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE",
                        "SOCIAL_ENGINEERING",
                        "UNWANTED_SOFTWARE",
                        "POTENTIALLY_HARMFUL_APPLICATION"
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [
                        {"url": url_to_check}
                    ]
                }
            }

            response = self.session.post(api_url, json=payload, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                result['scanned'] = True

                # Se retornar matches, não é seguro
                if 'matches' in data and data['matches']:
                    result['is_safe'] = False
                    for match in data['matches']:
                        threat_type = match.get('threatType', 'UNKNOWN')
                        result['threats'].append(match)
                        result['threat_types'].append(threat_type)

                    logger.warning(f"Google Safe Browsing: {domain} contém ameaças: {result['threat_types']}")
                else:
                    logger.debug(f"Google Safe Browsing: {domain} é seguro")

        except Exception as e:
            logger.debug(f"Erro ao verificar Google Safe Browsing para {domain}: {e}")

        return result

    def check_public_blacklists(self, ip_address: str) -> Dict:
        """
        Verifica IP em blacklists públicas comuns (DNSBL)

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com status de blacklists
        """
        result = {
            'checked': False,
            'blacklisted': False,
            'blacklists_found': [],
            'total_checked': 0,
            'total_blacklisted': 0
        }

        # Lista de DNSBLs comuns
        blacklists = [
            'zen.spamhaus.org',
            'bl.spamcop.net',
            'b.barracudacentral.org',
            'dnsbl.sorbs.net',
            'psbl.surriel.com',
            'ix.dnsbl.manitu.net'
        ]

        if not ip_address:
            return result

        try:
            import socket

            # Inverte o IP (1.2.3.4 vira 4.3.2.1)
            reversed_ip = '.'.join(reversed(ip_address.split('.')))

            result['checked'] = True
            result['total_checked'] = len(blacklists)

            for bl in blacklists:
                try:
                    query = f"{reversed_ip}.{bl}"
                    socket.gethostbyname(query)

                    # Se chegou aqui, está na blacklist
                    result['blacklisted'] = True
                    result['blacklists_found'].append(bl)
                    result['total_blacklisted'] += 1
                    logger.warning(f"IP {ip_address} encontrado em blacklist: {bl}")

                except socket.gaierror:
                    # Não está na blacklist (normal)
                    pass
                except Exception as e:
                    logger.debug(f"Erro ao verificar blacklist {bl}: {e}")

        except Exception as e:
            logger.debug(f"Erro ao verificar blacklists para {ip_address}: {e}")

        return result

    def check_domain_reputation(self, domain: str) -> Dict:
        """
        Verifica reputação geral do domínio usando múltiplas fontes

        Args:
            domain: Nome do domínio

        Returns:
            Dict com score de reputação consolidado
        """
        result = {
            'reputation_score': 0,  # -100 (muito ruim) a 100 (muito bom)
            'is_safe': True,
            'issues': [],
            'sources_checked': []
        }

        domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        score = 0

        # VirusTotal
        if self.virustotal_api_key:
            vt_result = self.check_virustotal(domain_clean)
            result['sources_checked'].append('virustotal')

            if vt_result['scanned']:
                # Penaliza por detecções maliciosas
                score -= vt_result['malicious_count'] * 20
                score -= vt_result['suspicious_count'] * 10

                # Bonifica por scanners que marcaram como limpo
                if vt_result['total_scanners'] > 0:
                    clean_ratio = vt_result['clean_count'] / vt_result['total_scanners']
                    score += clean_ratio * 30

                if vt_result['malicious_count'] > 0:
                    result['issues'].append(f"{vt_result['malicious_count']} scanners detectaram como malicioso")
                    result['is_safe'] = False

        # Google Safe Browsing
        if self.google_safe_browsing_key:
            gsb_result = self.check_google_safe_browsing(domain_clean)
            result['sources_checked'].append('google_safe_browsing')

            if gsb_result['scanned']:
                if not gsb_result['is_safe']:
                    score -= 50
                    result['issues'].append(f"Google Safe Browsing: {', '.join(gsb_result['threat_types'])}")
                    result['is_safe'] = False
                else:
                    score += 20

        # Normaliza score para -100 a 100
        result['reputation_score'] = max(-100, min(100, score))

        return result

    def check_ssl_blacklists(self, ssl_fingerprint: str) -> Dict:
        """
        Verifica se certificado SSL está em blacklists

        Args:
            ssl_fingerprint: Fingerprint do certificado SSL

        Returns:
            Dict com status
        """
        # Placeholder - pode ser expandido com serviços específicos
        result = {
            'blacklisted': False,
            'sources_checked': []
        }

        # TODO: Implementar verificação em bases de certificados revogados
        # Exemplo: OCSP, CRL, etc.

        return result
