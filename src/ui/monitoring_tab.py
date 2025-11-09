"""
Aba de Monitoramento Abrangente - Dashboard completo de dados de domínios
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MonitoringTab:
    """Aba de monitoramento abrangente de domínios"""

    def __init__(self, parent, db, collector=None):
        """
        Inicializa a aba de monitoramento

        Args:
            parent: Widget pai (Notebook)
            db: DatabaseManager instance
            collector: DomainCollector instance (opcional)
        """
        self.db = db
        self.collector = collector
        self.current_domain = None

        # Frame principal
        self.frame = ttk.Frame(parent)

        # Criar interface
        self.create_widgets()

    def create_widgets(self):
        """Cria os widgets da interface"""
        # Container com scroll
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame superior: Seleção de domínio e alertas globais
        top_frame = ttk.Frame(container)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Seleção de domínio
        select_frame = ttk.LabelFrame(top_frame, text="Selecionar Domínio", padding=10)
        select_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(select_frame, text="Domínio:").pack(side=tk.LEFT, padx=(0, 10))

        self.domain_var = tk.StringVar()
        self.domain_combo = ttk.Combobox(
            select_frame,
            textvariable=self.domain_var,
            width=40,
            state='readonly'
        )
        self.domain_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.domain_combo.bind('<<ComboboxSelected>>', self.on_domain_selected)

        refresh_btn = ttk.Button(
            select_frame,
            text="🔄 Atualizar Lista",
            command=self.refresh_domain_list
        )
        refresh_btn.pack(side=tk.LEFT)

        # Alertas globais
        alerts_frame = ttk.LabelFrame(top_frame, text="Alertas Críticos", padding=10)
        alerts_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.alerts_label = ttk.Label(
            alerts_frame,
            text="Nenhum alerta",
            foreground='green',
            font=('Arial', 10, 'bold')
        )
        self.alerts_label.pack()

        # Notebook principal com seções
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # === SEÇÕES DO DASHBOARD ===

        # 1. Visão Geral
        self.create_overview_tab()

        # 2. WHOIS/RDAP
        self.create_whois_tab()

        # 3. DNS e Email
        self.create_dns_tab()

        # 4. SSL/TLS
        self.create_ssl_tab()

        # 5. Segurança e Blacklists
        self.create_security_tab()

        # 6. SEO e Tráfego
        self.create_seo_tab()

        # 7. Performance
        self.create_performance_tab()

        # 8. Dados Técnicos
        self.create_technical_tab()

        # Carregar lista de domínios
        self.refresh_domain_list()

    def create_overview_tab(self):
        """Cria aba de visão geral"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Visão Geral")

        # Container com scroll
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Conteúdo
        self.overview_frame = scrollable_frame

        # Cards de métricas
        cards_frame = ttk.Frame(self.overview_frame)
        cards_frame.pack(fill=tk.X, padx=10, pady=10)

        # Status do domínio
        self.status_card = self.create_card(cards_frame, "Status do Domínio", 0, 0)

        # Validade
        self.validity_card = self.create_card(cards_frame, "Validade", 0, 1)

        # Segurança
        self.security_card = self.create_card(cards_frame, "Segurança", 0, 2)

        # SEO/Visibilidade
        self.seo_card = self.create_card(cards_frame, "SEO", 1, 0)

        # Email Auth
        self.email_card = self.create_card(cards_frame, "Email Auth", 1, 1)

        # Tecnologia
        self.tech_card = self.create_card(cards_frame, "Tecnologia", 1, 2)

    def create_whois_tab(self):
        """Cria aba de dados WHOIS/RDAP"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📋 WHOIS")

        # ScrolledText para exibir dados
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.whois_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.whois_text.pack(fill=tk.BOTH, expand=True)

    def create_dns_tab(self):
        """Cria aba de DNS e Email Authentication"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🌐 DNS & Email")

        # Container com scroll
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.dns_frame = scrollable_frame

        # Seção de registros DNS
        dns_section = ttk.LabelFrame(self.dns_frame, text="Registros DNS", padding=10)
        dns_section.pack(fill=tk.BOTH, padx=10, pady=10)

        self.dns_text = scrolledtext.ScrolledText(
            dns_section,
            wrap=tk.WORD,
            height=15,
            font=('Courier', 10)
        )
        self.dns_text.pack(fill=tk.BOTH, expand=True)

        # Seção de autenticação de email
        email_section = ttk.LabelFrame(self.dns_frame, text="Autenticação de Email", padding=10)
        email_section.pack(fill=tk.BOTH, padx=10, pady=10)

        self.email_auth_text = scrolledtext.ScrolledText(
            email_section,
            wrap=tk.WORD,
            height=12,
            font=('Courier', 10)
        )
        self.email_auth_text.pack(fill=tk.BOTH, expand=True)

    def create_ssl_tab(self):
        """Cria aba de SSL/TLS"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔒 SSL/TLS")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.ssl_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.ssl_text.pack(fill=tk.BOTH, expand=True)

    def create_security_tab(self):
        """Cria aba de Segurança e Blacklists"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🛡️ Segurança")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.security_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.security_text.pack(fill=tk.BOTH, expand=True)

    def create_seo_tab(self):
        """Cria aba de SEO e Tráfego"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📈 SEO")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.seo_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.seo_text.pack(fill=tk.BOTH, expand=True)

    def create_performance_tab(self):
        """Cria aba de Performance e Core Web Vitals"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚡ Performance")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.performance_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.performance_text.pack(fill=tk.BOTH, expand=True)

    def create_technical_tab(self):
        """Cria aba de Dados Técnicos"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Técnico")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.technical_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=30,
            font=('Courier', 10)
        )
        self.technical_text.pack(fill=tk.BOTH, expand=True)

    def create_card(self, parent, title, row, col):
        """Cria um card de métrica visual aprimorado"""
        # Frame externo com cor de fundo
        outer_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        outer_frame.grid(row=row, column=col, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        parent.grid_columnconfigure(col, weight=1)

        # Título do card
        title_label = tk.Label(
            outer_frame,
            text=title,
            font=('Arial', 10, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=5
        )
        title_label.pack(fill=tk.X)

        # Container de conteúdo com background
        content_frame = tk.Frame(outer_frame, bg='white', padx=15, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Ícone/Badge grande no topo
        icon_label = tk.Label(
            content_frame,
            text="",
            font=('Arial', 36),
            bg='white'
        )
        icon_label.pack()

        # Valor principal (número grande)
        value_label = tk.Label(
            content_frame,
            text="",
            font=('Arial', 24, 'bold'),
            bg='white'
        )
        value_label.pack()

        # Descrição/detalhes (texto menor)
        detail_label = tk.Label(
            content_frame,
            text="Selecione um domínio",
            font=('Arial', 10),
            bg='white',
            fg='#555',
            justify=tk.CENTER
        )
        detail_label.pack()

        # Retorna um dicionário com referências
        return {
            'frame': outer_frame,
            'content_frame': content_frame,
            'icon': icon_label,
            'value': value_label,
            'detail': detail_label
        }

    def refresh_domain_list(self):
        """Atualiza lista de domínios"""
        try:
            # Busca apenas domínios visíveis
            domains = self.db.get_all_domains(include_hidden=False)

            domain_names = sorted([d['domain'] for d in domains])

            self.domain_combo['values'] = domain_names

            if domain_names and not self.domain_var.get():
                self.domain_combo.current(0)
                self.on_domain_selected()

        except Exception as e:
            logger.error(f"Erro ao carregar domínios: {e}")

    def on_domain_selected(self, event=None):
        """Callback quando um domínio é selecionado"""
        domain_name = self.domain_var.get()

        if not domain_name:
            return

        try:
            # Busca dados do domínio diretamente (mais eficiente)
            domain_data = self.db.get_domain(domain_name)

            if not domain_data:
                return

            self.current_domain = domain_data

            # Atualiza todas as seções
            self.update_overview(domain_data)
            self.update_whois_display(domain_data)
            self.update_dns_display(domain_data)
            self.update_ssl_display(domain_data)
            self.update_security_display(domain_data)
            self.update_seo_display(domain_data)
            self.update_performance_display(domain_data)
            self.update_technical_display(domain_data)
            self.update_alerts(domain_data)

        except Exception as e:
            logger.error(f"Erro ao carregar dados do domínio: {e}")

    def update_overview(self, data):
        """Atualiza cards da visão geral com visual aprimorado"""

        # === 1. STATUS DO DOMÍNIO ===
        status = data.get('status_code')
        if status == 200:
            self.status_card['content_frame'].config(bg='#d4edda')  # Verde claro
            self.status_card['icon'].config(text='✓', fg='#28a745', bg='#d4edda')
            self.status_card['value'].config(text=f'{status}', fg='#28a745', bg='#d4edda')
            self.status_card['detail'].config(text='Online', fg='#155724', bg='#d4edda')
        elif status and 300 <= status < 400:
            self.status_card['content_frame'].config(bg='#fff3cd')  # Amarelo claro
            self.status_card['icon'].config(text='↻', fg='#ffc107', bg='#fff3cd')
            self.status_card['value'].config(text=f'{status}', fg='#ffc107', bg='#fff3cd')
            self.status_card['detail'].config(text='Redirect', fg='#856404', bg='#fff3cd')
        elif status and status >= 400:
            self.status_card['content_frame'].config(bg='#f8d7da')  # Vermelho claro
            self.status_card['icon'].config(text='✗', fg='#dc3545', bg='#f8d7da')
            self.status_card['value'].config(text=f'{status}', fg='#dc3545', bg='#f8d7da')
            self.status_card['detail'].config(text='Erro', fg='#721c24', bg='#f8d7da')
        else:
            self.status_card['content_frame'].config(bg='#e2e3e5')  # Cinza claro
            self.status_card['icon'].config(text='?', fg='#6c757d', bg='#e2e3e5')
            self.status_card['value'].config(text='N/A', fg='#6c757d', bg='#e2e3e5')
            self.status_card['detail'].config(text='Desconhecido', fg='#383d41', bg='#e2e3e5')

        # IP adicional
        ip = data.get('ip_address', '-')
        current_detail = self.status_card['detail'].cget('text')
        self.status_card['detail'].config(text=f'{current_detail}\n{ip}')

        # === 2. VALIDADE (menor das duas) ===
        days_until_exp = data.get('days_until_expiration')
        ssl_days = data.get('ssl_expires_days')

        # Determina o menor prazo
        min_days = None
        min_label = ""

        if days_until_exp is not None and ssl_days is not None:
            if days_until_exp < ssl_days:
                min_days = days_until_exp
                min_label = "Domínio"
            else:
                min_days = ssl_days
                min_label = "SSL"
        elif days_until_exp is not None:
            min_days = days_until_exp
            min_label = "Domínio"
        elif ssl_days is not None:
            min_days = ssl_days
            min_label = "SSL"

        if min_days is not None:
            if min_days <= 7:
                self.validity_card['content_frame'].config(bg='#f8d7da')  # Vermelho
                self.validity_card['icon'].config(text='⚠', fg='#dc3545', bg='#f8d7da')
                self.validity_card['value'].config(text=f'{min_days}', fg='#dc3545', bg='#f8d7da')
                self.validity_card['detail'].config(text=f'dias ({min_label})\nCRÍTICO!', fg='#721c24', bg='#f8d7da')
            elif min_days <= 30:
                self.validity_card['content_frame'].config(bg='#fff3cd')  # Amarelo
                self.validity_card['icon'].config(text='⏰', fg='#ffc107', bg='#fff3cd')
                self.validity_card['value'].config(text=f'{min_days}', fg='#ffc107', bg='#fff3cd')
                self.validity_card['detail'].config(text=f'dias ({min_label})\nAtenção', fg='#856404', bg='#fff3cd')
            else:
                self.validity_card['content_frame'].config(bg='#d4edda')  # Verde
                self.validity_card['icon'].config(text='✓', fg='#28a745', bg='#d4edda')
                self.validity_card['value'].config(text=f'{min_days}', fg='#28a745', bg='#d4edda')
                self.validity_card['detail'].config(text=f'dias ({min_label})\nOK', fg='#155724', bg='#d4edda')
        else:
            self.validity_card['content_frame'].config(bg='#e2e3e5')
            self.validity_card['icon'].config(text='?', fg='#6c757d', bg='#e2e3e5')
            self.validity_card['value'].config(text='N/A', fg='#6c757d', bg='#e2e3e5')
            self.validity_card['detail'].config(text='Sem dados', fg='#383d41', bg='#e2e3e5')

        # === 3. SEGURANÇA ===
        vt_malicious = data.get('virustotal_malicious', 0)
        blacklist_count = data.get('blacklist_count', 0)
        reputation = data.get('reputation_score', 0)

        total_threats = vt_malicious + blacklist_count

        if total_threats > 0:
            self.security_card['content_frame'].config(bg='#f8d7da')  # Vermelho
            self.security_card['icon'].config(text='⚠', fg='#dc3545', bg='#f8d7da')
            self.security_card['value'].config(text=f'{total_threats}', fg='#dc3545', bg='#f8d7da')
            self.security_card['detail'].config(text='Ameaças\ndetectadas!', fg='#721c24', bg='#f8d7da')
        elif reputation < 0:
            self.security_card['content_frame'].config(bg='#fff3cd')  # Amarelo
            self.security_card['icon'].config(text='⚡', fg='#ffc107', bg='#fff3cd')
            self.security_card['value'].config(text=f'{reputation}', fg='#ffc107', bg='#fff3cd')
            self.security_card['detail'].config(text='Reputação\nbaixa', fg='#856404', bg='#fff3cd')
        else:
            self.security_card['content_frame'].config(bg='#d4edda')  # Verde
            self.security_card['icon'].config(text='🛡', fg='#28a745', bg='#d4edda')
            self.security_card['value'].config(text='Limpo', fg='#28a745', bg='#d4edda')
            self.security_card['detail'].config(text=f'Score: {reputation}', fg='#155724', bg='#d4edda')

        # === 4. SEO ===
        da = data.get('domain_authority')
        pa = data.get('page_authority')
        perf_score = data.get('performance_score')

        # Usa melhor métrica disponível
        main_metric = da or pa or perf_score

        if main_metric:
            if main_metric >= 70:
                bg_color = '#d4edda'
                fg_color = '#28a745'
                detail_color = '#155724'
                icon = '★'
                status_text = 'Excelente'
            elif main_metric >= 50:
                bg_color = '#fff3cd'
                fg_color = '#ffc107'
                detail_color = '#856404'
                icon = '●'
                status_text = 'Bom'
            else:
                bg_color = '#f8d7da'
                fg_color = '#dc3545'
                detail_color = '#721c24'
                icon = '▼'
                status_text = 'Precisa melhorar'

            self.seo_card['content_frame'].config(bg=bg_color)
            self.seo_card['icon'].config(text=icon, fg=fg_color, bg=bg_color)
            self.seo_card['value'].config(text=f'{main_metric}', fg=fg_color, bg=bg_color)

            label = 'DA' if da else 'PA' if pa else 'Perf'
            self.seo_card['detail'].config(text=f'{label}: {status_text}', fg=detail_color, bg=bg_color)
        else:
            self.seo_card['content_frame'].config(bg='#e2e3e5')
            self.seo_card['icon'].config(text='?', fg='#6c757d', bg='#e2e3e5')
            self.seo_card['value'].config(text='N/A', fg='#6c757d', bg='#e2e3e5')
            self.seo_card['detail'].config(text='Sem dados', fg='#383d41', bg='#e2e3e5')

        # === 5. EMAIL AUTH ===
        spf_valid = data.get('spf_valid', 0)
        dmarc_policy = data.get('dmarc_policy')
        dkim_configured = data.get('dkim_configured', 0)

        # Conta configurações
        configured = sum([bool(spf_valid), bool(dmarc_policy), bool(dkim_configured)])

        if configured == 3:
            self.email_card['content_frame'].config(bg='#d4edda')  # Verde
            self.email_card['icon'].config(text='✓', fg='#28a745', bg='#d4edda')
            self.email_card['value'].config(text='3/3', fg='#28a745', bg='#d4edda')
            self.email_card['detail'].config(text='Totalmente\nconfigurado', fg='#155724', bg='#d4edda')
        elif configured >= 1:
            self.email_card['content_frame'].config(bg='#fff3cd')  # Amarelo
            self.email_card['icon'].config(text='⚠', fg='#ffc107', bg='#fff3cd')
            self.email_card['value'].config(text=f'{configured}/3', fg='#ffc107', bg='#fff3cd')
            self.email_card['detail'].config(text='Parcialmente\nconfigurado', fg='#856404', bg='#fff3cd')
        else:
            self.email_card['content_frame'].config(bg='#f8d7da')  # Vermelho
            self.email_card['icon'].config(text='✗', fg='#dc3545', bg='#f8d7da')
            self.email_card['value'].config(text='0/3', fg='#dc3545', bg='#f8d7da')
            self.email_card['detail'].config(text='Não\nconfigurado', fg='#721c24', bg='#f8d7da')

        # === 6. TECNOLOGIA ===
        cms = data.get('cms_detected')
        cloud = data.get('cloud_provider')

        if cms:
            self.tech_card['content_frame'].config(bg='#d1ecf1')  # Azul claro
            self.tech_card['icon'].config(text='⚙', fg='#17a2b8', bg='#d1ecf1')

            # Abrevia nome do CMS se muito longo
            cms_short = cms if len(cms) <= 12 else cms[:9] + '...'
            self.tech_card['value'].config(text=cms_short, fg='#17a2b8', bg='#d1ecf1')

            detail_text = f'CMS'
            if cloud:
                detail_text += f'\n☁ {cloud}'
            self.tech_card['detail'].config(text=detail_text, fg='#0c5460', bg='#d1ecf1')
        else:
            self.tech_card['content_frame'].config(bg='#e2e3e5')
            self.tech_card['icon'].config(text='?', fg='#6c757d', bg='#e2e3e5')
            self.tech_card['value'].config(text='N/A', fg='#6c757d', bg='#e2e3e5')
            detail = 'Sem CMS'
            if cloud:
                detail = f'☁ {cloud}'
            self.tech_card['detail'].config(text=detail, fg='#383d41', bg='#e2e3e5')

    def update_whois_display(self, data):
        """Atualiza display WHOIS"""
        self.whois_text.delete('1.0', tk.END)

        whois_info = []
        whois_info.append("=" * 60)
        whois_info.append("INFORMAÇÕES WHOIS/RDAP")
        whois_info.append("=" * 60)
        whois_info.append("")

        # Registrar
        if data.get('registrar'):
            whois_info.append(f"Registrar: {data['registrar']}")

        # Datas
        if data.get('whois_created'):
            whois_info.append(f"Data de Criação: {data['whois_created']}")
        if data.get('whois_expires'):
            whois_info.append(f"Data de Expiração: {data['whois_expires']}")
        if data.get('whois_updated'):
            whois_info.append(f"Última Atualização: {data['whois_updated']}")

        # Dias até expiração
        if data.get('days_until_expiration') is not None:
            days = data['days_until_expiration']
            if days < 0:
                whois_info.append(f"⚠️ DOMÍNIO EXPIRADO! ({abs(days)} dias atrás)")
            elif days <= 7:
                whois_info.append(f"⚠️ CRÍTICO: Expira em {days} dias!")
            elif days <= 30:
                whois_info.append(f"⚠️ ATENÇÃO: Expira em {days} dias")
            else:
                whois_info.append(f"✅ Expira em {days} dias")

        # Idade do domínio
        if data.get('domain_age_days'):
            years = data['domain_age_days'] // 365
            whois_info.append(f"Idade do Domínio: {years} anos ({data['domain_age_days']} dias)")

        whois_info.append("")

        # Status
        if data.get('whois_status'):
            whois_info.append(f"Status: {data['whois_status']}")

        # Nameservers
        if data.get('whois_nameservers'):
            whois_info.append(f"\nNameservers:")
            ns_list = data['whois_nameservers'].split(', ')
            for ns in ns_list:
                whois_info.append(f"  - {ns}")

        # Contatos
        whois_info.append("")
        if data.get('whois_registrant_name'):
            whois_info.append(f"Registrante: {data['whois_registrant_name']}")
        if data.get('whois_registrant_org'):
            whois_info.append(f"Organização: {data['whois_registrant_org']}")

        self.whois_text.insert('1.0', '\n'.join(whois_info))

    def update_dns_display(self, data):
        """Atualiza display DNS"""
        self.dns_text.delete('1.0', tk.END)

        dns_info = []
        dns_info.append("REGISTROS DNS")
        dns_info.append("=" * 60)
        dns_info.append("")

        # A Records
        if data.get('dns_a_records'):
            try:
                a_records = json.loads(data['dns_a_records'])
                dns_info.append(f"A Records (IPv4):")
                for record in a_records:
                    dns_info.append(f"  {record}")
                dns_info.append("")
            except:
                pass

        # MX Records
        if data.get('dns_mx_records'):
            try:
                mx_records = json.loads(data['dns_mx_records'])
                dns_info.append(f"MX Records (Email):")
                for record in mx_records:
                    dns_info.append(f"  {record}")
                dns_info.append("")
            except:
                pass

        # NS Records
        if data.get('dns_ns_records'):
            try:
                ns_records = json.loads(data['dns_ns_records'])
                dns_info.append(f"NS Records (Nameservers):")
                for record in ns_records:
                    dns_info.append(f"  {record}")
                dns_info.append("")
            except:
                pass

        # Reverse DNS
        if data.get('ip_reverse_dns'):
            dns_info.append(f"Reverse DNS (PTR): {data['ip_reverse_dns']}")
            dns_info.append("")

        self.dns_text.insert('1.0', '\n'.join(dns_info))

        # Email Authentication
        self.email_auth_text.delete('1.0', tk.END)

        email_info = []
        email_info.append("AUTENTICAÇÃO DE EMAIL")
        email_info.append("=" * 60)
        email_info.append("")

        # SPF
        email_info.append("SPF (Sender Policy Framework):")
        if data.get('spf_record'):
            status = "✅ Configurado e válido" if data.get('spf_valid') else "⚠️ Configurado mas inválido"
            email_info.append(f"  Status: {status}")
            email_info.append(f"  Record: {data['spf_record']}")
        else:
            email_info.append("  Status: ❌ Não configurado")
        email_info.append("")

        # DMARC
        email_info.append("DMARC (Domain-based Message Authentication):")
        if data.get('dmarc_record'):
            email_info.append(f"  Status: ✅ Configurado")
            email_info.append(f"  Policy: {data.get('dmarc_policy', 'none')}")
            email_info.append(f"  Record: {data['dmarc_record']}")
        else:
            email_info.append("  Status: ❌ Não configurado")
        email_info.append("")

        # DKIM
        email_info.append("DKIM (DomainKeys Identified Mail):")
        if data.get('dkim_configured'):
            email_info.append("  Status: ✅ Configurado (seletores encontrados)")
        else:
            email_info.append("  Status: ❌ Não configurado ou seletores não encontrados")

        self.email_auth_text.insert('1.0', '\n'.join(email_info))

    def update_ssl_display(self, data):
        """Atualiza display SSL"""
        self.ssl_text.delete('1.0', tk.END)

        ssl_info = []
        ssl_info.append("=" * 60)
        ssl_info.append("CERTIFICADO SSL/TLS")
        ssl_info.append("=" * 60)
        ssl_info.append("")

        if not data.get('ssl_issuer'):
            ssl_info.append("❌ Sem certificado SSL")
            self.ssl_text.insert('1.0', '\n'.join(ssl_info))
            return

        # Emissor
        ssl_info.append(f"Emissor: {data['ssl_issuer']}")

        # Validade
        if data.get('ssl_valid_from'):
            ssl_info.append(f"Válido desde: {data['ssl_valid_from']}")
        if data.get('ssl_valid_until'):
            ssl_info.append(f"Válido até: {data['ssl_valid_until']}")

        # Dias até expiração
        if data.get('ssl_expires_days') is not None:
            days = data['ssl_expires_days']
            if days < 0:
                ssl_info.append(f"⚠️ CERTIFICADO EXPIRADO! ({abs(days)} dias atrás)")
            elif days <= 7:
                ssl_info.append(f"⚠️ CRÍTICO: Expira em {days} dias!")
            elif days <= 30:
                ssl_info.append(f"⚠️ ATENÇÃO: Expira em {days} dias")
            else:
                ssl_info.append(f"✅ Expira em {days} dias")

        ssl_info.append("")

        # Status de validade
        is_valid = data.get('ssl_is_valid', 0)
        ssl_info.append(f"Certificado válido: {'✅ Sim' if is_valid else '❌ Não'}")

        chain_valid = data.get('ssl_chain_valid', 0)
        ssl_info.append(f"Cadeia SSL válida: {'✅ Sim' if chain_valid else '❌ Não'}")

        # Algoritmo de assinatura
        if data.get('ssl_signature_algorithm'):
            ssl_info.append(f"Algoritmo de assinatura: {data['ssl_signature_algorithm']}")

        # SANs (Subject Alternative Names)
        if data.get('ssl_san_domains'):
            try:
                san_domains = json.loads(data['ssl_san_domains'])
                ssl_info.append(f"\nDomínios alternativos (SANs):")
                for san in san_domains[:10]:  # Limita a 10
                    ssl_info.append(f"  - {san}")
                if len(san_domains) > 10:
                    ssl_info.append(f"  ... e mais {len(san_domains) - 10} domínios")
            except:
                pass

        self.ssl_text.insert('1.0', '\n'.join(ssl_info))

    def update_security_display(self, data):
        """Atualiza display de Segurança"""
        self.security_text.delete('1.0', tk.END)

        security_info = []
        security_info.append("=" * 60)
        security_info.append("SEGURANÇA E REPUTAÇÃO")
        security_info.append("=" * 60)
        security_info.append("")

        # Score geral
        reputation = data.get('reputation_score', 0)
        if reputation >= 50:
            rep_status = "✅ Excelente"
        elif reputation >= 0:
            rep_status = "⚠️ Boa"
        elif reputation >= -50:
            rep_status = "⚠️ Moderada"
        else:
            rep_status = "❌ Ruim"

        security_info.append(f"Score de Reputação: {reputation} ({rep_status})")
        security_info.append("")

        # VirusTotal
        security_info.append("VirusTotal:")
        vt_malicious = data.get('virustotal_malicious', 0)
        vt_suspicious = data.get('virustotal_suspicious', 0)
        vt_reputation = data.get('virustotal_reputation', 0)

        if vt_malicious > 0:
            security_info.append(f"  ❌ {vt_malicious} scanners detectaram como MALICIOSO")
        if vt_suspicious > 0:
            security_info.append(f"  ⚠️ {vt_suspicious} scanners marcaram como SUSPEITO")

        if vt_malicious == 0 and vt_suspicious == 0:
            security_info.append(f"  ✅ Nenhuma ameaça detectada")

        security_info.append(f"  Reputação VT: {vt_reputation}")
        security_info.append("")

        # Google Safe Browsing
        security_info.append("Google Safe Browsing:")
        gsb_safe = data.get('gsb_is_safe', 1)

        if gsb_safe:
            security_info.append("  ✅ Domínio seguro")
        else:
            security_info.append("  ❌ AMEAÇA DETECTADA!")
            if data.get('gsb_threats'):
                try:
                    threats = json.loads(data['gsb_threats'])
                    security_info.append(f"  Tipos de ameaça: {', '.join(threats)}")
                except:
                    pass
        security_info.append("")

        # Blacklists (DNSBL)
        security_info.append("Blacklists Públicas (DNSBL):")
        blacklist_count = data.get('blacklist_count', 0)

        if blacklist_count == 0:
            security_info.append("  ✅ IP não está em blacklists")
        else:
            security_info.append(f"  ❌ IP encontrado em {blacklist_count} blacklist(s)")
            security_info.append("  ⚠️ Pode afetar entregabilidade de emails")

        self.security_text.insert('1.0', '\n'.join(security_info))

    def update_seo_display(self, data):
        """Atualiza display SEO"""
        self.seo_text.delete('1.0', tk.END)

        seo_info = []
        seo_info.append("=" * 60)
        seo_info.append("SEO E VISIBILIDADE")
        seo_info.append("=" * 60)
        seo_info.append("")

        # MOZ Metrics
        seo_info.append("MOZ Metrics:")
        if data.get('domain_authority') or data.get('page_authority'):
            seo_info.append(f"  Domain Authority (DA): {data.get('domain_authority', 'N/A')}")
            seo_info.append(f"  Page Authority (PA): {data.get('page_authority', 'N/A')}")
        else:
            seo_info.append("  Sem dados disponíveis")
        seo_info.append("")

        # Rankings
        seo_info.append("Rankings:")
        if data.get('global_rank'):
            seo_info.append(f"  Ranking Global: {data['global_rank']:,}")
        else:
            seo_info.append("  Ranking Global: N/A")
        seo_info.append("")

        # Backlinks
        if data.get('backlinks_count'):
            seo_info.append(f"Backlinks: {data['backlinks_count']:,}")
        else:
            seo_info.append("Backlinks: N/A")
        seo_info.append("")

        # Indexação Google
        if data.get('google_indexed_pages'):
            seo_info.append(f"Páginas indexadas (Google): {data['google_indexed_pages']:,}")
        else:
            seo_info.append("Páginas indexadas (Google): N/A")
        seo_info.append("")

        # SEO Score
        if data.get('seo_score'):
            seo_info.append(f"SEO Score: {data['seo_score']}/100")
        seo_info.append("")

        # Valor estimado
        if data.get('estimated_domain_value'):
            seo_info.append(f"Valor estimado do domínio: ${data['estimated_domain_value']:,}")

        self.seo_text.insert('1.0', '\n'.join(seo_info))

    def update_performance_display(self, data):
        """Atualiza display de Performance"""
        self.performance_text.delete('1.0', tk.END)

        perf_info = []
        perf_info.append("=" * 60)
        perf_info.append("MÉTRICAS DE PERFORMANCE (PageSpeed Insights)")
        perf_info.append("=" * 60)
        perf_info.append("")

        if not data.get('performance_score'):
            perf_info.append("⚠️ Métricas de performance não disponíveis")
            perf_info.append("")
            perf_info.append("Para coletar:")
            perf_info.append("1. Ative 'Coletar SEO da Web' nas configurações")
            perf_info.append("2. Configure API key do PageSpeed Insights (opcional mas recomendado)")
            perf_info.append("3. Re-analise o domínio")
            self.performance_text.insert('1.0', '\n'.join(perf_info))
            return

        # Performance Score
        score = data.get('performance_score', 0)
        if score >= 90:
            score_status = "✅ Excelente"
            score_color = "verde"
        elif score >= 50:
            score_status = "⚠️ Precisa melhorar"
            score_color = "amarelo"
        else:
            score_status = "❌ Ruim"
            score_color = "vermelho"

        perf_info.append(f"Performance Score: {score}/100 ({score_status})")
        perf_info.append("=" * 60)
        perf_info.append("")

        # Core Web Vitals
        perf_info.append("CORE WEB VITALS (Métricas principais do Google):")
        perf_info.append("")

        # LCP - Largest Contentful Paint
        lcp = data.get('performance_lcp')
        if lcp:
            lcp_sec = lcp / 1000
            if lcp_sec <= 2.5:
                lcp_status = "✅ Bom"
            elif lcp_sec <= 4.0:
                lcp_status = "⚠️ Precisa melhorar"
            else:
                lcp_status = "❌ Ruim"

            perf_info.append(f"LCP (Largest Contentful Paint): {lcp_sec:.2f}s {lcp_status}")
            perf_info.append("  → Tempo para o maior elemento ser carregado")
            perf_info.append(f"  → Bom: ≤2.5s | Melhorar: ≤4.0s | Ruim: >4.0s")
        else:
            perf_info.append("LCP (Largest Contentful Paint): N/A")

        perf_info.append("")

        # FID - First Input Delay
        fid = data.get('performance_fid')
        if fid:
            if fid <= 100:
                fid_status = "✅ Bom"
            elif fid <= 300:
                fid_status = "⚠️ Precisa melhorar"
            else:
                fid_status = "❌ Ruim"

            perf_info.append(f"FID (First Input Delay): {fid}ms {fid_status}")
            perf_info.append("  → Tempo de resposta à primeira interação")
            perf_info.append(f"  → Bom: ≤100ms | Melhorar: ≤300ms | Ruim: >300ms")
        else:
            perf_info.append("FID (First Input Delay): N/A")

        perf_info.append("")

        # CLS - Cumulative Layout Shift
        cls = data.get('performance_cls')
        if cls is not None:
            if cls <= 0.1:
                cls_status = "✅ Bom"
            elif cls <= 0.25:
                cls_status = "⚠️ Precisa melhorar"
            else:
                cls_status = "❌ Ruim"

            perf_info.append(f"CLS (Cumulative Layout Shift): {cls:.3f} {cls_status}")
            perf_info.append("  → Estabilidade visual (quanto menor, melhor)")
            perf_info.append(f"  → Bom: ≤0.1 | Melhorar: ≤0.25 | Ruim: >0.25")
        else:
            perf_info.append("CLS (Cumulative Layout Shift): N/A")

        perf_info.append("")
        perf_info.append("=" * 60)
        perf_info.append("OUTRAS MÉTRICAS:")
        perf_info.append("")

        # FCP - First Contentful Paint
        fcp = data.get('performance_fcp')
        if fcp:
            fcp_sec = fcp / 1000
            perf_info.append(f"FCP (First Contentful Paint): {fcp_sec:.2f}s")
            perf_info.append("  → Tempo para primeiro conteúdo aparecer")
        else:
            perf_info.append("FCP (First Contentful Paint): N/A")

        perf_info.append("")

        # TTFB - Time to First Byte
        ttfb = data.get('performance_ttfb')
        if ttfb:
            ttfb_ms = ttfb
            if ttfb_ms <= 200:
                ttfb_status = "✅"
            elif ttfb_ms <= 500:
                ttfb_status = "⚠️"
            else:
                ttfb_status = "❌"
            perf_info.append(f"TTFB (Time to First Byte): {ttfb_ms}ms {ttfb_status}")
            perf_info.append("  → Tempo de resposta do servidor")
        else:
            perf_info.append("TTFB (Time to First Byte): N/A")

        perf_info.append("")

        # TTI - Time to Interactive
        tti = data.get('performance_tti')
        if tti:
            tti_sec = tti / 1000
            perf_info.append(f"TTI (Time to Interactive): {tti_sec:.2f}s")
            perf_info.append("  → Tempo até a página estar totalmente interativa")
        else:
            perf_info.append("TTI (Time to Interactive): N/A")

        perf_info.append("")

        # TBT - Total Blocking Time
        tbt = data.get('performance_tbt')
        if tbt:
            perf_info.append(f"TBT (Total Blocking Time): {tbt}ms")
            perf_info.append("  → Tempo total de bloqueio da thread principal")
        else:
            perf_info.append("TBT (Total Blocking Time): N/A")

        perf_info.append("")

        # Speed Index
        speed_index = data.get('performance_speed_index')
        if speed_index:
            si_sec = speed_index / 1000
            perf_info.append(f"Speed Index: {si_sec:.2f}s")
            perf_info.append("  → Velocidade de renderização visual")
        else:
            perf_info.append("Speed Index: N/A")

        self.performance_text.insert('1.0', '\n'.join(perf_info))

    def update_technical_display(self, data):
        """Atualiza display de dados técnicos"""
        self.technical_text.delete('1.0', tk.END)

        tech_info = []
        tech_info.append("=" * 60)
        tech_info.append("DADOS TÉCNICOS")
        tech_info.append("=" * 60)
        tech_info.append("")

        # HTTP/Web
        tech_info.append("HTTP/Servidor:")
        tech_info.append(f"  Status Code: {data.get('status_code', 'N/A')}")
        tech_info.append(f"  Servidor: {data.get('server', 'N/A')}")
        tech_info.append(f"  Cloud Provider: {data.get('cloud_provider', 'N/A')}")
        tech_info.append(f"  Redirects: {data.get('redirect_count', 0)}")
        tech_info.append("")

        # CMS e Analytics
        tech_info.append("CMS e Analytics:")
        tech_info.append(f"  CMS: {data.get('cms_detected', 'Nenhum')}")
        if data.get('cms_version'):
            tech_info.append(f"  Versão: {data['cms_version']}")
        tech_info.append(f"  GA4: {data.get('ga4_code', 'Não detectado')}")
        tech_info.append(f"  Facebook Pixel: {data.get('fb_pixel', 'Não detectado')}")
        tech_info.append("")

        # Rede
        tech_info.append("Rede:")
        tech_info.append(f"  IP: {data.get('ip_address', 'N/A')}")
        tech_info.append(f"  Reverse DNS: {data.get('ip_reverse_dns', 'N/A')}")
        tech_info.append(f"  ASN: {data.get('ip_asn', 'N/A')}")
        tech_info.append("")

        # Geolocalização
        if data.get('ip_country') or data.get('ip_city'):
            tech_info.append("Geolocalização:")
            if data.get('ip_country'):
                tech_info.append(f"  País: {data['ip_country']}")
            if data.get('ip_city'):
                tech_info.append(f"  Cidade: {data['ip_city']}")
            if data.get('ip_latitude') and data.get('ip_longitude'):
                tech_info.append(f"  Coordenadas: {data['ip_latitude']}, {data['ip_longitude']}")
            if data.get('ip_timezone'):
                tech_info.append(f"  Timezone: {data['ip_timezone']}")
            if data.get('ip_isp'):
                tech_info.append(f"  ISP: {data['ip_isp']}")
            if data.get('ip_organization'):
                tech_info.append(f"  Organização: {data['ip_organization']}")
            tech_info.append("")

        # Hosting
        if data.get('hosting_provider'):
            tech_info.append(f"Provedor de Hospedagem: {data['hosting_provider']}")
            tech_info.append("")

        # Subdomínios descobertos
        if data.get('discovered_subdomains'):
            try:
                subdomains = json.loads(data['discovered_subdomains']) if isinstance(data['discovered_subdomains'], str) else data['discovered_subdomains']
                if subdomains:
                    tech_info.append(f"Subdomínios descobertos ({len(subdomains)}):")
                    for subdomain in subdomains[:20]:  # Limita a 20
                        tech_info.append(f"  - {subdomain}")
                    if len(subdomains) > 20:
                        tech_info.append(f"  ... e mais {len(subdomains) - 20} subdomínios")
            except:
                pass

        self.technical_text.insert('1.0', '\n'.join(tech_info))

    def update_alerts(self, data):
        """Atualiza alertas críticos"""
        alerts = []

        # Verifica expiração do domínio
        days_until_exp = data.get('days_until_expiration')
        if days_until_exp is not None:
            if days_until_exp < 0:
                alerts.append(f"❌ DOMÍNIO EXPIRADO!")
            elif days_until_exp <= 7:
                alerts.append(f"⚠️ Domínio expira em {days_until_exp} dias!")
            elif days_until_exp <= 30:
                alerts.append(f"⚠️ Domínio expira em {days_until_exp} dias")

        # Verifica SSL
        ssl_days = data.get('ssl_expires_days')
        if ssl_days is not None:
            if ssl_days < 0:
                alerts.append(f"❌ SSL EXPIRADO!")
            elif ssl_days <= 7:
                alerts.append(f"⚠️ SSL expira em {ssl_days} dias!")

        # Verifica segurança
        if data.get('virustotal_malicious', 0) > 0:
            alerts.append(f"❌ Detectado como malicioso!")
        if data.get('blacklist_count', 0) > 0:
            alerts.append(f"⚠️ Em {data['blacklist_count']} blacklist(s)")
        if not data.get('gsb_is_safe', 1):
            alerts.append(f"❌ Ameaça Google Safe Browsing!")

        # Verifica email auth
        if not data.get('spf_valid'):
            alerts.append(f"⚠️ SPF não configurado")
        if not data.get('dmarc_record'):
            alerts.append(f"⚠️ DMARC não configurado")

        # Atualiza label
        if alerts:
            self.alerts_label.config(
                text="\n".join(alerts[:3]),  # Máximo 3 alertas
                foreground='red',
                font=('Arial', 10, 'bold')
            )
        else:
            self.alerts_label.config(
                text="✅ Tudo OK!",
                foreground='green',
                font=('Arial', 10, 'bold')
            )
