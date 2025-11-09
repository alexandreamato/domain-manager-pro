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
from src.ui.monitoring_tab import MonitoringTab

logger = logging.getLogger(__name__)


class MainWindow:
    """Janela principal da aplicação"""

    def __init__(self):
        """Inicializa a janela principal"""
        self.root = tk.Tk()
        self.root.title("🌐 Domain Manager Pro")
        self.root.geometry("1400x900")

        # Tenta configurar ícone se disponível
        try:
            # Tenta carregar ícone PNG se existir
            icon_path = "assets/icon.png"
            import os
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            logger.debug(f"Não foi possível carregar ícone: {e}")

        # Managers
        self.db = DatabaseManager()
        self.config = ConfigManager()
        self.collector = DomainCollector(
            timeout=self.config.get('timeout', 5),
            max_workers=self.config.get('max_workers', 10),
            collect_web_seo=self.config.get('collect_web_seo', False),
            semrush_api_key=self.config.get('api_keys.semrush', ''),
            moz_api_key=self.config.get('api_keys.moz', ''),
            wappalyzer_key=self.config.get('api_keys.wappalyzer', ''),
            whatcms_key=self.config.get('api_keys.whatcms', ''),
            virustotal_api_key=self.config.get('api_keys.virustotal', ''),
            google_safe_browsing_key=self.config.get('api_keys.google_safe_browsing', ''),
            pagespeed_api_key=self.config.get('api_keys.pagespeed', '')
        )

        # Dados
        self.domains_data = []

        # Auto-refresh
        self.auto_refresh_timer = None
        self.last_auto_refresh = None

        # Aplicar tema escuro
        self.apply_dark_theme()

        # Criar interface
        self.create_widgets()

        # Carregar dados salvos
        self.load_saved_domains()

        # Iniciar auto-refresh se configurado
        self.start_auto_refresh()

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

        # Aba de Monitoramento
        self.monitoring_tab = MonitoringTab(self.notebook, self.db, self.collector)
        self.notebook.add(self.monitoring_tab.frame, text="🔍 Monitoramento")

        # Aba de SEO Dashboard
        self.seo_tab = SEOTab(self.notebook, self.db)
        self.notebook.add(self.seo_tab.frame, text="📈 SEO Dashboard")

        # Aba de Relatórios
        self.reports_tab = ReportsTab(self.notebook, self.db)
        self.notebook.add(self.reports_tab.frame, text="📊 Relatórios")

        # Aba de Configurações
        self.settings_tab = SettingsTab(self.notebook, self.config, self.on_settings_changed)
        self.notebook.add(self.settings_tab.frame, text="⚙️ Configurações")

        # Bind para mudança de aba
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def load_saved_domains(self):
        """Carrega domínios salvos do banco de dados (filtra ocultos)"""
        try:
            self.domains_data = self.db.get_all_domains(include_hidden=False)
            self.domains_tab.populate_table(self.domains_data)
            self.update_status(f"Carregados {len(self.domains_data)} domínio(s) visível(is)")
            logger.info(f"Carregados {len(self.domains_data)} domínios visíveis do banco de dados")
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

        # Remove subdomínios que já existem no banco (visíveis ou ocultos)
        if discovered_subdomains:
            # Busca TODOS os domínios (incluindo ocultos) para evitar re-descoberta
            all_domains_in_db = self.db.get_all_domains(include_hidden=True)
            existing_domains = set(d['domain'] for d in all_domains_in_db)

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
            max_workers=self.config.get('max_workers', 10),
            collect_web_seo=self.config.get('collect_web_seo', False),
            semrush_api_key=self.config.get('api_keys.semrush', ''),
            moz_api_key=self.config.get('api_keys.moz', ''),
            wappalyzer_key=self.config.get('api_keys.wappalyzer', ''),
            whatcms_key=self.config.get('api_keys.whatcms', ''),
            virustotal_api_key=self.config.get('api_keys.virustotal', ''),
            google_safe_browsing_key=self.config.get('api_keys.google_safe_browsing', ''),
            pagespeed_api_key=self.config.get('api_keys.pagespeed', '')
        )

        # Atualiza no domains_tab
        self.domains_tab.collector = self.collector

        # Reinicia auto-refresh com novas configurações
        self.stop_auto_refresh()
        self.start_auto_refresh()

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

    def start_auto_refresh(self):
        """Inicia o timer de auto-refresh diário"""
        # Verifica se está habilitado
        auto_refresh_enabled = self.config.get('auto_refresh_enabled', True)
        if not auto_refresh_enabled:
            logger.info("Auto-refresh desabilitado")
            return

        # Intervalo em horas (padrão: 24h = 1 dia)
        refresh_interval_hours = self.config.get('auto_refresh_interval', 24)

        # Carrega última atualização do DB
        last_refresh_str = self.db.get_setting('last_auto_refresh')

        if last_refresh_str:
            try:
                from datetime import datetime, timedelta
                self.last_auto_refresh = datetime.fromisoformat(last_refresh_str)

                # Calcula tempo desde última atualização
                time_since_refresh = datetime.now() - self.last_auto_refresh
                hours_since_refresh = time_since_refresh.total_seconds() / 3600

                logger.info(f"Última auto-atualização: {hours_since_refresh:.1f}h atrás")

                # Se já passou o intervalo, atualiza agora
                if hours_since_refresh >= refresh_interval_hours:
                    logger.info("Intervalo de atualização atingido, executando agora...")
                    self.root.after(5000, self.execute_auto_refresh)  # 5s após iniciar
                    return
            except Exception as e:
                logger.error(f"Erro ao processar última atualização: {e}")

        # Agenda próxima verificação (verifica a cada hora)
        check_interval_ms = 3600000  # 1 hora em milissegundos
        self.auto_refresh_timer = self.root.after(check_interval_ms, self.check_auto_refresh)

        logger.info(f"Auto-refresh agendado (intervalo: {refresh_interval_hours}h)")

    def check_auto_refresh(self):
        """Verifica se é hora de executar auto-refresh"""
        from datetime import datetime, timedelta

        refresh_interval_hours = self.config.get('auto_refresh_interval', 24)

        # Se nunca atualizou, atualiza agora
        if not self.last_auto_refresh:
            logger.info("Primeira auto-atualização")
            self.execute_auto_refresh()
            return

        # Calcula tempo desde última atualização
        time_since_refresh = datetime.now() - self.last_auto_refresh
        hours_since_refresh = time_since_refresh.total_seconds() / 3600

        # Se passou o intervalo, atualiza
        if hours_since_refresh >= refresh_interval_hours:
            logger.info(f"Auto-refresh executado ({hours_since_refresh:.1f}h desde última atualização)")
            self.execute_auto_refresh()
        else:
            # Agenda próxima verificação (1 hora)
            check_interval_ms = 3600000
            self.auto_refresh_timer = self.root.after(check_interval_ms, self.check_auto_refresh)

            hours_remaining = refresh_interval_hours - hours_since_refresh
            logger.debug(f"Próxima auto-atualização em ~{hours_remaining:.1f}h")

    def execute_auto_refresh(self):
        """Executa a atualização automática de todos os domínios"""
        from datetime import datetime

        try:
            logger.info("═══ INICIANDO AUTO-ATUALIZAÇÃO AUTOMÁTICA ═══")

            # Atualiza status
            self.update_status("🔄 Auto-atualização iniciada...")

            # Pega todos os domínios não ocultos
            domains = self.db.get_all_domains(include_hidden=False)

            if not domains:
                logger.info("Nenhum domínio para atualizar")
                self.update_status("Nenhum domínio para atualizar")
                return

            logger.info(f"Auto-atualizando {len(domains)} domínio(s)...")

            # Extrai apenas os nomes dos domínios
            domain_names = [d['domain'] for d in domains]

            # Executa análise em thread separada
            def analyze_thread():
                try:
                    # Análise com callback de progresso
                    def progress_callback(current, total, domain):
                        percent = int((current / total) * 100)
                        self.root.after(0, lambda: self.update_status(
                            f"🔄 Auto-atualização: {current}/{total} ({percent}%) - {domain}"
                        ))

                    # Coleta informações
                    results = self.collector.collect_multiple(domain_names, progress_callback)

                    # Salva no banco
                    for result in results:
                        self.db.save_domain(result)

                    # Atualiza timestamp da última atualização
                    from datetime import datetime
                    now = datetime.now()
                    self.last_auto_refresh = now
                    self.db.save_setting('last_auto_refresh', now.isoformat())

                    # Recarrega dados na UI
                    self.root.after(0, self.load_saved_domains)

                    # Atualiza status
                    self.root.after(0, lambda: self.update_status(
                        f"✅ Auto-atualização concluída: {len(results)} domínio(s)"
                    ))

                    logger.info(f"═══ AUTO-ATUALIZAÇÃO CONCLUÍDA: {len(results)} domínio(s) ═══")

                    # Agenda próxima verificação
                    check_interval_ms = 3600000  # 1 hora
                    self.auto_refresh_timer = self.root.after(check_interval_ms, self.check_auto_refresh)

                except Exception as e:
                    logger.error(f"Erro na auto-atualização: {e}")
                    self.root.after(0, lambda: self.update_status(f"❌ Erro na auto-atualização: {e}"))

            # Inicia thread
            thread = threading.Thread(target=analyze_thread, daemon=True)
            thread.start()

        except Exception as e:
            logger.error(f"Erro ao iniciar auto-atualização: {e}")
            self.update_status(f"❌ Erro ao iniciar auto-atualização")

    def stop_auto_refresh(self):
        """Para o timer de auto-refresh"""
        if self.auto_refresh_timer:
            self.root.after_cancel(self.auto_refresh_timer)
            self.auto_refresh_timer = None
            logger.info("Auto-refresh interrompido")

    def on_closing(self):
        """Callback para fechamento da janela"""
        # Para auto-refresh antes de fechar
        self.stop_auto_refresh()

        if messagebox.askokcancel("Sair", "Deseja realmente sair do Domain Manager Pro?"):
            logger.info("Aplicação fechada pelo usuário")
            self.root.destroy()

    def run(self):
        """Inicia o loop principal da aplicação"""
        logger.info("Domain Manager Pro iniciado")
        self.root.mainloop()
