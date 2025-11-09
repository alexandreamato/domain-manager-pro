"""
Detector de CMS usando múltiplas APIs e fallbacks
"""
import requests
import re
import logging
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


class CMSDetector:
    """Detecta CMS usando Wappalyzer, WhatCMS e fallbacks"""

    def __init__(self, timeout=10, wappalyzer_key=None, whatcms_key=None):
        """
        Inicializa o detector de CMS

        Args:
            timeout: Timeout para requisições
            wappalyzer_key: API key do Wappalyzer (opcional)
            whatcms_key: API key do WhatCMS (opcional)
        """
        self.timeout = timeout
        self.wappalyzer_key = wappalyzer_key
        self.whatcms_key = whatcms_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def detect_cms(self, domain, html_content=None):
        """
        Detecta o CMS de um domínio usando múltiplas estratégias

        Args:
            domain: Nome do domínio
            html_content: HTML já carregado (opcional, para evitar nova requisição)

        Returns:
            Dict com 'name' e 'version' do CMS
        """
        result = {
            'name': None,
            'version': None
        }

        # 1. Tenta Wappalyzer API (mais completo)
        if self.wappalyzer_key:
            wapp_result = self._detect_with_wappalyzer(domain)
            if wapp_result['name']:
                logger.info(f"CMS detectado via Wappalyzer: {wapp_result['name']}")
                return wapp_result

        # 2. Tenta WhatCMS API (fallback)
        if self.whatcms_key:
            whatcms_result = self._detect_with_whatcms(domain)
            if whatcms_result['name']:
                logger.info(f"CMS detectado via WhatCMS: {whatcms_result['name']}")
                return whatcms_result

        # 3. Fallback: análise de HTML (método atual)
        if html_content:
            fallback_result = self._detect_from_html(html_content)
            if fallback_result['name']:
                logger.info(f"CMS detectado via HTML: {fallback_result['name']}")
                return fallback_result

        logger.debug(f"CMS não detectado para {domain}")
        return result

    def _detect_with_wappalyzer(self, domain):
        """
        Detecta CMS usando Wappalyzer API

        Args:
            domain: Nome do domínio

        Returns:
            Dict com 'name' e 'version'
        """
        result = {'name': None, 'version': None}

        try:
            # Normaliza domínio
            if not domain.startswith(('http://', 'https://')):
                domain = f'https://{domain}'

            url = f"https://api.wappalyzer.com/lookup/v2/?url={quote(domain)}"
            headers = {'x-api-key': self.wappalyzer_key}

            response = self.session.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # Procura por CMS nas tecnologias detectadas
                if 'technologies' in data:
                    for tech in data['technologies']:
                        # Lista de categorias que indicam CMS
                        cms_categories = ['CMS', 'Blogs', 'Wiki', 'Ecommerce']

                        categories = tech.get('categories', [])
                        for cat in categories:
                            if cat.get('name') in cms_categories:
                                result['name'] = tech.get('name')
                                result['version'] = tech.get('version')
                                return result

                # Fallback: pega o primeiro da lista se não encontrou CMS específico
                if data.get('technologies') and not result['name']:
                    first_tech = data['technologies'][0]
                    result['name'] = first_tech.get('name')
                    result['version'] = first_tech.get('version')

        except Exception as e:
            logger.debug(f"Erro no Wappalyzer para {domain}: {e}")

        return result

    def _detect_with_whatcms(self, domain):
        """
        Detecta CMS usando WhatCMS API

        Args:
            domain: Nome do domínio

        Returns:
            Dict com 'name' e 'version'
        """
        result = {'name': None, 'version': None}

        try:
            # Normaliza domínio (WhatCMS não quer protocolo)
            domain_clean = domain.replace('http://', '').replace('https://', '').split('/')[0]

            # Endpoint principal (detect)
            url = f"https://whatcms.org/APIEndpoint/Detect?key={self.whatcms_key}&url={quote(domain_clean)}"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if data.get('result'):
                    result_data = data['result']
                    result['name'] = result_data.get('name')
                    result['version'] = result_data.get('version')

                    if result['name']:
                        return result

        except Exception as e:
            logger.debug(f"Erro no WhatCMS para {domain}: {e}")

        return result

    def _detect_from_html(self, html_content):
        """
        Detecta CMS analisando o HTML (fallback)

        Args:
            html_content: Conteúdo HTML da página

        Returns:
            Dict com 'name' e 'version'
        """
        result = {'name': None, 'version': None}

        if not html_content:
            return result

        try:
            # WordPress
            if 'wp-content' in html_content or 'wordpress' in html_content.lower():
                result['name'] = 'WordPress'

                # Tenta extrair versão
                version_match = re.search(
                    r'<meta name="generator" content="WordPress (\d+\.\d+(?:\.\d+)?)"',
                    html_content,
                    re.IGNORECASE
                )
                if version_match:
                    result['version'] = version_match.group(1)

                return result

            # Joomla
            if '/components/com_' in html_content or 'Joomla' in html_content:
                result['name'] = 'Joomla'

                version_match = re.search(
                    r'<meta name="generator" content="Joomla! - Open Source Content Management - Version (\d+\.\d+(?:\.\d+)?)"',
                    html_content,
                    re.IGNORECASE
                )
                if version_match:
                    result['version'] = version_match.group(1)

                return result

            # Drupal
            if 'Drupal' in html_content or '/sites/default/' in html_content:
                result['name'] = 'Drupal'

                version_match = re.search(
                    r'<meta name="Generator" content="Drupal (\d+\.?\d*)',
                    html_content,
                    re.IGNORECASE
                )
                if version_match:
                    result['version'] = version_match.group(1)

                return result

            # Shopify
            if 'cdn.shopify.com' in html_content or 'Shopify.theme' in html_content:
                result['name'] = 'Shopify'
                return result

            # Wix
            if 'wix.com' in html_content or 'X-Wix-' in html_content:
                result['name'] = 'Wix'
                return result

            # Squarespace
            if 'squarespace' in html_content.lower():
                result['name'] = 'Squarespace'
                return result

            # Magento
            if 'Magento' in html_content or '/skin/frontend/' in html_content:
                result['name'] = 'Magento'
                return result

            # PrestaShop
            if 'prestashop' in html_content.lower() or '/modules/ps_' in html_content:
                result['name'] = 'PrestaShop'
                return result

            # MediaWiki / Wikimedia
            if 'mediawiki' in html_content.lower() or 'wgVersion' in html_content:
                result['name'] = 'MediaWiki'
                # Verifica se é Wikimedia Foundation
                if 'wikimedia' in html_content.lower() or 'wikipedia' in html_content.lower():
                    result['name'] = 'Wikimedia (MediaWiki)'
                return result

            # Wikipedia/Wikimedia específico
            if 'wikipedia' in html_content.lower() or 'wikimedia.org' in html_content.lower():
                result['name'] = 'Wikimedia'
                return result

            # Blogger
            if 'blogger.com' in html_content or 'blogspot.com' in html_content:
                result['name'] = 'Blogger'
                return result

            # Ghost
            if 'ghost.io' in html_content or '"ghost"' in html_content:
                result['name'] = 'Ghost'
                return result

            # Webflow
            if 'webflow' in html_content.lower() or 'wf-page' in html_content:
                result['name'] = 'Webflow'
                return result

            # Hugo
            if 'hugo' in html_content.lower() or 'generator.*hugo' in html_content.lower():
                result['name'] = 'Hugo (Static)'
                return result

            # Jekyll
            if 'jekyll' in html_content.lower() or 'generator.*jekyll' in html_content.lower():
                result['name'] = 'Jekyll (Static)'
                return result

            # Next.js
            if '__next' in html_content or '_next/static' in html_content:
                result['name'] = 'Next.js'
                return result

            # Gatsby
            if 'gatsby' in html_content.lower() or 'gatsby-image' in html_content:
                result['name'] = 'Gatsby'
                return result

            # Detecção de HTML estático (sem CMS)
            # Verifica se NÃO tem sinais de frameworks dinâmicos
            is_static = self._is_static_html(html_content)
            if is_static:
                result['name'] = 'HTML Estático'
                return result

        except Exception as e:
            logger.debug(f"Erro ao analisar HTML para CMS: {e}")

        return result

    def _is_static_html(self, html_content):
        """
        Verifica se é um site HTML estático (sem CMS)

        Args:
            html_content: Conteúdo HTML

        Returns:
            True se aparenta ser HTML estático
        """
        if not html_content:
            return False

        html_lower = html_content.lower()

        # Sinais de que é estático
        static_indicators = 0

        # Não tem meta generator
        if '<meta name="generator"' not in html_lower:
            static_indicators += 1

        # Não tem sinais de frameworks comuns
        framework_signs = [
            'wp-content', 'wordpress', 'joomla', 'drupal',
            'cdn.shopify', 'wix.com', 'squarespace',
            '__next', 'gatsby', 'nuxt', 'vue', 'react',
            'angular', 'ember', 'backbone'
        ]

        has_framework = any(sign in html_lower for sign in framework_signs)
        if not has_framework:
            static_indicators += 1

        # Tem estrutura HTML básica simples
        if '<html' in html_lower and '</html>' in html_lower:
            static_indicators += 1

        # Não tem muitos scripts complexos
        script_count = html_lower.count('<script')
        if script_count < 5:  # Sites dinâmicos geralmente têm muitos scripts
            static_indicators += 1

        # Considera estático se tiver pelo menos 3 indicadores
        return static_indicators >= 3
