"""Aba de configurações"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class SettingsTab:
    """Aba de configurações"""

    def __init__(self, parent, config, on_change_callback):
        """
        Inicializa a aba de configurações

        Args:
            parent: Widget pai (Notebook)
            config: ConfigManager
            on_change_callback: Callback para quando configurações mudarem
        """
        self.parent = parent
        self.config = config
        self.on_change_callback = on_change_callback

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
            text="⚙️ Configurações",
            font=('Arial', 16, 'bold')
        )
        title.pack(side=tk.LEFT)

        # Container com scroll
        canvas = tk.Canvas(self.frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)

        settings_container = ttk.Frame(canvas)
        settings_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=settings_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Seção de configurações gerais
        general_frame = ttk.LabelFrame(settings_container, text="Configurações Gerais", padding=20)
        general_frame.pack(fill=tk.X, padx=10, pady=10)

        # Timeout
        timeout_frame = ttk.Frame(general_frame)
        timeout_frame.pack(fill=tk.X, pady=5)

        ttk.Label(timeout_frame, text="Timeout (segundos):", width=30).pack(side=tk.LEFT)

        self.timeout_var = tk.IntVar(value=self.config.get('timeout', 5))
        timeout_spin = ttk.Spinbox(
            timeout_frame,
            from_=1,
            to=30,
            textvariable=self.timeout_var,
            width=10
        )
        timeout_spin.pack(side=tk.LEFT, padx=(10, 0))

        # Max workers
        workers_frame = ttk.Frame(general_frame)
        workers_frame.pack(fill=tk.X, pady=5)

        ttk.Label(workers_frame, text="Threads paralelas:", width=30).pack(side=tk.LEFT)

        self.workers_var = tk.IntVar(value=self.config.get('max_workers', 10))
        workers_spin = ttk.Spinbox(
            workers_frame,
            from_=1,
            to=50,
            textvariable=self.workers_var,
            width=10
        )
        workers_spin.pack(side=tk.LEFT, padx=(10, 0))

        # Auto-refresh automático
        auto_refresh_frame = ttk.Frame(general_frame)
        auto_refresh_frame.pack(fill=tk.X, pady=5)

        self.auto_refresh_enabled_var = tk.BooleanVar(value=self.config.get('auto_refresh_enabled', True))

        auto_refresh_check = ttk.Checkbutton(
            auto_refresh_frame,
            text="🔄 Atualizar automaticamente todos os domínios",
            variable=self.auto_refresh_enabled_var
        )
        auto_refresh_check.pack(anchor=tk.W, pady=5)

        # Intervalo de auto-refresh
        interval_frame = ttk.Frame(auto_refresh_frame)
        interval_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        ttk.Label(interval_frame, text="A cada:", width=12).pack(side=tk.LEFT)

        self.refresh_var = tk.IntVar(value=self.config.get('auto_refresh_interval', 24))
        refresh_spin = ttk.Spinbox(
            interval_frame,
            from_=1,
            to=168,  # Máximo 1 semana
            textvariable=self.refresh_var,
            width=8
        )
        refresh_spin.pack(side=tk.LEFT, padx=(5, 5))

        ttk.Label(interval_frame, text="hora(s)").pack(side=tk.LEFT)

        # Ajuda sobre auto-refresh
        auto_refresh_help = ttk.Label(
            auto_refresh_frame,
            text="ℹ️ Enquanto o app estiver aberto, atualizará todos os domínios automaticamente no intervalo configurado",
            font=('Arial', 8),
            foreground='#888'
        )
        auto_refresh_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 5))

        # Seção de SEO
        seo_frame = ttk.LabelFrame(settings_container, text="Configurações de SEO", padding=20)
        seo_frame.pack(fill=tk.X, padx=10, pady=10)

        # Checkbox para ativar Web SEO
        self.collect_web_seo_var = tk.BooleanVar(value=self.config.get('collect_web_seo', False))

        web_seo_check = ttk.Checkbutton(
            seo_frame,
            text="🌐 Coletar SEO da Web (MOZ, SimilarWeb, etc.)",
            variable=self.collect_web_seo_var
        )
        web_seo_check.pack(anchor=tk.W, pady=5)

        seo_help = ttk.Label(
            seo_frame,
            text="⚠️ Atenção: Ativa coleta de métricas avançadas de SEO da web. Pode deixar a análise mais lenta.",
            foreground='#ffa500',
            wraplength=600
        )
        seo_help.pack(anchor=tk.W, pady=(0, 10))

        seo_info = ttk.Label(
            seo_frame,
            text="Métricas coletadas: Domain Authority, Page Authority, Ranking Global, Backlinks, Idade do Domínio, Hosting Provider",
            foreground='#aaa',
            wraplength=600
        )
        seo_info.pack(anchor=tk.W)

        # Seção de API Keys
        api_frame = ttk.LabelFrame(settings_container, text="API Keys (Opcional)", padding=20)
        api_frame.pack(fill=tk.X, padx=10, pady=10)

        api_help = ttk.Label(
            api_frame,
            text="Configure suas chaves de API para funcionalidades avançadas de SEO",
            foreground='#aaa'
        )
        api_help.pack(anchor=tk.W, pady=(0, 10))

        # SEMrush API
        semrush_frame = ttk.Frame(api_frame)
        semrush_frame.pack(fill=tk.X, pady=5)

        ttk.Label(semrush_frame, text="SEMrush API Key:", width=20).pack(side=tk.LEFT)

        self.semrush_var = tk.StringVar(value=self.config.get('api_keys.semrush', ''))
        semrush_entry = ttk.Entry(semrush_frame, textvariable=self.semrush_var, width=40, show='*')
        semrush_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Estibot API
        estibot_frame = ttk.Frame(api_frame)
        estibot_frame.pack(fill=tk.X, pady=5)

        ttk.Label(estibot_frame, text="Estibot API Key:", width=20).pack(side=tk.LEFT)

        self.estibot_var = tk.StringVar(value=self.config.get('api_keys.estibot', ''))
        estibot_entry = ttk.Entry(estibot_frame, textvariable=self.estibot_var, width=40, show='*')
        estibot_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Moz API
        moz_frame = ttk.Frame(api_frame)
        moz_frame.pack(fill=tk.X, pady=5)

        ttk.Label(moz_frame, text="Moz API Key:", width=20).pack(side=tk.LEFT)

        self.moz_var = tk.StringVar(value=self.config.get('api_keys.moz', ''))
        moz_entry = ttk.Entry(moz_frame, textvariable=self.moz_var, width=40, show='*')
        moz_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Instruções Moz
        moz_help = ttk.Label(
            api_frame,
            text="ℹ️ Moz: Use o formato 'access_id:secret_key'",
            font=('Arial', 8),
            foreground='#888'
        )
        moz_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 5))

        # Wappalyzer API
        wappalyzer_frame = ttk.Frame(api_frame)
        wappalyzer_frame.pack(fill=tk.X, pady=5)

        ttk.Label(wappalyzer_frame, text="Wappalyzer API Key:", width=20).pack(side=tk.LEFT)

        self.wappalyzer_var = tk.StringVar(value=self.config.get('api_keys.wappalyzer', ''))
        wappalyzer_entry = ttk.Entry(wappalyzer_frame, textvariable=self.wappalyzer_var, width=40, show='*')
        wappalyzer_entry.pack(side=tk.LEFT, padx=(10, 0))

        # WhatCMS API
        whatcms_frame = ttk.Frame(api_frame)
        whatcms_frame.pack(fill=tk.X, pady=5)

        ttk.Label(whatcms_frame, text="WhatCMS API Key:", width=20).pack(side=tk.LEFT)

        self.whatcms_var = tk.StringVar(value=self.config.get('api_keys.whatcms', ''))
        whatcms_entry = ttk.Entry(whatcms_frame, textvariable=self.whatcms_var, width=40, show='*')
        whatcms_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Instruções CMS APIs
        cms_help = ttk.Label(
            api_frame,
            text="ℹ️ Wappalyzer e WhatCMS melhoram a detecção de CMS",
            font=('Arial', 8),
            foreground='#888'
        )
        cms_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))

        # VirusTotal API
        virustotal_frame = ttk.Frame(api_frame)
        virustotal_frame.pack(fill=tk.X, pady=5)

        ttk.Label(virustotal_frame, text="VirusTotal API Key:", width=20).pack(side=tk.LEFT)

        self.virustotal_var = tk.StringVar(value=self.config.get('api_keys.virustotal', ''))
        virustotal_entry = ttk.Entry(virustotal_frame, textvariable=self.virustotal_var, width=40, show='*')
        virustotal_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Google Safe Browsing API
        gsb_frame = ttk.Frame(api_frame)
        gsb_frame.pack(fill=tk.X, pady=5)

        ttk.Label(gsb_frame, text="Google Safe Browsing:", width=20).pack(side=tk.LEFT)

        self.gsb_var = tk.StringVar(value=self.config.get('api_keys.google_safe_browsing', ''))
        gsb_entry = ttk.Entry(gsb_frame, textvariable=self.gsb_var, width=40, show='*')
        gsb_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Instruções Security APIs
        security_help = ttk.Label(
            api_frame,
            text="ℹ️ VirusTotal e Google Safe Browsing verificam segurança e blacklists",
            font=('Arial', 8),
            foreground='#888'
        )
        security_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))

        # Google PageSpeed Insights API
        pagespeed_frame = ttk.Frame(api_frame)
        pagespeed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(pagespeed_frame, text="PageSpeed Insights:", width=20).pack(side=tk.LEFT)

        self.pagespeed_var = tk.StringVar(value=self.config.get('api_keys.pagespeed', ''))
        pagespeed_entry = ttk.Entry(pagespeed_frame, textvariable=self.pagespeed_var, width=40, show='*')
        pagespeed_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Instruções PageSpeed
        pagespeed_help = ttk.Label(
            api_frame,
            text="ℹ️ PageSpeed Insights fornece Core Web Vitals (lento, requer collect_web_seo ativo)",
            font=('Arial', 8),
            foreground='#888'
        )
        pagespeed_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))

        # Seção sobre
        about_frame = ttk.LabelFrame(settings_container, text="Sobre", padding=20)
        about_frame.pack(fill=tk.X, padx=10, pady=10)

        about_text = """
