"""
Coletor de informações SSL/TLS
"""
import ssl
import socket
import logging
from datetime import datetime
from typing import Dict, Optional
import OpenSSL

logger = logging.getLogger(__name__)


class SSLCollector:
    """Coleta informações de certificados SSL/TLS"""

    def __init__(self, timeout=10):
        """
        Inicializa o coletor SSL

        Args:
            timeout: Timeout para conexões
        """
        self.timeout = timeout

    def get_ssl_info(self, domain: str, port: int = 443) -> Dict:
        """
        Obtém informações completas do certificado SSL

        Args:
            domain: Nome do domínio
            port: Porta SSL (padrão 443)

        Returns:
            Dict com informações SSL
        """
        domain_clean = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

        result = {
            'has_ssl': False,
            'issuer': None,
            'subject': None,
            'valid_from': None,
            'valid_until': None,
            'days_until_expiration': None,
            'is_valid': False,
            'is_expired': False,
            'is_self_signed': False,
            'serial_number': None,
            'version': None,
            'signature_algorithm': None,
            'san_domains': [],
            'chain_length': 0,
            'protocol_version': None,
            'cipher_suite': None
        }

        try:
            # Cria contexto SSL
            context = ssl.create_default_context()

            # Conecta e obtém certificado
            with socket.create_connection((domain_clean, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain_clean) as secure_sock:
                    cert = secure_sock.getpeercert()

                    result['has_ssl'] = True
                    result['protocol_version'] = secure_sock.version()
                    result['cipher_suite'] = secure_sock.cipher()[0] if secure_sock.cipher() else None

                    # Informações básicas
                    if 'issuer' in cert:
                        result['issuer'] = self._parse_cert_name(cert['issuer'])

                    if 'subject' in cert:
                        result['subject'] = self._parse_cert_name(cert['subject'])

                    # Datas de validade
                    if 'notBefore' in cert:
                        valid_from = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                        result['valid_from'] = valid_from.isoformat()

                    if 'notAfter' in cert:
                        valid_until = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        result['valid_until'] = valid_until.isoformat()

                        # Calcula dias até expiração
                        delta = valid_until - datetime.now()
                        result['days_until_expiration'] = delta.days

                        # Verifica se expirou
                        result['is_expired'] = delta.days < 0
                        result['is_valid'] = delta.days > 0

                    # Serial number
                    if 'serialNumber' in cert:
                        result['serial_number'] = cert['serialNumber']

                    # Version
                    if 'version' in cert:
                        result['version'] = cert['version']

                    # Subject Alternative Names (SANs)
                    if 'subjectAltName' in cert:
                        result['san_domains'] = [name[1] for name in cert['subjectAltName'] if name[0] == 'DNS']

            # Obtém informações detalhadas com PyOpenSSL
            try:
                detailed_info = self._get_detailed_ssl_info(domain_clean, port)
                result.update(detailed_info)
            except Exception as e:
                logger.debug(f"Erro ao obter informações detalhadas SSL: {e}")

            logger.debug(f"SSL coletado para {domain}")

        except ssl.SSLError as e:
            logger.debug(f"Erro SSL para {domain}: {e}")
            result['has_ssl'] = False
        except socket.timeout:
            logger.debug(f"Timeout SSL para {domain}")
        except Exception as e:
            logger.debug(f"Erro ao coletar SSL de {domain}: {e}")

        return result

    def _parse_cert_name(self, name_tuple) -> str:
        """Parse o formato de nome do certificado"""
        try:
            if isinstance(name_tuple, tuple):
                parts = []
                for item in name_tuple:
                    for pair in item:
                        parts.append(f"{pair[0]}={pair[1]}")
                return ', '.join(parts)
            return str(name_tuple)
        except:
            return str(name_tuple)

    def _get_detailed_ssl_info(self, domain: str, port: int = 443) -> Dict:
        """Obtém informações detalhadas usando PyOpenSSL"""
        result = {}

        try:
            # Conecta e obtém certificado
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((domain, port))

            context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
            connection = OpenSSL.SSL.Connection(context, sock)
            connection.set_tlsext_host_name(domain.encode())
            connection.set_connect_state()
            connection.do_handshake()

            # Obtém certificado
            cert = connection.get_peer_certificate()

            # Algoritmo de assinatura
            result['signature_algorithm'] = cert.get_signature_algorithm().decode('utf-8')

            # Verifica se é auto-assinado
            result['is_self_signed'] = cert.get_issuer() == cert.get_subject()

            # Obtém chain de certificados
            cert_chain = connection.get_peer_cert_chain()
            result['chain_length'] = len(cert_chain) if cert_chain else 0

            connection.close()
            sock.close()

        except Exception as e:
            logger.debug(f"Erro ao obter informações detalhadas SSL: {e}")

        return result

    def check_ssl_expiration_alert(self, valid_until_str: str, warning_days: int = 30) -> Dict:
        """
        Verifica se certificado SSL está próximo de expirar

        Args:
            valid_until_str: Data de expiração em formato ISO
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
            if not valid_until_str:
                return result

            valid_until = datetime.fromisoformat(valid_until_str)
            delta = valid_until - datetime.now()
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
            logger.debug(f"Erro ao verificar expiração SSL: {e}")

        return result

    def verify_ssl_chain(self, domain: str, port: int = 443) -> Dict:
        """
        Verifica se a cadeia SSL é válida

        Args:
            domain: Nome do domínio
            port: Porta SSL

        Returns:
            Dict com status da verificação
        """
        result = {
            'valid_chain': False,
            'error': None
        }

        try:
            context = ssl.create_default_context()

            with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as secure_sock:
                    # Se chegou aqui, a cadeia é válida
                    result['valid_chain'] = True

        except ssl.SSLError as e:
            result['error'] = str(e)
            logger.debug(f"Erro na cadeia SSL de {domain}: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.debug(f"Erro ao verificar cadeia SSL: {e}")

        return result
