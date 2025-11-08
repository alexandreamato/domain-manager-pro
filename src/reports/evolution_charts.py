"""Gráficos de evolução temporal de domínios"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')


class EvolutionChartGenerator:
    """Gera gráficos de evolução temporal para métricas de domínios"""

    @staticmethod
    def create_seo_evolution_chart(history, parent_frame):
        """
        Cria gráfico de evolução do SEO Score

        Args:
            history: Lista de snapshots históricos
            parent_frame: Frame Tkinter onde o gráfico será inserido

        Returns:
            Canvas do Matplotlib
        """
        if not history or len(history) < 2:
            return None

        # Extrai dados
        dates = []
        seo_scores = []

        for snapshot in history:
            if snapshot.get('checked_at') and snapshot.get('seo_score') is not None:
                try:
                    date = datetime.fromisoformat(str(snapshot['checked_at']))
                    dates.append(date)
                    seo_scores.append(snapshot['seo_score'])
                except:
                    pass

        if len(dates) < 2:
            return None

        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Plot
        ax.plot(dates, seo_scores, color='#00adb5', linewidth=2, marker='o', markersize=6)

        # Linha de meta (70 = bom SEO)
        ax.axhline(y=70, color='#28a745', linestyle='--', alpha=0.5, label='Meta (70)')

        ax.set_title('Evolução do SEO Score', color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', color='white')
        ax.set_ylabel('SEO Score', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2)
        ax.legend()

        # Formata eixo X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45)

        # Limites do Y
        ax.set_ylim(0, 100)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        # Canvas Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_ssl_evolution_chart(history, parent_frame):
        """
        Cria gráfico de evolução do SSL (dias até expiração)

        Args:
            history: Lista de snapshots históricos
            parent_frame: Frame Tkinter

        Returns:
            Canvas do Matplotlib
        """
        if not history or len(history) < 2:
            return None

        dates = []
        ssl_days = []

        for snapshot in history:
            if snapshot.get('checked_at') and snapshot.get('ssl_expires_days') is not None:
                try:
                    date = datetime.fromisoformat(str(snapshot['checked_at']))
                    dates.append(date)
                    ssl_days.append(snapshot['ssl_expires_days'])
                except:
                    pass

        if len(dates) < 2:
            return None

        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Plot
        ax.plot(dates, ssl_days, color='#ffc107', linewidth=2, marker='o', markersize=6)

        # Linhas de alerta
        ax.axhline(y=30, color='#ffc107', linestyle='--', alpha=0.5, label='Aviso (30 dias)')
        ax.axhline(y=7, color='#dc3545', linestyle='--', alpha=0.5, label='Crítico (7 dias)')

        ax.set_title('Evolução do Certificado SSL', color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', color='white')
        ax.set_ylabel('Dias até expiração', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2)
        ax.legend()

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_domain_value_evolution_chart(history, parent_frame):
        """
        Cria gráfico de evolução do valor estimado do domínio

        Args:
            history: Lista de snapshots históricos
            parent_frame: Frame Tkinter

        Returns:
            Canvas do Matplotlib
        """
        if not history or len(history) < 2:
            return None

        dates = []
        values = []

        for snapshot in history:
            if snapshot.get('checked_at') and snapshot.get('estimated_domain_value') is not None:
                try:
                    date = datetime.fromisoformat(str(snapshot['checked_at']))
                    dates.append(date)
                    values.append(snapshot['estimated_domain_value'])
                except:
                    pass

        if len(dates) < 2:
            return None

        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Plot
        ax.plot(dates, values, color='#28a745', linewidth=2, marker='o', markersize=6)
        ax.fill_between(dates, values, alpha=0.3, color='#28a745')

        ax.set_title('Evolução do Valor Estimado', color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', color='white')
        ax.set_ylabel('Valor (USD)', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45)

        # Formata valores em USD
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_authority_evolution_chart(history, parent_frame):
        """
        Cria gráfico de evolução do Domain/Page Authority

        Args:
            history: Lista de snapshots históricos
            parent_frame: Frame Tkinter

        Returns:
            Canvas do Matplotlib
        """
        if not history or len(history) < 2:
            return None

        dates = []
        domain_authority = []
        page_authority = []

        for snapshot in history:
            if snapshot.get('checked_at'):
                try:
                    date = datetime.fromisoformat(str(snapshot['checked_at']))

                    da = snapshot.get('domain_authority')
                    pa = snapshot.get('page_authority')

                    if da is not None or pa is not None:
                        dates.append(date)
                        domain_authority.append(da if da is not None else 0)
                        page_authority.append(pa if pa is not None else 0)
                except:
                    pass

        if len(dates) < 2:
            return None

        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Plot
        ax.plot(dates, domain_authority, color='#17a2b8', linewidth=2, marker='o',
                markersize=6, label='Domain Authority')
        ax.plot(dates, page_authority, color='#e94560', linewidth=2, marker='s',
                markersize=6, label='Page Authority')

        ax.set_title('Evolução do Authority (MOZ)', color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', color='white')
        ax.set_ylabel('Authority Score', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2)
        ax.legend()

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45)

        ax.set_ylim(0, 100)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_multi_metric_chart(history, parent_frame):
        """
        Cria gráfico com múltiplas métricas normalizadas

        Args:
            history: Lista de snapshots históricos
            parent_frame: Frame Tkinter

        Returns:
            Canvas do Matplotlib
        """
        if not history or len(history) < 2:
            return None

        dates = []
        data = {
            'seo_score': [],
            'domain_authority': [],
            'ssl_health': []  # Normalizado: 100 quando > 90 dias, 0 quando expirado
        }

        for snapshot in history:
            if snapshot.get('checked_at'):
                try:
                    date = datetime.fromisoformat(str(snapshot['checked_at']))
                    dates.append(date)

                    # SEO Score
                    seo = snapshot.get('seo_score', 0) or 0
                    data['seo_score'].append(seo)

                    # Domain Authority
                    da = snapshot.get('domain_authority', 0) or 0
                    data['domain_authority'].append(da)

                    # SSL Health (normalizado)
                    ssl_days = snapshot.get('ssl_expires_days')
                    if ssl_days is None:
                        ssl_health = 0
                    elif ssl_days <= 0:
                        ssl_health = 0
                    elif ssl_days >= 90:
                        ssl_health = 100
                    else:
                        ssl_health = (ssl_days / 90) * 100

                    data['ssl_health'].append(ssl_health)

                except:
                    pass

        if len(dates) < 2:
            return None

        # Cria figura
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1a1a2e')
        ax.set_facecolor('#16213e')

        # Plot múltiplas métricas
        ax.plot(dates, data['seo_score'], color='#00adb5', linewidth=2,
                marker='o', label='SEO Score')
        ax.plot(dates, data['domain_authority'], color='#17a2b8', linewidth=2,
                marker='s', label='Domain Authority')
        ax.plot(dates, data['ssl_health'], color='#28a745', linewidth=2,
                marker='^', label='SSL Health')

        ax.set_title('Evolução de Métricas Principais', color='white',
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', color='white')
        ax.set_ylabel('Score (0-100)', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2)
        ax.legend()

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45)

        ax.set_ylim(0, 100)

        for spine in ax.spines.values():
            spine.set_color('#0f3460')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()

        return canvas
