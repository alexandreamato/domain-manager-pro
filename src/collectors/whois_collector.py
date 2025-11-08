"""
Coletor de dados WHOIS/RDAP
"""
import whois
import socket
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WhoisCollector:
    """Coleta dados WHOIS/RDAP de domínios"""

    def __init__(self, timeout=10):
        """
        Inicializa o coletor WHOIS

        Args:
            timeout: Timeout para consultas
        """
        self.timeout = timeout
        socket.setdefaulttimeout(timeout)

    def get_whois_data(self, domain: str) -> Dict:
        """
        Obtém dados WHOIS completos de um domínio

        Args:
            domain: Nome do domínio

        Returns:
            Dict com dados WHOIS
        """
        result = {
            'registrar': None,
            'creation_date': None,
            'expiration_date': None,
            'updated_date': None,
            'status': None,
            'name_servers': None,
            'registrant_name': None,
            'registrant_org': None,
            'registrant_email': None,
            'admin_email': None,
            'tech_email': None,
            'days_until_expiration': None,
            'domain_age_days': None
        }

        try:
            # Remove protocolo e www
            domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

            # Consulta WHOIS
            w = whois.whois(domain_clean)

            # Registrar
            if hasattr(w, 'registrar') and w.registrar:
                result['registrar'] = str(w.registrar)

            # Datas
            creation_date = self._normalize_date(w.creation_date)
            expiration_date = self._normalize_date(w.expiration_date)
            updated_date = self._normalize_date(w.updated_date)

            result['creation_date'] = creation_date.isoformat() if creation_date else None
            result['expiration_date'] = expiration_date.isoformat() if expiration_date else None
            result['updated_date'] = updated_date.isoformat() if updated_date else None

            # Calcula dias até expiração
            if expiration_date:
                delta = expiration_date - datetime.now()
                result['days_until_expiration'] = delta.days

            # Calcula idade do domínio
            if creation_date:
                delta = datetime.now() - creation_date
                result['domain_age_days'] = delta.days

            # Status
            if hasattr(w, 'status') and w.status:
                if isinstance(w.status, list):
                    result['status'] = ', '.join([str(s) for s in w.status])
                else:
                    result['status'] = str(w.status)

            # Name servers
            if hasattr(w, 'name_servers') and w.name_servers:
                if isinstance(w.name_servers, list):
                    result['name_servers'] = ', '.join([str(ns).lower() for ns in w.name_servers])
                else:
                    result['name_servers'] = str(w.name_servers).lower()

            # Informações de contato
            if hasattr(w, 'name') and w.name:
                result['registrant_name'] = str(w.name)

            if hasattr(w, 'org') and w.org:
                result['registrant_org'] = str(w.org)

            # Emails
            if hasattr(w, 'emails') and w.emails:
                if isinstance(w.emails, list):
                    if len(w.emails) > 0:
                        result['registrant_email'] = w.emails[0]
                    if len(w.emails) > 1:
                        result['admin_email'] = w.emails[1]
                    if len(w.emails) > 2:
                        result['tech_email'] = w.emails[2]
                else:
                    result['registrant_email'] = str(w.emails)

            logger.debug(f"WHOIS coletado para {domain}")

        except Exception as e:
            logger.debug(f"Erro ao coletar WHOIS de {domain}: {e}")

        return result

    def _normalize_date(self, date_value):
        """Normaliza datas que podem vir como lista ou datetime"""
        if not date_value:
            return None

        if isinstance(date_value, list):
            # Pega a primeira data da lista
            date_value = date_value[0] if date_value else None

        if isinstance(date_value, datetime):
            return date_value

        return None

    def get_nameservers(self, domain: str) -> list:
        """
        Obtém nameservers de um domínio via DNS lookup

        Args:
            domain: Nome do domínio

        Returns:
            Lista de nameservers
        """
        try:
            import dns.resolver

            domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

            answers = dns.resolver.resolve(domain_clean, 'NS', lifetime=self.timeout)
            nameservers = [str(rdata.target).rstrip('.') for rdata in answers]

            return nameservers

        except Exception as e:
            logger.debug(f"Erro ao obter nameservers de {domain}: {e}")
            return []

    def check_expiration_alert(self, expiration_date_str: str, warning_days: int = 30) -> Dict:
        """
        Verifica se um domínio está próximo de expirar

        Args:
            expiration_date_str: Data de expiração em formato ISO
            warning_days: Dias de antecedência para alertar

        Returns:
            Dict com status do alerta
        """
        result = {
            'is_expiring_soon': False,
            'days_remaining': None,
            'severity': None  # 'critical', 'warning', 'ok'
        }

        try:
            if not expiration_date_str:
                return result

            expiration_date = datetime.fromisoformat(expiration_date_str)
            delta = expiration_date - datetime.now()
            days_remaining = delta.days

            result['days_remaining'] = days_remaining

            if days_remaining < 0:
                result['is_expiring_soon'] = True
                result['severity'] = 'expired'
            elif days_remaining <= 7:
                result['is_expiring_soon'] = True
                result['severity'] = 'critical'
            elif days_remaining <= warning_days:
                result['is_expiring_soon'] = True
                result['severity'] = 'warning'
            else:
                result['severity'] = 'ok'

        except Exception as e:
            logger.debug(f"Erro ao verificar expiração: {e}")

        return result
