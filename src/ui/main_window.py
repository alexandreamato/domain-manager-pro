"""Janela principal do Domain Manager Pro"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.collectors.domain_collector import DomainCollector
from src.reports.exporter import DataExporter
from src.utils.config import ConfigManager
from src.ui.domains_tab import DomainsTab
from src.ui.seo_tab import SEOTab
from src.ui.reports_tab import ReportsTab
from src.ui.settings_tab import SettingsTab

logger = logging.getLogger(__name__)


class MainWindow:
    """Janela principal da aplicação"""

    def __init__(self):
        """Inicializa a janela principal"""
        self.root = tk.Tk()
        self.root.title("Domain Manager Pro")
        self.root.geometry("1400x900")

        # Managers
        self.db = DatabaseManager()
        self.config = ConfigManager()
        self.collector = DomainCollector(
            timeout=self.config.get('timeout', 5),
            max_workers=self.config.get('max_workers', 10)
        )

        # Dados
        self.domains_data = []

        # Aplicar tema escuro
        self.apply_dark_theme()

        # Criar interface
        self.create_widgets()

        # Carregar dados salvos
        self.load_saved_domains()

        # Configurar fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_dark_theme(self):
        """Aplica tema escuro na aplicação"""
        style = ttk.Style()
        style.theme_use('clam')

        # Cores do tema escuro
        bg_color = '#1a1a2e'
        fg_color = '#eee'
        select_bg = '#0f3460'
        select_fg = '#ffffff'

        # Configurações gerais
        self.root.configure(bg=bg_color)

        # Estilos
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background='#0f3460', foreground=fg_color, borderwidth=1)
        style.map('TButton', background=[('active', '#16213e')])

        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background='#16213e', foreground=fg_color, padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', '#0f3460')], foreground=[('selected', '#ffffff')])

        style.configure('Treeview', background='#16213e', foreground=fg_color, fieldbackground='#16213e', borderwidth=0)
        style.configure('Treeview.Heading', background='#0f3460', foreground='white', borderwidth=1)
        style.map('Treeview', background=[('selected', select_bg)], foreground=[('selected', select_fg)])

        style.configure('TEntry', fieldbackground='#16213e', foreground=fg_color, borderwidth=1)
        style.configure('TCombobox', fieldbackground='#16213e', foreground=fg_color, borderwidth=1)

    def create_widgets(self):
        """Cria os widgets da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="🌐 Domain Manager Pro",
            font=('Arial', 24, 'bold')
        )
        title_label.pack(side=tk.LEFT)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, font=('Arial', 10))
        status_label.pack(side=tk.RIGHT, padx=10)

        # Notebook (abas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Aba de Domínios
        self.domains_tab = DomainsTab(
            self.notebook,
            self.db,
            self.collector,
            self.config,
            self.on_analyze_complete
        )
        self.notebook.add(self.domains_tab.frame, text="🏠 Domínios")

        # Aba de SEO Dashboard
        self.seo_tab = SEOTab(self.notebook, self.db)
        self.notebook.add(self.seo_tab.frame, text="🔍 SEO Dashboard")

        # Aba de Relatórios
        self.reports_tab = ReportsTab(self.notebook, self.db)
        self.notebook.add(self.reports_tab.frame, text="📊 Relatórios")

        # Aba de Configurações
        self.settings_tab = SettingsTab(self.notebook, self.config, self.on_settings_changed)
        self.notebook.add(self.settings_tab.frame, text="⚙️ Configurações")

        # Bind para mudança de aba
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def load_saved_domains(self):
        """Carrega domínios salvos do banco de dados"""
        try:
            self.domains_data = self.db.get_all_domains()
            self.domains_tab.populate_table(self.domains_data)
            self.update_status(f"Carregados {len(self.domains_data)} domínios")
            logger.info(f"Carregados {len(self.domains_data)} domínios do banco de dados")
        except Exception as e:
            logger.error(f"Erro ao carregar domínios: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar domínios: {e}")

    def on_analyze_complete(self, results):
        """
        Callback chamado quando a análise é concluída

        Args:
            results: Lista de resultados da análise
        """
        # Salva no banco de dados
        for result in results:
            try:
                self.db.save_domain(result)
            except Exception as e:
                logger.error(f"Erro ao salvar domínio {result.get('domain')}: {e}")

        # Coleta subdomínios descobertos para análise automática
        discovered_subdomains = []
        for result in results:
            subdomains = result.get('discovered_subdomains', [])
            if subdomains:
                logger.info(f"Descobertos {len(subdomains)} subdomínios para {result.get('domain')}")
                discovered_subdomains.extend(subdomains)

        # Remove subdomínios que já existem no banco
        if discovered_subdomains:
            existing_domains = set(d['domain'] for d in self.domains_data)
            new_subdomains = [s for s in discovered_subdomains if s not in existing_domains]

            if new_subdomains:
                logger.info(f"Analisando {len(new_subdomains)} novos subdomínios...")
                self.update_status(f"Analisando {len(new_subdomains)} subdomínios descobertos...")

                # Analisa subdomínios em background
                threading.Thread(
                    target=self._analyze_subdomains,
                    args=(new_subdomains,),
                    daemon=True
                ).start()

        # Atualiza dados
        self.load_saved_domains()

        # Atualiza aba de relatórios
        self.reports_tab.refresh_charts(self.domains_data)

        # Atualiza aba de SEO
        self.seo_tab.populate_table(self.domains_data)

        self.update_status("Análise concluída")

    def _analyze_subdomains(self, subdomains):
        """
        Analisa subdomínios descobertos em background

        Args:
            subdomains: Lista de subdomínios para analisar
        """
        try:
            # Analisa subdomínios
            results = self.collector.collect_multiple(subdomains)

            # Salva no banco
            for result in results:
                try:
                    self.db.save_domain(result)
                except Exception as e:
                    logger.error(f"Erro ao salvar subdomínio {result.get('domain')}: {e}")

            # Atualiza UI no thread principal
            self.root.after(0, self._on_subdomains_complete, len(results))

        except Exception as e:
            logger.error(f"Erro ao analisar subdomínios: {e}")

    def _on_subdomains_complete(self, count):
        """
        Callback quando análise de subdomínios é concluída

        Args:
            count: Número de subdomínios analisados
        """
        # Atualiza dados
        self.load_saved_domains()

        # Atualiza abas
        self.reports_tab.refresh_charts(self.domains_data)
        self.seo_tab.populate_table(self.domains_data)

        # Notifica usuário
        self.update_status(f"{count} subdomínios analisados")
        messagebox.showinfo(
            "Subdomínios Descobertos",
            f"{count} subdomínios foram descobertos e analisados automaticamente!"
        )

    def on_tab_changed(self, event):
        """Callback para mudança de aba"""
        tab_id = self.notebook.select()
        tab_text = self.notebook.tab(tab_id, "text")

        if "Relatórios" in tab_text:
            # Atualiza relatórios quando a aba é selecionada
            self.reports_tab.refresh_charts(self.domains_data)
        elif "SEO Dashboard" in tab_text:
            # Atualiza SEO Dashboard quando a aba é selecionada
            self.seo_tab.populate_table(self.domains_data)

    def on_settings_changed(self):
        """Callback para quando as configurações são alteradas"""
        # Recarrega configurações
        self.config.load()

        # Atualiza collector
        self.collector = DomainCollector(
            timeout=self.config.get('timeout', 5),
            max_workers=self.config.get('max_workers', 10)
        )

        # Atualiza no domains_tab
        self.domains_tab.collector = self.collector

        self.update_status("Configurações atualizadas")
        logger.info("Configurações atualizadas")

    def update_status(self, message):
        """
        Atualiza a barra de status

        Args:
            message: Mensagem a ser exibida
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_var.set(f"{timestamp} - {message}")

    def on_closing(self):
        """Callback para fechamento da janela"""
        if messagebox.askokcancel("Sair", "Deseja realmente sair do Domain Manager Pro?"):
            logger.info("Aplicação fechada pelo usuário")
            self.root.destroy()

    def run(self):
        """Inicia o loop principal da aplicação"""
        logger.info("Domain Manager Pro iniciado")
        self.root.mainloop()
