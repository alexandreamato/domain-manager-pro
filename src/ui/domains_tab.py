"""Aba de gerenciamento de domínios"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import logging
from datetime import datetime

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
        self.cms_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.cms_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_table())

        # Botões de ação
        issues_btn = ttk.Button(tools_frame, text="⚠️ Problemas", command=self.show_issues_only)
        issues_btn.pack(side=tk.LEFT, padx=(0, 5))

        export_btn = ttk.Button(tools_frame, text="💾 Exportar", command=self.export_data)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))

        refresh_btn = ttk.Button(tools_frame, text="🔄 Atualizar", command=self.refresh_selected)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        delete_btn = ttk.Button(tools_frame, text="❌ Remover", command=self.delete_selected)
        delete_btn.pack(side=tk.LEFT)

        # Frame da tabela
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        columns = (
            'domain', 'status', 'cms', 'version', 'ip', 'server',
            'cloud', 'registrar', 'ssl', 'ga4', 'fb', 'checked'
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

        # Layout
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind duplo clique para ver detalhes
        self.tree.bind('<Double-Button-1>', self.show_details)

        # Bind botão direito para menu de contexto
        self.tree.bind('<Button-3>', self.show_context_menu)

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

                messagebox.showinfo("Sucesso", "Domínios importados com sucesso!")

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
            def progress_callback(current, total, domain):
                """Callback de progresso"""
                percentage = (current / total) * 100
                self.progress_var.set(percentage)
                self.progress_label.config(text=f"{current}/{total} - {domain}")

            # Coleta informações
            results = self.collector.collect_multiple(domains, progress_callback)

            # Callback no thread principal
            self.frame.after(0, lambda: self._analysis_complete(results))

        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro na análise: {e}"))
            self.frame.after(0, self._reset_analysis)

    def _analysis_complete(self, results):
        """Callback quando análise é concluída"""
        self._reset_analysis()

        # Callback para janela principal
        if self.on_complete_callback:
            self.on_complete_callback(results)

        messagebox.showinfo("Sucesso", f"{len(results)} domínio(s) analisado(s) com sucesso!")

    def _reset_analysis(self):
        """Reseta estado de análise"""
        self.analyzing = False
        self.analyze_btn.config(state='normal')
        self.progress_frame.pack_forget()
        self.progress_var.set(0)
        self.progress_label.config(text="")

    def populate_table(self, domains):
        """
        Popula a tabela com dados

        Args:
            domains: Lista de domínios
        """
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

        # Popula
        for domain in domains:
            self._insert_domain(domain)

    def _insert_domain(self, domain):
        """Insere um domínio na tabela"""
        # Formata dados
        status = domain.get('status_code', '-')
        cms = domain.get('cms_detected', '-') or '-'
        version = domain.get('cms_version', '-') or '-'
        ip = domain.get('ip_address', '-') or '-'
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
        if status == 200:
            tags.append('ok')
        elif isinstance(status, int) and 300 <= status < 400:
            tags.append('redirect')
        elif isinstance(status, int) and status >= 400:
            tags.append('error')

        # Insere
        self.tree.insert(
            '',
            tk.END,
            values=(
                domain.get('domain', ''),
                status,
                cms,
                version,
                ip,
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
        for domain in self.current_data:
            # Filtro de busca
            if search_term:
                domain_name = domain.get('domain', '').lower()
                if search_term not in domain_name:
                    continue

            # Filtro de status
            if status_filter != "Todos":
                status = domain.get('status_code')
                if status_filter == "OK (200)" and status != 200:
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

            # Insere
            self._insert_domain(domain)

    def sort_column(self, column):
        """Ordena tabela por coluna"""
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
            'server': 'server',
            'cloud': 'cloud_provider',
            'registrar': 'registrar',
            'ssl': 'ssl_expires_days',
            'ga4': 'ga4_code',
            'fb': 'fb_pixel',
            'checked': 'last_checked'
        }

        field = column_map.get(column)
        if not field:
            return

        # Ordena dados
        try:
            self.current_data.sort(
                key=lambda x: (x.get(field) is None, x.get(field) or ''),
                reverse=reverse
            )

            # Atualiza tabela
            for item in self.tree.get_children():
                self.tree.delete(item)

            for domain in self.current_data:
                self._insert_domain(domain)

        except Exception as e:
            logger.error(f"Erro ao ordenar por {column}: {e}")

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
        # TODO: Implementar menu de contexto
        pass

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