Domain Manager Pro v1.0.0

Sistema completo de gerenciamento e monitoramento de domínios.

Desenvolvido com Python e Tkinter.

Recursos:
- Análise automática de domínios
- Detecção de CMS, Analytics e tecnologias
- Verificação de SSL, WHOIS e DNS
- Relatórios e visualizações
- Exportação em múltiplos formatos
        """

        about_label = ttk.Label(about_frame, text=about_text.strip(), justify=tk.LEFT)
        about_label.pack(anchor=tk.W)

        # Botões de ação
        buttons_frame = ttk.Frame(settings_container)
        buttons_frame.pack(fill=tk.X, padx=10, pady=20)

        save_btn = ttk.Button(
            buttons_frame,
            text="💾 Salvar Configurações",
            command=self.save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = ttk.Button(
            buttons_frame,
            text="🔄 Restaurar Padrões",
            command=self.reset_settings
        )
        reset_btn.pack(side=tk.LEFT)

    def save_settings(self):
        """Salva as configurações"""
        try:
            # Salva configurações gerais
            self.config.set('timeout', self.timeout_var.get())
            self.config.set('max_workers', self.workers_var.get())
            self.config.set('auto_refresh_enabled', self.auto_refresh_enabled_var.get())
            self.config.set('auto_refresh_interval', self.refresh_var.get())

            # Salva configurações de SEO
            self.config.set('collect_web_seo', self.collect_web_seo_var.get())

            # Salva API keys
            self.config.set('api_keys.semrush', self.semrush_var.get())
            self.config.set('api_keys.estibot', self.estibot_var.get())
            self.config.set('api_keys.moz', self.moz_var.get())
            self.config.set('api_keys.wappalyzer', self.wappalyzer_var.get())
            self.config.set('api_keys.whatcms', self.whatcms_var.get())
            self.config.set('api_keys.virustotal', self.virustotal_var.get())
            self.config.set('api_keys.google_safe_browsing', self.gsb_var.get())
            self.config.set('api_keys.pagespeed', self.pagespeed_var.get())

            # Callback
            if self.on_change_callback:
                self.on_change_callback()

            logger.info("Configurações salvas")

        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

    def reset_settings(self):
        """Restaura configurações padrão"""
        if messagebox.askyesno("Confirmar", "Deseja realmente restaurar as configurações padrão?"):
            try:
                self.config.reset()

                # Atualiza campos
                self.timeout_var.set(self.config.get('timeout'))
                self.workers_var.set(self.config.get('max_workers'))
                self.refresh_var.set(self.config.get('auto_refresh_interval'))
                self.semrush_var.set('')
                self.estibot_var.set('')
                self.moz_var.set('')

                messagebox.showinfo("Sucesso", "Configurações restauradas!")

                # Callback
                if self.on_change_callback:
                    self.on_change_callback()

                logger.info("Configurações restauradas para padrão")

            except Exception as e:
                logger.error(f"Erro ao restaurar configurações: {e}")
                messagebox.showerror("Erro", f"Erro ao restaurar configurações: {e}")
