"""
Coletor de informações de geolocalização por IP
"""
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GeolocationCollector:
    """Coleta dados de geolocalização a partir de endereços IP"""

    def __init__(self, timeout=10):
        """
        Inicializa o coletor de geolocalização

        Args:
            timeout: Timeout para requisições
        """
        self.timeout = timeout
        self.session = requests.Session()

    def get_ip_geolocation(self, ip_address: str) -> Dict:
        """
        Obtém dados de geolocalização de um IP usando múltiplas APIs gratuitas

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com dados de geolocalização
        """
        result = {
            'ip': ip_address,
            'country': None,
            'country_code': None,
            'region': None,
            'city': None,
            'latitude': None,
            'longitude': None,
            'timezone': None,
            'asn': None,
            'organization': None,
            'isp': None
        }

        if not ip_address:
            return result

        # Tenta múltiplas APIs em ordem de preferência
        apis = [
            self._get_from_ipapi,
            self._get_from_ipwhois,
            self._get_from_ipinfo
        ]

        for api_func in apis:
            try:
                data = api_func(ip_address)
                if data and data.get('country'):
                    # Mescla resultados (prioriza dados não-None)
                    for key in result.keys():
                        if data.get(key) is not None:
                            result[key] = data[key]

                    logger.debug(f"Geolocalização obtida para {ip_address}: {result['city']}, {result['country']}")
                    return result
            except Exception as e:
                logger.debug(f"Erro em {api_func.__name__} para {ip_address}: {e}")
                continue

        logger.debug(f"Não foi possível obter geolocalização para {ip_address}")
        return result

    def _get_from_ipapi(self, ip_address: str) -> Optional[Dict]:
        """
        Obtém dados do ip-api.com (gratuito, 45 req/min)

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com dados ou None
        """
        try:
            url = f"http://ip-api.com/json/{ip_address}"
            params = {
                'fields': 'status,country,countryCode,region,city,lat,lon,timezone,isp,org,as'
            }

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    result = {
                        'ip': ip_address,
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'region': data.get('region'),
                        'city': data.get('city'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'asn': data.get('as'),
                        'organization': data.get('org'),
                        'isp': data.get('isp')
                    }
                    return result

        except Exception as e:
            logger.debug(f"Erro em ip-api.com: {e}")

        return None

    def _get_from_ipwhois(self, ip_address: str) -> Optional[Dict]:
        """
        Obtém dados do ipwhois.app (gratuito, 10k req/mês)

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com dados ou None
        """
        try:
            url = f"https://ipwhois.app/json/{ip_address}"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    result = {
                        'ip': ip_address,
                        'country': data.get('country'),
                        'country_code': data.get('country_code'),
                        'region': data.get('region'),
                        'city': data.get('city'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'timezone': data.get('timezone'),
                        'asn': data.get('asn'),
                        'organization': data.get('org'),
                        'isp': data.get('isp')
                    }
                    return result

        except Exception as e:
            logger.debug(f"Erro em ipwhois.app: {e}")

        return None

    def _get_from_ipinfo(self, ip_address: str) -> Optional[Dict]:
        """
        Obtém dados do ipinfo.io (gratuito, 50k req/mês sem API key)

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com dados ou None
        """
        try:
            url = f"https://ipinfo.io/{ip_address}/json"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # ipinfo.io retorna loc como "latitude,longitude"
                lat, lon = None, None
                if data.get('loc'):
                    try:
                        lat_str, lon_str = data['loc'].split(',')
                        lat = float(lat_str)
                        lon = float(lon_str)
                    except:
                        pass

                result = {
                    'ip': ip_address,
                    'country': data.get('country'),
                    'country_code': data.get('country'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'latitude': lat,
                    'longitude': lon,
                    'timezone': data.get('timezone'),
                    'asn': data.get('asn'),
                    'organization': data.get('org'),
                    'isp': None
                }
                return result

        except Exception as e:
            logger.debug(f"Erro em ipinfo.io: {e}")

        return None

    def get_distance_between_ips(self, ip1: str, ip2: str) -> Optional[float]:
        """
        Calcula distância aproximada entre dois IPs em km

        Args:
            ip1: Primeiro IP
            ip2: Segundo IP

        Returns:
            Distância em km ou None
        """
        try:
            geo1 = self.get_ip_geolocation(ip1)
            geo2 = self.get_ip_geolocation(ip2)

            if not (geo1.get('latitude') and geo2.get('latitude')):
                return None

            # Fórmula de Haversine para calcular distância
            from math import radians, cos, sin, asin, sqrt

            lat1 = radians(geo1['latitude'])
            lon1 = radians(geo1['longitude'])
            lat2 = radians(geo2['latitude'])
            lon2 = radians(geo2['longitude'])

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))

            # Raio da Terra em km
            r = 6371

            return round(c * r, 2)

        except Exception as e:
            logger.debug(f"Erro ao calcular distância: {e}")
            return None

    def is_ip_in_country(self, ip_address: str, country_code: str) -> bool:
        """
        Verifica se um IP pertence a um país específico

        Args:
            ip_address: Endereço IP
            country_code: Código do país (ex: 'US', 'BR')

        Returns:
            True se o IP pertence ao país
        """
        try:
            geo = self.get_ip_geolocation(ip_address)
            return geo.get('country_code', '').upper() == country_code.upper()
        except:
            return False

    def get_asn_info(self, ip_address: str) -> Dict:
        """
        Obtém informações detalhadas sobre o ASN (Autonomous System Number)

        Args:
            ip_address: Endereço IP

        Returns:
            Dict com informações do ASN
        """
        result = {
            'asn': None,
            'asn_name': None,
            'asn_country': None,
            'asn_registry': None
        }

        try:
            # Usa ipwhois.app que tem bons dados de ASN
            url = f"https://ipwhois.app/json/{ip_address}"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                result['asn'] = data.get('asn')
                result['asn_name'] = data.get('org')
                result['asn_country'] = data.get('country_code')

        except Exception as e:
            logger.debug(f"Erro ao obter ASN info: {e}")

        return result
