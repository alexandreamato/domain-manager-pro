"""
Coletor de registros DNS e autenticação de email
"""
import dns.resolver
import dns.exception
import socket
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DNSCollector:
    """Coleta registros DNS e verifica autenticação de email"""

    def __init__(self, timeout=10):
        """
        Inicializa o coletor DNS

        Args:
            timeout: Timeout para consultas DNS
        """
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout

    def get_dns_records(self, domain: str) -> Dict:
        """
        Obtém todos os registros DNS relevantes de um domínio

        Args:
            domain: Nome do domínio

        Returns:
            Dict com registros DNS
        """
        domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

        result = {
            'a_records': [],
            'aaaa_records': [],
            'mx_records': [],
            'txt_records': [],
            'cname_records': [],
            'ns_records': [],
            'srv_records': [],
            'caa_records': []
        }

        # A records (IPv4)
        result['a_records'] = self._query_dns(domain_clean, 'A')

        # AAAA records (IPv6)
        result['aaaa_records'] = self._query_dns(domain_clean, 'AAAA')

        # MX records (Mail Exchange)
        mx_records = self._query_dns(domain_clean, 'MX')
        result['mx_records'] = [f"{r.preference} {r.exchange}" for r in mx_records] if mx_records else []

        # TXT records
        txt_records = self._query_dns(domain_clean, 'TXT')
        result['txt_records'] = [str(r).strip('"') for r in txt_records] if txt_records else []

        # CNAME records
        result['cname_records'] = self._query_dns(f'www.{domain_clean}', 'CNAME')

        # NS records
        result['ns_records'] = self._query_dns(domain_clean, 'NS')

        # CAA records (Certificate Authority Authorization)
        caa_records = self._query_dns(domain_clean, 'CAA')
        result['caa_records'] = [str(r) for r in caa_records] if caa_records else []

        return result

    def _query_dns(self, domain: str, record_type: str) -> List:
        """
        Executa query DNS

        Args:
            domain: Nome do domínio
            record_type: Tipo de registro (A, MX, TXT, etc)

        Returns:
            Lista de registros ou lista vazia
        """
        try:
            answers = self.resolver.resolve(domain, record_type, lifetime=self.timeout)

            # Para registros que precisam de formatação especial
            if record_type == 'TXT':
                return [str(rdata) for rdata in answers]
            elif record_type == 'MX':
                return [rdata for rdata in answers]
            else:
                return [str(rdata).rstrip('.') for rdata in answers]

        except dns.resolver.NoAnswer:
            logger.debug(f"Nenhum registro {record_type} para {domain}")
            return []
        except dns.resolver.NXDOMAIN:
            logger.debug(f"Domínio não existe: {domain}")
            return []
        except dns.exception.Timeout:
            logger.debug(f"Timeout na consulta {record_type} para {domain}")
            return []
        except Exception as e:
            logger.debug(f"Erro ao consultar {record_type} para {domain}: {e}")
            return []

    def check_email_authentication(self, domain: str) -> Dict:
        """
        Verifica configurações de autenticação de email (SPF, DKIM, DMARC)

        Args:
            domain: Nome do domínio

        Returns:
            Dict com status de SPF, DKIM e DMARC
        """
        domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

        result = {
            'spf': {
                'configured': False,
                'record': None,
                'valid': False,
                'mechanisms': []
            },
            'dmarc': {
                'configured': False,
                'record': None,
                'policy': None,
                'valid': False
            },
            'dkim': {
                'configured': False,
                'selectors_found': []
            }
        }

        # Verifica SPF
        spf_data = self._check_spf(domain_clean)
        result['spf'] = spf_data

        # Verifica DMARC
        dmarc_data = self._check_dmarc(domain_clean)
        result['dmarc'] = dmarc_data

        # Verifica DKIM (tenta seletores comuns)
        dkim_data = self._check_dkim(domain_clean)
        result['dkim'] = dkim_data

        return result

    def _check_spf(self, domain: str) -> Dict:
        """Verifica registro SPF"""
        result = {
            'configured': False,
            'record': None,
            'valid': False,
            'mechanisms': []
        }

        try:
            txt_records = self._query_dns(domain, 'TXT')

            for record in txt_records:
                record_str = str(record).strip('"')
                if record_str.startswith('v=spf1'):
                    result['configured'] = True
                    result['record'] = record_str
                    result['valid'] = True

                    # Extrai mecanismos SPF
                    mechanisms = record_str.split()[1:]  # Pula 'v=spf1'
                    result['mechanisms'] = mechanisms

                    logger.debug(f"SPF encontrado para {domain}: {record_str}")
                    break

        except Exception as e:
            logger.debug(f"Erro ao verificar SPF de {domain}: {e}")

        return result

    def _check_dmarc(self, domain: str) -> Dict:
        """Verifica registro DMARC"""
        result = {
            'configured': False,
            'record': None,
            'policy': None,
            'valid': False
        }

        try:
            # DMARC fica em _dmarc.domain.com
            dmarc_domain = f'_dmarc.{domain}'
            txt_records = self._query_dns(dmarc_domain, 'TXT')

            for record in txt_records:
                record_str = str(record).strip('"')
                if record_str.startswith('v=DMARC1'):
                    result['configured'] = True
                    result['record'] = record_str
                    result['valid'] = True

                    # Extrai política
                    policy_match = re.search(r'p=(\w+)', record_str)
                    if policy_match:
                        result['policy'] = policy_match.group(1)

                    logger.debug(f"DMARC encontrado para {domain}: {record_str}")
                    break

        except Exception as e:
            logger.debug(f"Erro ao verificar DMARC de {domain}: {e}")

        return result

    def _check_dkim(self, domain: str) -> Dict:
        """Verifica DKIM tentando seletores comuns"""
        result = {
            'configured': False,
            'selectors_found': []
        }

        # Seletores DKIM comuns
        common_selectors = [
            'default', 'google', 'k1', 'selector1', 'selector2',
            'dkim', 'mail', 'email', 's1', 's2', 'mx'
        ]

        try:
            for selector in common_selectors:
                dkim_domain = f'{selector}._domainkey.{domain}'
                txt_records = self._query_dns(dkim_domain, 'TXT')

                for record in txt_records:
                    record_str = str(record).strip('"')
                    if 'v=DKIM1' in record_str or 'k=rsa' in record_str:
                        result['configured'] = True
                        result['selectors_found'].append({
                            'selector': selector,
                            'record': record_str
                        })
                        logger.debug(f"DKIM encontrado para {domain} (seletor: {selector})")

        except Exception as e:
            logger.debug(f"Erro ao verificar DKIM de {domain}: {e}")

        return result

    def get_reverse_dns(self, ip_address: str) -> Optional[str]:
        """
        Obtém reverse DNS (PTR) de um IP

        Args:
            ip_address: Endereço IP

        Returns:
            Hostname ou None
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except Exception as e:
            logger.debug(f"Erro ao obter reverse DNS de {ip_address}: {e}")
            return None

    def check_dns_consistency(self, domain: str, ip_address: str) -> Dict:
        """
        Verifica consistência DNS (A record vs reverse DNS)

        Args:
            domain: Nome do domínio
            ip_address: IP do domínio

        Returns:
            Dict com status de consistência
        """
        result = {
            'consistent': False,
            'forward_lookup': None,
            'reverse_lookup': None,
            'matches': False
        }

        try:
            domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

            # Forward lookup
            a_records = self._query_dns(domain_clean, 'A')
            result['forward_lookup'] = a_records

            # Reverse lookup
            reverse = self.get_reverse_dns(ip_address)
            result['reverse_lookup'] = reverse

            # Verifica se o reverse aponta de volta para o domínio
            if reverse:
                reverse_a = self._query_dns(reverse, 'A')
                if ip_address in reverse_a:
                    result['consistent'] = True
                    result['matches'] = True

        except Exception as e:
            logger.debug(f"Erro ao verificar consistência DNS: {e}")

        return result
