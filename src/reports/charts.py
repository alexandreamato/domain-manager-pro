"""Gerador de gráficos e visualizações"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')


class ChartGenerator:
    """Gera gráficos e visualizações para os dados"""

    @staticmethod
    def create_cms_distribution_chart(domains, parent_frame):
        """
        Cria gráfico de distribuição de CMS

        Args:
            domains: Lista de domínios
            parent_frame: Frame Tkinter onde o gráfico será inserido

        Returns:
            Canvas do Matplotlib
        """
        # Conta CMS
        cms_count = {}
        for domain in domains:
            cms = domain.get('cms_detected', 'Desconhecido')
            if cms:
                cms_count[cms] = cms_count.get(cms, 0) + 1

        if not cms_count:
            return None

        # Cria figura (tamanho reduzido para melhor visualização)
        fig, ax = plt.subplots(figsize=(5, 4), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Gráfico de pizza
        colors = ['#e94560', '#0f3460', '#16213e', '#533483', '#1a1a2e', '#00adb5']
        wedges, texts, autotexts = ax.pie(
            cms_count.values(),
            labels=cms_count.keys(),
            autopct='%1.1f%%',
            colors=colors,
            textprops={'color': 'white', 'fontsize': 9}
        )

        ax.set_title('Distribuição de CMS', color='white', fontsize=12, fontweight='bold')

        # Canvas Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_status_distribution_chart(domains, parent_frame):
        """
        Cria gráfico de distribuição de status HTTP

        Args:
            domains: Lista de domínios
            parent_frame: Frame Tkinter onde o gráfico será inserido

        Returns:
            Canvas do Matplotlib
        """
        # Conta status
        status_groups = {'OK (200)': 0, 'Redirect (3xx)': 0, 'Error (4xx/5xx)': 0, 'Outros': 0}

        for domain in domains:
            status = domain.get('status_code')
            if status is None:
                status_groups['Outros'] += 1
            elif status == 200:
                status_groups['OK (200)'] += 1
            elif 300 <= status < 400:
                status_groups['Redirect (3xx)'] += 1
            elif status >= 400:
                status_groups['Error (4xx/5xx)'] += 1
            else:
                status_groups['Outros'] += 1

        # Cria figura (tamanho reduzido)
        fig, ax = plt.subplots(figsize=(5, 4), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Gráfico de barras
        colors = ['#28a745', '#ffc107', '#dc3545', '#6c757d']
        bars = ax.bar(
            status_groups.keys(),
            status_groups.values(),
            color=colors,
            edgecolor='white',
            linewidth=1.5
        )

        ax.set_title('Distribuição de Status HTTP', color='white', fontsize=12, fontweight='bold')
        ax.set_ylabel('Quantidade', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=8)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        # Canvas Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_cloud_providers_chart(domains, parent_frame):
        """
        Cria gráfico de provedores cloud

        Args:
            domains: Lista de domínios
            parent_frame: Frame Tkinter onde o gráfico será inserido

        Returns:
            Canvas do Matplotlib
        """
        # Conta providers
        provider_count = {}
        for domain in domains:
            provider = domain.get('cloud_provider', 'Não detectado')
            if provider:
                provider_count[provider] = provider_count.get(provider, 0) + 1

        if not provider_count:
            return None

        # Limita aos top 10
        sorted_providers = sorted(provider_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # Cria figura (tamanho reduzido)
        fig, ax = plt.subplots(figsize=(6, 4), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Gráfico de barras horizontais
        providers = [p[0] for p in sorted_providers]
        counts = [p[1] for p in sorted_providers]

        bars = ax.barh(providers, counts, color='#00adb5', edgecolor='white', linewidth=1.5)

        ax.set_title('Provedores Cloud Mais Usados', color='white', fontsize=12, fontweight='bold')
        ax.set_xlabel('Quantidade', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=8)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        # Canvas Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_ssl_expiration_chart(domains, parent_frame):
        """
        Cria gráfico de expiração SSL

        Args:
            domains: Lista de domínios
            parent_frame: Frame Tkinter onde o gráfico será inserido

        Returns:
            Canvas do Matplotlib
        """
        # Conta por faixa de dias
        ssl_ranges = {
            'Expirado/Sem SSL': 0,
            '1-30 dias': 0,
            '31-90 dias': 0,
            '91-180 dias': 0,
            '> 180 dias': 0
        }

        for domain in domains:
            ssl_days = domain.get('ssl_expires_days')
            if ssl_days is None or ssl_days <= 0:
                ssl_ranges['Expirado/Sem SSL'] += 1
            elif ssl_days <= 30:
                ssl_ranges['1-30 dias'] += 1
            elif ssl_days <= 90:
                ssl_ranges['31-90 dias'] += 1
            elif ssl_days <= 180:
                ssl_ranges['91-180 dias'] += 1
            else:
                ssl_ranges['> 180 dias'] += 1

        # Cria figura (tamanho reduzido)
        fig, ax = plt.subplots(figsize=(5, 4), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Gráfico de barras
        colors = ['#dc3545', '#ffc107', '#17a2b8', '#28a745', '#6c757d']
        bars = ax.bar(
            ssl_ranges.keys(),
            ssl_ranges.values(),
            color=colors,
            edgecolor='white',
            linewidth=1.5
        )

        ax.set_title('Expiração de Certificados SSL', color='white', fontsize=12, fontweight='bold')
        ax.set_ylabel('Quantidade', color='white', fontsize=9)
        ax.tick_params(colors='white', axis='x', rotation=15, labelsize=8)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        # Canvas Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas
