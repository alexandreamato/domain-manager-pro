"""Aba de gerenciamento de domínios"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import logging
from datetime import datetime
from src.utils.favicon_cache import FaviconCache

logger = logging.getLogger(__name__)


class DomainsTab:
    """Aba de gerenciamento de domínios"""

    def __init__(self, parent, db, collector, config, on_complete_callback):
        """
        Inicializa a aba de domínios

        Args:
            parent: Widget pai (Notebook)
            db: DatabaseManager
            collector: DomainCollector
            config: ConfigManager
            on_complete_callback: Callback para quando análise completar
        """
        self.parent = parent
        self.db = db
        self.collector = collector
        self.config = config
        self.on_complete_callback = on_complete_callback

        self.analyzing = False
        self.current_data = []
        self.sort_reverse = {}  # Controla direção de ordenação por coluna
        self.current_sort_column = None  # Rastreia coluna atualmente ordenada

        # Cache de favicons
        self.favicon_cache = FaviconCache()

        # Criar frame principal
        self.frame = ttk.Frame(parent)
        self.create_widgets()

    def create_widgets(self):
        """Cria os widgets da aba"""
        # Frame superior - entrada de domínios
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Label
        label = ttk.Label(input_frame, text="📝 Adicionar domínios (um por linha):", font=('Arial', 11, 'bold'))
        label.pack(anchor=tk.W, pady=(0, 5))

        # Frame para text area e botão
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(fill=tk.X)

        # Text area para domínios
        text_frame = ttk.Frame(entry_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.domains_text = scrolledtext.ScrolledText(
            text_frame,
            height=5,
            width=50,
            bg='#16213e',
            fg='#eee',
            insertbackground='white',
            font=('Consolas', 10)
        )
        self.domains_text.pack(fill=tk.BOTH, expand=True)

        # Botões
        buttons_frame = ttk.Frame(entry_frame)
        buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        self.analyze_btn = ttk.Button(
            buttons_frame,
            text="🔍 Analisar Domínios",
            command=self.analyze_domains
        )
        self.analyze_btn.pack(fill=tk.X, pady=(0, 5))

        clear_btn = ttk.Button(
            buttons_frame,
            text="🗑️ Limpar",
            command=lambda: self.domains_text.delete('1.0', tk.END)
        )
        clear_btn.pack(fill=tk.X, pady=(0, 5))

        import_btn = ttk.Button(
            buttons_frame,
            text="📂 Importar TXT",
            command=self.import_domains
        )
        import_btn.pack(fill=tk.X)

        # Barra de progresso
        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.progress_label = ttk.Label(self.progress_frame, text="", width=30)
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))

        # Inicialmente oculta
        self.progress_frame.pack_forget()

        # Frame de ferramentas
        tools_frame = ttk.Frame(self.frame)
        tools_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Busca
        ttk.Label(tools_frame, text="🔎 Buscar:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_table())

        search_entry = ttk.Entry(tools_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Filtro por status
        ttk.Label(tools_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        self.status_filter = tk.StringVar(value="Todos")
        status_combo = ttk.Combobox(
            tools_frame,
            textvariable=self.status_filter,
            values=["Todos", "OK (200)", "Redirect (3xx)", "Erro (4xx/5xx)"],
            state='readonly',
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=(0, 20))
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_table())

        # Filtro por CMS
        ttk.Label(tools_frame, text="CMS:").pack(side=tk.LEFT, padx=(0, 5))

        self.cms_filter = tk.StringVar(value="Todos")
        self.cms_combo = ttk.Combobox(
            tools_frame,
            textvariable=self.cms_filter,
            values=["Todos"],
            state='readonly',
            width=15
        )
        self.cms_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.cms_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_table())

        # Frame de botões (segunda linha para garantir visibilidade)
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Botões de ação
        issues_btn = ttk.Button(buttons_frame, text="⚠️ Problemas", command=self.show_issues_only)
        issues_btn.pack(side=tk.LEFT, padx=(0, 5))

        export_btn = ttk.Button(buttons_frame, text="💾 Exportar", command=self.export_data)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))

        refresh_btn = ttk.Button(buttons_frame, text="🔄 Atualizar", command=self.refresh_selected)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        hide_btn = ttk.Button(buttons_frame, text="🙈 Ocultar", command=self.hide_selected)
        hide_btn.pack(side=tk.LEFT, padx=(0, 5))

        show_hidden_btn = ttk.Button(buttons_frame, text="📂 Ver Ocultos", command=self.show_hidden_domains)
        show_hidden_btn.pack(side=tk.LEFT, padx=(0, 5))

        delete_btn = ttk.Button(buttons_frame, text="❌ Remover", command=self.delete_selected)
        delete_btn.pack(side=tk.LEFT)

        # Frame de estatísticas (painel visual)
        stats_frame = ttk.LabelFrame(self.frame, text="📊 Estatísticas", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Grid para estatísticas
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)

        # Total de domínios
        total_frame = tk.Frame(stats_container, bg='#e3f2fd', relief=tk.RAISED, bd=2)
        total_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        tk.Label(total_frame, text="Total", bg='#e3f2fd', font=('Arial', 9, 'bold')).pack()
        self.stats_total_label = tk.Label(total_frame, text="0", bg='#e3f2fd', font=('Arial', 16, 'bold'), fg='#1976d2')
        self.stats_total_label.pack()
        tk.Label(total_frame, text="domínios", bg='#e3f2fd', font=('Arial', 8)).pack()

        # Domínios OK
        ok_frame = tk.Frame(stats_container, bg='#e8f5e9', relief=tk.RAISED, bd=2)
        ok_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        tk.Label(ok_frame, text="✓ OK (200)", bg='#e8f5e9', font=('Arial', 9, 'bold')).pack()
        self.stats_ok_label = tk.Label(ok_frame, text="0", bg='#e8f5e9', font=('Arial', 16, 'bold'), fg='#2e7d32')
        self.stats_ok_label.pack()
        tk.Label(ok_frame, text="online", bg='#e8f5e9', font=('Arial', 8)).pack()

        # Domínios com erro
        error_frame = tk.Frame(stats_container, bg='#ffebee', relief=tk.RAISED, bd=2)
        error_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        tk.Label(error_frame, text="✗ Erros (4xx/5xx)", bg='#ffebee', font=('Arial', 9, 'bold')).pack()
        self.stats_error_label = tk.Label(error_frame, text="0", bg='#ffebee', font=('Arial', 16, 'bold'), fg='#c62828')
        self.stats_error_label.pack()
        tk.Label(error_frame, text="com problemas", bg='#ffebee', font=('Arial', 8)).pack()

        # Redirects
        redirect_frame = tk.Frame(stats_container, bg='#fff8e1', relief=tk.RAISED, bd=2)
        redirect_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        tk.Label(redirect_frame, text="↻ Redirects", bg='#fff8e1', font=('Arial', 9, 'bold')).pack()
        self.stats_redirect_label = tk.Label(redirect_frame, text="0", bg='#fff8e1', font=('Arial', 16, 'bold'), fg='#f57c00')
        self.stats_redirect_label.pack()
        tk.Label(redirect_frame, text="redirecionamentos", bg='#fff8e1', font=('Arial', 8)).pack()

        # Frame da tabela
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        columns = (
            'domain', 'status', 'cms', 'version', 'ip', 'country', 'city',
            'server', 'cloud', 'registrar', 'ssl', 'ga4', 'fb', 'checked'
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode='extended'
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Colunas
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('domain', width=200, anchor=tk.W)
        self.tree.column('status', width=60, anchor=tk.CENTER)
        self.tree.column('cms', width=100, anchor=tk.W)
        self.tree.column('version', width=80, anchor=tk.W)
        self.tree.column('ip', width=120, anchor=tk.W)
        self.tree.column('country', width=80, anchor=tk.W)
        self.tree.column('city', width=100, anchor=tk.W)
        self.tree.column('server', width=120, anchor=tk.W)
        self.tree.column('cloud', width=120, anchor=tk.W)
        self.tree.column('registrar', width=150, anchor=tk.W)
        self.tree.column('ssl', width=70, anchor=tk.CENTER)
        self.tree.column('ga4', width=50, anchor=tk.CENTER)
        self.tree.column('fb', width=50, anchor=tk.CENTER)
        self.tree.column('checked', width=100, anchor=tk.W)

        # Headings
        self.tree.heading('domain', text='Domínio', command=lambda: self.sort_column('domain'))
        self.tree.heading('status', text='Status', command=lambda: self.sort_column('status'))
        self.tree.heading('cms', text='CMS', command=lambda: self.sort_column('cms'))
        self.tree.heading('version', text='Versão', command=lambda: self.sort_column('version'))
        self.tree.heading('ip', text='IP', command=lambda: self.sort_column('ip'))
        self.tree.heading('country', text='País', command=lambda: self.sort_column('country'))
        self.tree.heading('city', text='Cidade', command=lambda: self.sort_column('city'))
        self.tree.heading('server', text='Servidor', command=lambda: self.sort_column('server'))
        self.tree.heading('cloud', text='Cloud', command=lambda: self.sort_column('cloud'))
        self.tree.heading('registrar', text='Registrar', command=lambda: self.sort_column('registrar'))
        self.tree.heading('ssl', text='SSL (dias)', command=lambda: self.sort_column('ssl'))
        self.tree.heading('ga4', text='GA4', command=lambda: self.sort_column('ga4'))
        self.tree.heading('fb', text='FB', command=lambda: self.sort_column('fb'))
        self.tree.heading('checked', text='Verificado', command=lambda: self.sort_column('checked'))

        # Tags para cores
        self.tree.tag_configure('ok', foreground='#28a745')
        self.tree.tag_configure('redirect', foreground='#ffc107')
        self.tree.tag_configure('error', foreground='#dc3545')
        self.tree.tag_configure('cms', foreground='#17a2b8')
        self.tree.tag_configure('placeholder', foreground='#888888')  # Cinza para não analisados

        # Layout
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Duplo clique desabilitado para não interferir com expansão de subdomínios
        # Para ver detalhes, use clique direito → "Ver Detalhes"
        # self.tree.bind('<Double-Button-1>', self.show_details)

        # Bind botão direito para menu de contexto
        self.tree.bind('<Button-3>', self.show_context_menu)

        # Bind seleção para atualizar observações
        self.tree.bind('<<TreeviewSelect>>', self.on_domain_selected)

        # Painel de observações
        notes_frame = ttk.LabelFrame(self.frame, text="📝 Observações", padding=10)
        notes_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Texto das observações
        self.notes_text = scrolledtext.ScrolledText(
            notes_frame,
            height=4,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        self.notes_text.pack(fill=tk.X, pady=(0, 5))

        # Botão salvar
        save_notes_btn = ttk.Button(
            notes_frame,
            text="💾 Salvar Observações",
            command=self.save_notes
        )
        save_notes_btn.pack(anchor=tk.E)

        # Variável para armazenar domínio atual
        self.current_selected_domain = None

    def import_domains(self):
        """Importa domínios de um arquivo TXT"""
        filepath = filedialog.askopenfilename(
            title="Importar domínios",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    current = self.domains_text.get('1.0', tk.END)
                    self.domains_text.delete('1.0', tk.END)
                    self.domains_text.insert('1.0', current + content)

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao importar arquivo: {e}")

    def analyze_domains(self):
        """Inicia a análise dos domínios"""
        if self.analyzing:
            messagebox.showwarning("Aviso", "Já existe uma análise em andamento!")
            return

        # Obtém domínios do texto
        text = self.domains_text.get('1.0', tk.END)
        domains = [line.strip() for line in text.split('\n') if line.strip()]

        if not domains:
            messagebox.showwarning("Aviso", "Por favor, insira pelo menos um domínio!")
            return

        # Remove duplicatas
        domains = list(set(domains))

        # Confirma
        msg = f"Analisar {len(domains)} domínio(s)?"
        if not messagebox.askyesno("Confirmar", msg):
            return

        # Inicia análise em thread separada
        self.analyzing = True
        self.analyze_btn.config(state='disabled')
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        thread = threading.Thread(
            target=self._analyze_thread,
            args=(domains,),
            daemon=True
        )
        thread.start()

    def _analyze_thread(self, domains):
        """Thread de análise de domínios"""
        try:
            logger.info(f"Iniciando análise de {len(domains)} domínio(s): {', '.join(domains)}")

            def progress_callback(current, total, domain):
                """Callback de progresso"""
                percentage = (current / total) * 100
                self.progress_var.set(percentage)
                self.progress_label.config(text=f"{current}/{total} - {domain}")

            # Coleta informações
            results = self.collector.collect_multiple(domains, progress_callback)

            logger.info(f"Análise concluída. {len(results)} resultado(s) obtido(s)")

            # Callback no thread principal
            self.frame.after(0, lambda: self._analysis_complete(results))

        except Exception as e:
            logger.error(f"Erro na análise: {e}", exc_info=True)
            self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro na análise: {e}"))
            self.frame.after(0, self._reset_analysis)

    def _analysis_complete(self, results):
        """Callback quando análise é concluída"""
        self._reset_analysis()

        # Callback para janela principal
        if self.on_complete_callback:
            self.on_complete_callback(results)

    def _reset_analysis(self):
        """Reseta estado de análise"""
        self.analyzing = False
        self.analyze_btn.config(state='normal')
        self.progress_frame.pack_forget()
        self.progress_var.set(0)
        self.progress_label.config(text="")

    def _get_root_domain(self, domain):
        """
        Extrai o domínio raiz de um domínio completo

        Args:
            domain: Nome do domínio (ex: blog.example.com)

        Returns:
            Domínio raiz (ex: example.com)
        """
        # Remove protocolo se houver
        domain = domain.replace('http://', '').replace('https://', '').split('/')[0]

        parts = domain.split('.')

        # Se tem 2 ou menos partes, já é o domínio raiz
        if len(parts) <= 2:
            return domain

        # Casos especiais de TLDs com duas partes (co.uk, com.br, etc)
        two_part_tlds = [
            'co.uk', 'com.br', 'com.au', 'co.nz', 'co.za',
            'gov.br', 'org.br', 'net.br', 'edu.br', 'mil.br',
            'med.br', 'jus.br', 'leg.br', 'mus.br', 'art.br',
            'eco.br', 'esp.br', 'ind.br', 'tmp.br', 'tur.br',
            'ac.uk', 'gov.uk', 'org.uk', 'me.uk', 'net.uk',
            'co.jp', 'or.jp', 'ne.jp', 'ac.jp', 'go.jp',
            'com.mx', 'gob.mx', 'org.mx', 'edu.mx', 'net.mx'
        ]

        # Verifica se termina com TLD de duas partes
        if len(parts) >= 3:
            potential_tld = '.'.join(parts[-2:])
            if potential_tld in two_part_tlds:
                # Retorna domínio + TLD de duas partes
                return '.'.join(parts[-3:]) if len(parts) >= 3 else domain

        # Caso padrão: últimas duas partes
        return '.'.join(parts[-2:])

    def _is_subdomain_of(self, subdomain, parent):
        """
        Verifica se um domínio é subdomínio de outro

        Args:
            subdomain: Possível subdomínio
            parent: Domínio pai

        Returns:
            True se subdomain é subdomínio de parent
        """
        # Limpa protocolos
        subdomain = subdomain.replace('http://', '').replace('https://', '').split('/')[0]
        parent = parent.replace('http://', '').replace('https://', '').split('/')[0]

        # Não pode ser subdomínio de si mesmo
        if subdomain == parent:
            return False

        # Verifica se termina com .parent
        return subdomain.endswith('.' + parent)

    def _insert_domains_hierarchically(self, domains, sort_key=None, sort_reverse=False):
        """
        Insere domínios organizados hierarquicamente

        Args:
            domains: Lista de domínios para inserir
            sort_key: Função de ordenação (opcional)
            sort_reverse: Se True, ordena em ordem reversa
        """
        # Organiza domínios em hierarquia
        # 1. Separa domínios principais e subdomínios
        root_domains = {}
        subdomains = {}

        for domain_data in domains:
            domain_name = domain_data.get('domain', '')
            root = self._get_root_domain(domain_name)

            # É o domínio raiz?
            if domain_name == root:
                root_domains[domain_name] = domain_data
            else:
                # É subdomínio
                if root not in subdomains:
                    subdomains[root] = []
                subdomains[root].append(domain_data)

        # 2. Define função de ordenação
        if sort_key is None:
            # Ordenação padrão: alfabética por nome do domínio
            sort_function = lambda items: sorted(items, key=lambda x: x.get('domain', '').lower())
        else:
            # Usa função de ordenação customizada
            sort_function = lambda items: sorted(items, key=sort_key, reverse=sort_reverse)

        # 3. Ordena e insere domínios raiz
        sorted_roots = sort_function(list(root_domains.values()))

        for root_data in sorted_roots:
            root_name = root_data.get('domain', '')

            # Insere domínio raiz
            parent_id = self._insert_domain(root_data, parent='')

            # Insere subdomínios analisados abaixo (também ordenados)
            if root_name in subdomains:
                sorted_subs = sort_function(subdomains[root_name])
                for subdomain_data in sorted_subs:
                    self._insert_domain(subdomain_data, parent=parent_id)

            # Insere subdomínios descobertos (mas não analisados) abaixo
            discovered_subs = root_data.get('discovered_subdomains', [])
            if discovered_subs:
                # Converte de JSON se necessário
                if isinstance(discovered_subs, str):
                    try:
                        import json
                        discovered_subs = json.loads(discovered_subs)
                    except:
                        discovered_subs = []

                # Cria lista de subdomínios já analisados para evitar duplicatas
                analyzed_subdomains = set()
                if root_name in subdomains:
                    analyzed_subdomains = set(s.get('domain') for s in subdomains[root_name])

                # Insere subdomínios descobertos que ainda não foram analisados
                for sub_name in sorted(discovered_subs):
                    if sub_name not in analyzed_subdomains:
                        # Cria entrada "placeholder" para subdomínio não analisado
                        placeholder_data = {
                            'domain': sub_name,
                            'status_code': None,
                            'cms_detected': '(não analisado)',
                            'last_checked': None
                        }
                        self._insert_domain(placeholder_data, parent=parent_id, is_placeholder=True)

        # 4. Insere subdomínios órfãos (cujo domínio raiz não está na lista)
        orphan_subdomains = []
        for root_name in subdomains.keys():
            if root_name not in root_domains:
                orphan_subdomains.extend(subdomains[root_name])

        # Ordena e insere órfãos
        sorted_orphans = sort_function(orphan_subdomains)
        for subdomain_data in sorted_orphans:
            self._insert_domain(subdomain_data, parent='')

    def update_statistics(self, domains):
        """
        Atualiza painel de estatísticas

        Args:
            domains: Lista de domínios
        """
        total = len(domains)
        ok_count = 0
        error_count = 0
        redirect_count = 0

        for domain in domains:
            status = domain.get('status_code')
            if status == 200:
                ok_count += 1
            elif status and 300 <= status < 400:
                redirect_count += 1
            elif status and status >= 400:
                error_count += 1

        # Atualiza labels
        self.stats_total_label.config(text=str(total))
        self.stats_ok_label.config(text=str(ok_count))
        self.stats_error_label.config(text=str(error_count))
        self.stats_redirect_label.config(text=str(redirect_count))

    def populate_table(self, domains):
        """
        Popula a tabela com dados organizados hierarquicamente

        Args:
            domains: Lista de domínios
        """
        # Desabilita redesenho para performance
        self.tree.configure(takefocus=False)

        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Armazena dados
        self.current_data = domains

        # Atualiza filtro de CMS
        cms_set = set()
        for domain in domains:
            cms = domain.get('cms_detected')
            if cms:
                cms_set.add(cms)

        cms_list = ["Todos"] + sorted(cms_set)
        self.cms_combo['values'] = cms_list

        # Insere domínios hierarquicamente
        self._insert_domains_hierarchically(domains)

        # Re-habilita redesenho
        self.tree.configure(takefocus=True)

        # Pré-carrega favicons em background (não bloqueia UI)
        self.favicon_cache.prefetch_favicons(domains)

        # Atualiza estatísticas
        self.update_statistics(domains)

    def _insert_domain(self, domain, parent='', is_placeholder=False):
        """
        Insere um domínio na tabela

        Args:
            domain: Dados do domínio
            parent: ID do item pai (para hierarquia)
            is_placeholder: Se True, é um subdomínio descoberto mas não analisado
        """
        # Formata dados
        status = domain.get('status_code', '-')
        cms = domain.get('cms_detected', '-') or '-'
        version = domain.get('cms_version', '-') or '-'
        ip = domain.get('ip_address', '-') or '-'
        country = domain.get('ip_country', '-') or '-'
        city = domain.get('ip_city', '-') or '-'
        server = domain.get('server', '-') or '-'
        cloud = domain.get('cloud_provider', '-') or '-'
        registrar = domain.get('registrar', '-') or '-'
        ssl = domain.get('ssl_expires_days', '-')
        ga4 = '✓' if domain.get('ga4_code') else '-'
        fb = '✓' if domain.get('fb_pixel') else '-'

        # Data de verificação
        last_checked = domain.get('last_checked', '-')
        if last_checked and last_checked != '-':
            try:
                dt = datetime.fromisoformat(str(last_checked))
                checked = dt.strftime('%d/%m %H:%M')
            except:
                checked = '-'
        else:
            checked = '-'

        # Define tag de cor
        tags = []
        if is_placeholder:
            tags.append('placeholder')
        elif status == 200:
            tags.append('ok')
        elif isinstance(status, int) and 300 <= status < 400:
            tags.append('redirect')
        elif isinstance(status, int) and status >= 400:
            tags.append('error')

        # Obtém favicon do cache (sem download para não travar)
        favicon = self.favicon_cache.get_favicon(domain.get('domain', ''), size=16, download=False)

        # Insere (usa parent se fornecido)
        item_id = self.tree.insert(
            parent,  # Parent node ('' para nível raiz)
            tk.END,
            image=favicon if favicon else '',
            values=(
                domain.get('domain', ''),
                status,
                cms,
                version,
                ip,
                country,
                city,
                server,
                cloud,
                registrar,
                ssl if ssl != '-' else '-',
                ga4,
                fb,
                checked
            ),
            tags=tags
        )

        return item_id

    def filter_table(self):
        """Filtra a tabela com base nos critérios"""
        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtém filtros
        search_term = self.search_var.get().lower()
        status_filter = self.status_filter.get()
        cms_filter = self.cms_filter.get()

        # Filtra dados
        filtered_domains = []
        for domain in self.current_data:
            # Filtro de busca
            if search_term:
                domain_name = domain.get('domain', '').lower()
                if search_term not in domain_name:
                    continue

            # Filtro de status
            if status_filter != "Todos":
                status = domain.get('status_code')

                # Verifica se status é válido
                if status is None or not isinstance(status, int):
                    # Se não tem status, só mostra se o filtro for "Erro"
                    if status_filter != "Erro (4xx/5xx)":
                        continue
                elif status_filter == "OK (200)" and status != 200:
                    continue
                elif status_filter == "Redirect (3xx)" and not (300 <= status < 400):
                    continue
                elif status_filter == "Erro (4xx/5xx)" and not (status >= 400):
                    continue

            # Filtro de CMS
            if cms_filter != "Todos":
                cms = domain.get('cms_detected')
                if cms != cms_filter:
                    continue

            filtered_domains.append(domain)

        # Insere hierarquicamente
        self._insert_domains_hierarchically(filtered_domains)

    def sort_column(self, column):
        """Ordena tabela por coluna com indicadores visuais"""
        # Alterna direção de ordenação
        self.sort_reverse[column] = not self.sort_reverse.get(column, False)
        reverse = self.sort_reverse[column]

        # Mapeia coluna para campo no dicionário
        column_map = {
            'domain': 'domain',
            'status': 'status_code',
            'cms': 'cms_detected',
            'version': 'cms_version',
            'ip': 'ip_address',
            'country': 'ip_country',
            'city': 'ip_city',
            'server': 'server',
            'cloud': 'cloud_provider',
            'registrar': 'registrar',
            'ssl': 'ssl_expires_days',
            'ga4': 'ga4_code',
            'fb': 'fb_pixel',
            'checked': 'last_checked'
        }

        # Nomes amigáveis dos headers
        header_names = {
            'domain': 'Domínio',
            'status': 'Status',
            'cms': 'CMS',
            'version': 'Versão',
            'ip': 'IP',
            'country': 'País',
            'city': 'Cidade',
            'server': 'Servidor',
            'cloud': 'Cloud',
            'registrar': 'Registrar',
            'ssl': 'SSL (dias)',
            'ga4': 'GA4',
            'fb': 'FB',
            'checked': 'Verificado'
        }

        field = column_map.get(column)
        if not field:
            return

        # Ordena dados
        try:
            # Função de chave de ordenação que trata números e strings corretamente
            def sort_key(item):
                value = item.get(field)

                # Valores None vão para o final
                if value is None:
                    return (1, '')

                # Para campos numéricos, converte para número
                if field in ['status_code', 'ssl_expires_days']:
                    try:
                        return (0, int(value))
                    except (ValueError, TypeError):
                        return (1, str(value))

                # Para strings, normaliza
                return (0, str(value).lower())

            # Atualiza indicadores visuais nos headers
            for col in column_map.keys():
                header_text = header_names.get(col, col)
                if col == column:
                    # Adiciona seta indicando direção
                    indicator = ' ▼' if reverse else ' ▲'
                    self.tree.heading(col, text=header_text + indicator)
                else:
                    # Remove seta das outras colunas
                    self.tree.heading(col, text=header_text)

            # Atualiza coluna atualmente ordenada
            self.current_sort_column = column

            # Atualiza tabela
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insere hierarquicamente com ordenação
            self._insert_domains_hierarchically(self.current_data, sort_key=sort_key, sort_reverse=reverse)

        except Exception as e:
            logger.error(f"Erro ao ordenar por {column}: {e}")

    def on_domain_selected(self, event):
        """Atualiza o painel de observações quando um domínio é selecionado"""
        selection = self.tree.selection()
        if not selection:
            self.notes_text.delete('1.0', tk.END)
            self.current_selected_domain = None
            return

        # Pega o primeiro item selecionado
        item = selection[0]
        values = self.tree.item(item, 'values')

        if not values:
            return

        domain_name = values[0]
        self.current_selected_domain = domain_name

        # Busca as observações do banco
        try:
            domain_data = self.db.get_domain(domain_name)
            if domain_data:
                notes = domain_data.get('observations', '') or ''
                self.notes_text.delete('1.0', tk.END)
                self.notes_text.insert('1.0', notes)
        except Exception as e:
            logger.error(f"Erro ao carregar observações: {e}")

    def save_notes(self):
        """Salva as observações do domínio atual"""
        if not self.current_selected_domain:
            return

        try:
            notes = self.notes_text.get('1.0', tk.END).strip()

            # Atualiza no banco
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE domains SET observations = ? WHERE domain = ?',
                (notes, self.current_selected_domain)
            )
            conn.commit()
            conn.close()

            logger.info(f"Observações salvas para {self.current_selected_domain}")

        except Exception as e:
            logger.error(f"Erro ao salvar observações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar observações: {e}")

    def show_details(self, event):
        """Mostra detalhes de um domínio"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        domain_name = item['values'][0]

        # Busca dados completos
        domain_data = None
        for d in self.current_data:
            if d.get('domain') == domain_name:
                domain_data = d
                break

        if not domain_data:
            return

        # Cria janela de detalhes
        details_window = tk.Toplevel(self.frame)
        details_window.title(f"Detalhes - {domain_name}")
        details_window.geometry("800x600")
        details_window.configure(bg='#1a1a2e')

        # Notebook para abas
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Aba de informações gerais
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Informações Gerais")

        info_text = scrolledtext.ScrolledText(
            info_frame,
            bg='#16213e',
            fg='#eee',
            font=('Consolas', 10)
        )
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_content = f"""
DOMÍNIO: {domain_data.get('domain', '-')}
{'='*60}

STATUS HTTP: {domain_data.get('status_code', '-')}
SERVIDOR: {domain_data.get('server', '-')}
CLOUD PROVIDER: {domain_data.get('cloud_provider', '-')}

CMS DETECTADO: {domain_data.get('cms_detected', '-')}
VERSÃO CMS: {domain_data.get('cms_version', '-')}

IP ADDRESS: {domain_data.get('ip_address', '-')}
DNS SERVERS: {', '.join(domain_data.get('dns_servers', []) or [])}

REGISTRAR: {domain_data.get('registrar', '-')}
WHOIS CRIADO: {domain_data.get('whois_created', '-')}
WHOIS EXPIRA: {domain_data.get('whois_expires', '-')}

SSL EXPIRA (DIAS): {domain_data.get('ssl_expires_days', '-')}

GOOGLE ANALYTICS 4: {domain_data.get('ga4_code', '-')}
FACEBOOK PIXEL: {domain_data.get('fb_pixel', '-')}

SPAM BLACKLIST: {'Sim' if domain_data.get('is_spam') else 'Não'}

OBSERVAÇÕES: {domain_data.get('observations', '-')}

ÚLTIMA VERIFICAÇÃO: {domain_data.get('last_checked', '-')}
"""

        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')

        # Aba de headers HTTP
        headers_frame = ttk.Frame(notebook)
        notebook.add(headers_frame, text="HTTP Headers")

        headers_text = scrolledtext.ScrolledText(
            headers_frame,
            bg='#16213e',
            fg='#eee',
            font=('Consolas', 10)
        )
        headers_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        raw_headers = domain_data.get('raw_headers', {})

        # Converte de string JSON se necessário
        if isinstance(raw_headers, str):
            try:
                import json
                raw_headers = json.loads(raw_headers)
            except:
                raw_headers = {}

        if raw_headers:
            for key, value in raw_headers.items():
                headers_text.insert(tk.END, f"{key}: {value}\n")
        else:
            headers_text.insert(tk.END, "Nenhum header disponível")

        headers_text.config(state='disabled')

    def show_context_menu(self, event):
        """Mostra menu de contexto"""
        # Identifica item clicado
        item = self.tree.identify_row(event.y)
        if not item:
            return

        # Seleciona o item
        self.tree.selection_set(item)

        # Obtém dados do item
        values = self.tree.item(item, 'values')
        if not values:
            return

        domain_name = values[0]
        cms = values[2]

        # Cria menu
        menu = tk.Menu(self.tree, tearoff=0)

        # Verifica se é um placeholder (não analisado)
        is_placeholder = cms == '(não analisado)'

        if is_placeholder:
            # Opções para subdomínios não analisados
            menu.add_command(
                label=f"🔍 Analisar '{domain_name}'",
                command=lambda: self._analyze_single_domain(domain_name)
            )
            menu.add_separator()

        # Opções comuns
        menu.add_command(
            label="👁️ Ver Detalhes",
            command=lambda: self.show_details(event)
        )

        menu.add_separator()

        menu.add_command(
            label="🔄 Atualizar",
            command=lambda: self._refresh_single_domain(domain_name)
        )

        menu.add_command(
            label="🙈 Ocultar",
            command=lambda: self._hide_single_domain(domain_name)
        )

        menu.add_command(
            label="❌ Remover",
            command=lambda: self._delete_single_domain(domain_name)
        )

        # Mostra menu
        menu.post(event.x_root, event.y_root)

    def _analyze_single_domain(self, domain):
        """
        Analisa um único domínio (útil para placeholders)

        Args:
            domain: Nome do domínio
        """
        if messagebox.askyesno("Confirmar", f"Analisar domínio '{domain}'?"):
            # Adiciona ao campo de entrada
            self.domains_text.delete('1.0', tk.END)
            self.domains_text.insert('1.0', domain)

            # Inicia análise
            self.analyze_domains()

    def _refresh_single_domain(self, domain):
        """
        Atualiza um único domínio

        Args:
            domain: Nome do domínio
        """
        self.domains_text.delete('1.0', tk.END)
        self.domains_text.insert('1.0', domain)
        self.analyze_domains()

    def _hide_single_domain(self, domain):
        """
        Oculta um único domínio

        Args:
            domain: Nome do domínio
        """
        if messagebox.askyesno("Confirmar", f"Ocultar domínio '{domain}'?"):
            try:
                self.db.hide_domain(domain)
                self.load_domains()
                messagebox.showinfo("Sucesso", f"Domínio '{domain}' ocultado")
            except Exception as e:
                logger.error(f"Erro ao ocultar domínio: {e}")
                messagebox.showerror("Erro", f"Erro ao ocultar domínio: {e}")

    def _delete_single_domain(self, domain):
        """
        Remove um único domínio

        Args:
            domain: Nome do domínio
        """
        if messagebox.askyesno("ATENÇÃO", f"Remover permanentemente '{domain}'?\n\nEsta ação NÃO pode ser desfeita!"):
            try:
                self.db.delete_domain(domain)
                self.load_domains()
                messagebox.showinfo("Sucesso", f"Domínio '{domain}' removido")
            except Exception as e:
                logger.error(f"Erro ao remover domínio: {e}")
                messagebox.showerror("Erro", f"Erro ao remover domínio: {e}")

    def show_issues_only(self):
        """Mostra apenas domínios com problemas, ordenados por prioridade"""
        try:
            # Busca domínios com problemas
            issues = self.db.get_domains_with_issues()

            if not issues:
                messagebox.showinfo(
                    "Problemas",
                    "Nenhum domínio com problemas encontrado!\n\n"
                    "✓ Todos os domínios estão funcionando corretamente."
                )
                return

            # Popula tabela com domínios problemáticos
            self.populate_table(issues)

            # Conta por prioridade
            priority_counts = {}
            for domain in issues:
                priority = domain.get('issue_priority', 'DESCONHECIDO')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            # Monta mensagem
            msg_parts = [f"Encontrados {len(issues)} domínio(s) com problemas:\n"]

            if priority_counts.get('CRÍTICO'):
                msg_parts.append(f"🔴 {priority_counts['CRÍTICO']} CRÍTICO(S)")
            if priority_counts.get('MÉDIO'):
                msg_parts.append(f"🟡 {priority_counts['MÉDIO']} MÉDIO(S)")
            if priority_counts.get('AVISO'):
                msg_parts.append(f"🟠 {priority_counts['AVISO']} AVISO(S)")

            messagebox.showinfo("Problemas Detectados", "\n".join(msg_parts))

        except Exception as e:
            logger.error(f"Erro ao buscar domínios com problemas: {e}")
            messagebox.showerror("Erro", f"Erro ao buscar problemas: {e}")

    def export_data(self):
        """Exporta dados da tabela"""
        if not self.current_data:
            messagebox.showwarning("Aviso", "Não há dados para exportar!")
            return

        # Diálogo de escolha de formato
        from src.reports.exporter import DataExporter

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("HTML files", "*.html")
            ]
        )

        if not filepath:
            return

        try:
            exporter = DataExporter()

            if filepath.endswith('.csv'):
                success = exporter.export_csv(self.current_data, filepath)
            elif filepath.endswith('.json'):
                success = exporter.export_json(self.current_data, filepath)
            elif filepath.endswith('.html'):
                success = exporter.export_html(self.current_data, filepath)
            else:
                messagebox.showerror("Erro", "Formato não suportado!")
                return

            if success:
                messagebox.showinfo("Sucesso", "Dados exportados com sucesso!")
            else:
                messagebox.showerror("Erro", "Erro ao exportar dados!")

        except Exception as e:
            logger.error(f"Erro ao exportar: {e}")
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    def hide_selected(self):
        """Oculta os domínios selecionados"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione pelo menos um domínio para ocultar!")
            return

        # Confirma ação
        count = len(selection)
        if not messagebox.askyesno(
            "Confirmar",
            f"Deseja ocultar {count} domínio(s) selecionado(s)?\n\n"
            "Os domínios ocultos não aparecerão mais na lista, mas podem ser restaurados usando 'Ver Ocultos'."
        ):
            return

        try:
            # Oculta cada domínio
            for item in selection:
                values = self.tree.item(item)['values']
                domain_name = values[0]

                # Oculta no banco
                self.db.hide_domain(domain_name)

            # Atualiza UI
            self.load_domains()

            messagebox.showinfo("Sucesso", f"{count} domínio(s) ocultado(s) com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao ocultar domínios: {e}")
            messagebox.showerror("Erro", f"Erro ao ocultar domínios: {e}")

    def show_hidden_domains(self):
        """Mostra janela com domínios ocultos"""
        try:
            hidden = self.db.get_hidden_domains()

            if not hidden:
                messagebox.showinfo("Domínios Ocultos", "Nenhum domínio oculto encontrado!")
                return

            # Cria janela de diálogo
            dialog = tk.Toplevel(self.frame)
            dialog.title("Domínios Ocultos")
            dialog.geometry("800x600")
            dialog.configure(bg='#1a1a2e')

            # Header
            header = ttk.Label(
                dialog,
                text=f"📂 Domínios Ocultos ({len(hidden)})",
                font=('Arial', 14, 'bold')
            )
            header.pack(pady=10)

            # Frame da lista
            list_frame = ttk.Frame(dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

            # Scrollbars
            vsb = ttk.Scrollbar(list_frame, orient="vertical")
            hsb = ttk.Scrollbar(list_frame, orient="horizontal")

            # Treeview
            columns = ('domain', 'status', 'last_checked')
            tree = ttk.Treeview(
                list_frame,
                columns=columns,
                show='tree headings',
                yscrollcommand=vsb.set,
                xscrollcommand=hsb.set,
                selectmode='extended'
            )

            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)

            # Configurar colunas
            tree.column('#0', width=0, stretch=False)
            tree.heading('#0', text='')

            tree.column('domain', width=400, anchor='w')
            tree.heading('domain', text='Domínio')

            tree.column('status', width=100, anchor='center')
            tree.heading('status', text='Status')

            tree.column('last_checked', width=200, anchor='center')
            tree.heading('last_checked', text='Última Verificação')

            # Popula lista
            for domain in hidden:
                status = domain.get('status_code', '-')
                last_checked = domain.get('last_checked', '-')

                if last_checked and last_checked != '-':
                    try:
                        dt = datetime.fromisoformat(str(last_checked))
                        last_checked = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass

                tree.insert('', tk.END, values=(
                    domain.get('domain', ''),
                    status,
                    last_checked
                ))

            # Grid
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')

            list_frame.grid_rowconfigure(0, weight=1)
            list_frame.grid_columnconfigure(0, weight=1)

            # Botões
            buttons_frame = ttk.Frame(dialog)
            buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            def restore_selected():
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning("Aviso", "Selecione domínios para restaurar!")
                    return

                count = len(selection)
                if messagebox.askyesno("Confirmar", f"Restaurar {count} domínio(s)?"):
                    for item in selection:
                        values = tree.item(item)['values']
                        domain_name = values[0]
                        self.db.unhide_domain(domain_name)
                        tree.delete(item)

                    self.load_domains()  # Atualiza lista principal
                    messagebox.showinfo("Sucesso", f"{count} domínio(s) restaurado(s)!")

                    # Fecha se não sobrou nada
                    if not tree.get_children():
                        dialog.destroy()

            def delete_selected():
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning("Aviso", "Selecione domínios para remover!")
                    return

                count = len(selection)
                if messagebox.askyesno(
                    "ATENÇÃO",
                    f"Tem certeza que deseja REMOVER PERMANENTEMENTE {count} domínio(s)?\n\n"
                    "Esta ação NÃO pode ser desfeita!"
                ):
                    for item in selection:
                        values = tree.item(item)['values']
                        domain_name = values[0]
                        self.db.delete_domain(domain_name)
                        tree.delete(item)

                    messagebox.showinfo("Sucesso", f"{count} domínio(s) removido(s)!")

                    # Fecha se não sobrou nada
                    if not tree.get_children():
                        dialog.destroy()

            restore_btn = ttk.Button(buttons_frame, text="✅ Restaurar", command=restore_selected)
            restore_btn.pack(side=tk.LEFT, padx=5)

            delete_btn = ttk.Button(buttons_frame, text="❌ Remover", command=delete_selected)
            delete_btn.pack(side=tk.LEFT, padx=5)

            close_btn = ttk.Button(buttons_frame, text="Fechar", command=dialog.destroy)
            close_btn.pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            logger.error(f"Erro ao exibir domínios ocultos: {e}")
            messagebox.showerror("Erro", f"Erro ao exibir domínios ocultos: {e}")

    def load_domains(self):
        """Recarrega domínios do banco"""
        domains = self.db.get_all_domains(include_hidden=False)
        self.populate_table(domains)

    def refresh_selected(self):
        """Reanalisar domínios selecionados"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione pelo menos um domínio!")
            return

        # Obtém domínios selecionados
        domains = []
        for item in selection:
            values = self.tree.item(item)['values']
            domains.append(values[0])

        # Limpa campo de entrada e adiciona domínios
        self.domains_text.delete('1.0', tk.END)
        self.domains_text.insert('1.0', '\n'.join(domains))

        # Inicia análise
        self.analyze_domains()

    def delete_selected(self):
        """Remove domínios selecionados"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione pelo menos um domínio!")
            return

        if not messagebox.askyesno("Confirmar", "Deseja remover os domínios selecionados?"):
            return

        # Remove do banco
        for item in selection:
            values = self.tree.item(item)['values']
            domain = values[0]

            try:
                self.db.delete_domain(domain)
                self.tree.delete(item)

                # Remove dos dados
                self.current_data = [d for d in self.current_data if d.get('domain') != domain]

            except Exception as e:
                logger.error(f"Erro ao remover domínio {domain}: {e}")

        messagebox.showinfo("Sucesso", "Domínios removidos com sucesso!")
