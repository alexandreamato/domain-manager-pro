"""
Coletor de métricas de performance e Core Web Vitals
"""
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceCollector:
    """Coleta métricas de performance usando Google PageSpeed Insights"""

    def __init__(self, timeout=30, pagespeed_api_key=None):
        """
        Inicializa o coletor de performance

        Args:
            timeout: Timeout para requisições (PageSpeed pode ser lento)
            pagespeed_api_key: API key do Google PageSpeed Insights (opcional)
        """
        self.timeout = timeout
        self.pagespeed_api_key = pagespeed_api_key
        self.session = requests.Session()

    def get_pagespeed_metrics(self, domain: str, strategy: str = 'mobile') -> Dict:
        """
        Obtém métricas do Google PageSpeed Insights v5

        Args:
            domain: Nome do domínio
            strategy: 'mobile' ou 'desktop'

        Returns:
            Dict com métricas de performance
        """
        result = {
            'performance_score': None,
            'fcp': None,  # First Contentful Paint
            'lcp': None,  # Largest Contentful Paint
            'fid': None,  # First Input Delay
            'cls': None,  # Cumulative Layout Shift
            'ttfb': None,  # Time to First Byte
            'tti': None,  # Time to Interactive
            'tbt': None,  # Total Blocking Time
            'speed_index': None,
            'strategy': strategy
        }

        try:
            # Normaliza domínio
            if not domain.startswith(('http://', 'https://')):
                domain = f'https://{domain}'

            # Remove www se tiver
            domain_clean = domain.replace('www.', '')

            # Google PageSpeed Insights API v5
            url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'

            params = {
                'url': domain_clean,
                'strategy': strategy,
                'category': 'performance'
            }

            # Adiciona API key se disponível
            if self.pagespeed_api_key:
                params['key'] = self.pagespeed_api_key

            logger.debug(f"Consultando PageSpeed Insights para {domain_clean}...")
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # Performance Score (0-100)
                if 'lighthouseResult' in data and 'categories' in data['lighthouseResult']:
                    perf_category = data['lighthouseResult']['categories'].get('performance', {})
                    score = perf_category.get('score')
                    if score is not None:
                        result['performance_score'] = int(score * 100)

                # Core Web Vitals e outras métricas
                if 'lighthouseResult' in data and 'audits' in data['lighthouseResult']:
                    audits = data['lighthouseResult']['audits']

                    # First Contentful Paint
                    if 'first-contentful-paint' in audits:
                        fcp_value = audits['first-contentful-paint'].get('numericValue')
                        if fcp_value:
                            result['fcp'] = int(fcp_value)

                    # Largest Contentful Paint
                    if 'largest-contentful-paint' in audits:
                        lcp_value = audits['largest-contentful-paint'].get('numericValue')
                        if lcp_value:
                            result['lcp'] = int(lcp_value)

                    # Cumulative Layout Shift
                    if 'cumulative-layout-shift' in audits:
                        cls_value = audits['cumulative-layout-shift'].get('numericValue')
                        if cls_value is not None:
                            result['cls'] = round(cls_value, 3)

                    # Time to First Byte
                    if 'server-response-time' in audits:
                        ttfb_value = audits['server-response-time'].get('numericValue')
                        if ttfb_value:
                            result['ttfb'] = int(ttfb_value)

                    # Time to Interactive
                    if 'interactive' in audits:
                        tti_value = audits['interactive'].get('numericValue')
                        if tti_value:
                            result['tti'] = int(tti_value)

                    # Total Blocking Time
                    if 'total-blocking-time' in audits:
                        tbt_value = audits['total-blocking-time'].get('numericValue')
                        if tbt_value:
                            result['tbt'] = int(tbt_value)

                    # Speed Index
                    if 'speed-index' in audits:
                        si_value = audits['speed-index'].get('numericValue')
                        if si_value:
                            result['speed_index'] = int(si_value)

                # Tenta pegar FID dos dados de campo (loading experience)
                if 'loadingExperience' in data and 'metrics' in data['loadingExperience']:
                    metrics = data['loadingExperience']['metrics']

                    # First Input Delay
                    if 'FIRST_INPUT_DELAY_MS' in metrics:
                        fid_percentile = metrics['FIRST_INPUT_DELAY_MS'].get('percentile')
                        if fid_percentile:
                            result['fid'] = int(fid_percentile)

                logger.info(f"PageSpeed Score para {domain_clean}: {result['performance_score']}")

            elif response.status_code == 429:
                logger.warning(f"Rate limit atingido no PageSpeed Insights")
            else:
                logger.warning(f"PageSpeed API retornou status {response.status_code}")

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout ao consultar PageSpeed para {domain}")
        except Exception as e:
            logger.debug(f"Erro ao obter PageSpeed metrics de {domain}: {e}")

        return result

    def get_performance_summary(self, domain: str) -> Dict:
        """
        Obtém resumo de performance (mobile e desktop se API key disponível)

        Args:
            domain: Nome do domínio

        Returns:
            Dict com métricas mobile e desktop
        """
        result = {
            'mobile': None,
            'desktop': None
        }

        # Sempre tenta mobile
        try:
            result['mobile'] = self.get_pagespeed_metrics(domain, strategy='mobile')
        except Exception as e:
            logger.debug(f"Erro ao obter performance mobile: {e}")

        # Desktop apenas se tiver API key (para evitar rate limit)
        if self.pagespeed_api_key:
            try:
                import time
                time.sleep(2)  # Delay entre requests
                result['desktop'] = self.get_pagespeed_metrics(domain, strategy='desktop')
            except Exception as e:
                logger.debug(f"Erro ao obter performance desktop: {e}")

        return result

    def check_core_web_vitals(self, metrics: Dict) -> Dict:
        """
        Verifica se as Core Web Vitals estão dentro dos padrões recomendados

        Args:
            metrics: Dict com métricas (resultado de get_pagespeed_metrics)

        Returns:
            Dict com status de cada métrica (good/needs_improvement/poor)
        """
        result = {
            'lcp_status': None,  # Good: <= 2.5s, Poor: > 4.0s
            'fid_status': None,  # Good: <= 100ms, Poor: > 300ms
            'cls_status': None,  # Good: <= 0.1, Poor: > 0.25
            'overall_status': None
        }

        statuses = []

        # LCP (Largest Contentful Paint)
        lcp = metrics.get('lcp')
        if lcp is not None:
            lcp_seconds = lcp / 1000  # Converte ms para segundos
            if lcp_seconds <= 2.5:
                result['lcp_status'] = 'good'
                statuses.append('good')
            elif lcp_seconds <= 4.0:
                result['lcp_status'] = 'needs_improvement'
                statuses.append('needs_improvement')
            else:
                result['lcp_status'] = 'poor'
                statuses.append('poor')

        # FID (First Input Delay)
        fid = metrics.get('fid')
        if fid is not None:
            if fid <= 100:
                result['fid_status'] = 'good'
                statuses.append('good')
            elif fid <= 300:
                result['fid_status'] = 'needs_improvement'
                statuses.append('needs_improvement')
            else:
                result['fid_status'] = 'poor'
                statuses.append('poor')

        # CLS (Cumulative Layout Shift)
        cls = metrics.get('cls')
        if cls is not None:
            if cls <= 0.1:
                result['cls_status'] = 'good'
                statuses.append('good')
            elif cls <= 0.25:
                result['cls_status'] = 'needs_improvement'
                statuses.append('needs_improvement')
            else:
                result['cls_status'] = 'poor'
                statuses.append('poor')

        # Status geral
        if statuses:
            if all(s == 'good' for s in statuses):
                result['overall_status'] = 'good'
            elif any(s == 'poor' for s in statuses):
                result['overall_status'] = 'poor'
            else:
                result['overall_status'] = 'needs_improvement'

        return result
