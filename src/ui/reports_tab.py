"""Aba de relatórios e visualizações"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from src.reports.charts import ChartGenerator

logger = logging.getLogger(__name__)


class ReportsTab:
    """Aba de relatórios e visualizações"""

    def __init__(self, parent, db):
        """
        Inicializa a aba de relatórios

        Args:
            parent: Widget pai (Notebook)
            db: DatabaseManager
        """
        self.parent = parent
        self.db = db
        self.chart_generator = ChartGenerator()

        self.current_charts = []

        # Criar frame principal
        self.frame = ttk.Frame(parent)
        self.create_widgets()

    def create_widgets(self):
        """Cria os widgets da aba"""
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        title = ttk.Label(
            header_frame,
            text="📊 Relatórios e Estatísticas",
            font=('Arial', 16, 'bold')
        )
        title.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Atualizar",
            command=self.refresh_stats
        )
        refresh_btn.pack(side=tk.RIGHT)

        # Frame de estatísticas gerais
        stats_frame = ttk.LabelFrame(self.frame, text="Estatísticas Gerais", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.stats_labels = {}

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        # Total de domínios
        self._create_stat_widget(stats_grid, "Total de Domínios:", "total_domains", 0, 0)

        # Domínios ativos
        self._create_stat_widget(stats_grid, "Domínios Ativos (200):", "active_domains", 0, 2)

        # Com CMS
        self._create_stat_widget(stats_grid, "Com CMS Detectado:", "with_cms", 1, 0)

        # Com Analytics
        self._create_stat_widget(stats_grid, "Com Google Analytics:", "with_ga4", 1, 2)

        # Scrollable frame para gráficos
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Canvas e scrollbar
        canvas = tk.Canvas(canvas_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

        self.charts_container = ttk.Frame(canvas)
        self.charts_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.charts_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind scroll do mouse
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _create_stat_widget(self, parent, label_text, key, row, col):
        """Cria um widget de estatística"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=20, pady=10, sticky='w')

        label = ttk.Label(frame, text=label_text, font=('Arial', 10))
        label.pack(anchor='w')

        value = ttk.Label(frame, text="0", font=('Arial', 20, 'bold'), foreground='#00adb5')
        value.pack(anchor='w')

        self.stats_labels[key] = value

    def refresh_stats(self):
        """Atualiza estatísticas gerais"""
        try:
            stats = self.db.get_statistics()

            # Atualiza labels
            self.stats_labels['total_domains'].config(text=str(stats.get('total_domains', 0)))

            active = stats.get('status_distribution', {}).get('OK', 0)
            self.stats_labels['active_domains'].config(text=str(active))

            cms_total = sum(stats.get('cms_distribution', {}).values())
            self.stats_labels['with_cms'].config(text=str(cms_total))

            # Para GA4, precisamos consultar diretamente (filtra ocultos)
            domains = self.db.get_all_domains(include_hidden=False)
            with_ga4 = sum(1 for d in domains if d.get('ga4_code'))
            self.stats_labels['with_ga4'].config(text=str(with_ga4))

        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}")

    def refresh_charts(self, domains):
        """
        Atualiza os gráficos

        Args:
            domains: Lista de domínios
        """
        # Limpa gráficos existentes
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        self.current_charts = []

        if not domains:
            no_data_label = ttk.Label(
                self.charts_container,
                text="Nenhum dado disponível para gerar gráficos",
                font=('Arial', 12)
            )
            no_data_label.pack(pady=50)
            return

        # Atualiza estatísticas
        self.refresh_stats()

        # Frame para gráficos em grid
        charts_grid = ttk.Frame(self.charts_container)
        charts_grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        try:
            # Gráfico de distribuição de CMS
            cms_frame = ttk.LabelFrame(charts_grid, text="Distribuição de CMS", padding=5)
            cms_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

            cms_chart = self.chart_generator.create_cms_distribution_chart(domains, cms_frame)
            if cms_chart:
                cms_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                self.current_charts.append(cms_chart)

            # Gráfico de status HTTP
            status_frame = ttk.LabelFrame(charts_grid, text="Distribuição de Status HTTP", padding=5)
            status_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

            status_chart = self.chart_generator.create_status_distribution_chart(domains, status_frame)
            if status_chart:
                status_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                self.current_charts.append(status_chart)

            # Gráfico de cloud providers
            cloud_frame = ttk.LabelFrame(charts_grid, text="Provedores Cloud", padding=5)
            cloud_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

            cloud_chart = self.chart_generator.create_cloud_providers_chart(domains, cloud_frame)
            if cloud_chart:
                cloud_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                self.current_charts.append(cloud_chart)

            # Gráfico de SSL
            ssl_frame = ttk.LabelFrame(charts_grid, text="Expiração SSL", padding=5)
            ssl_frame.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

            ssl_chart = self.chart_generator.create_ssl_expiration_chart(domains, ssl_frame)
            if ssl_chart:
                ssl_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                self.current_charts.append(ssl_chart)

            # Configura grid
            charts_grid.columnconfigure(0, weight=1)
            charts_grid.columnconfigure(1, weight=1)
            charts_grid.rowconfigure(0, weight=1)
            charts_grid.rowconfigure(1, weight=1)

        except Exception as e:
            logger.error(f"Erro ao gerar gráficos: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar gráficos: {e}")
