"""Aba de Dashboard de SEO"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from src.utils.favicon_cache import FaviconCache

logger = logging.getLogger(__name__)


class SEOTab:
    """Aba de Dashboard de SEO"""

    def __init__(self, parent, db):
        """
        Inicializa a aba de SEO

        Args:
            parent: Widget pai
            db: DatabaseManager
        """
        self.parent = parent
        self.db = db

        # Frame principal
        self.frame = ttk.Frame(parent)

        # Dados atuais
        self.current_data = []
        self.sort_reverse = {}

        # Cache de favicons
        self.favicon_cache = FaviconCache()

        # Criar interface
        self.create_widgets()

    def create_widgets(self):
        """Cria os widgets da aba"""
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        title = ttk.Label(
            header_frame,
            text="📊 Dashboard de SEO",
            font=('Arial', 16, 'bold')
        )
        title.pack(side=tk.LEFT)

        # Botão de atualizar
        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Atualizar",
            command=self.refresh_data
        )
        refresh_btn.pack(side=tk.RIGHT)

        # Info sobre coleta de SEO
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        info_label = ttk.Label(
            info_frame,
            text="💡 Dica: Para ver Domain Authority, Page Authority e mais métricas, ative 'Coletar SEO da Web' nas Configurações",
            font=('Arial', 9),
            foreground='#aaa'
        )
        info_label.pack()

        # Frame de filtros
        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(filter_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_table())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Filtro por qualidade de SEO
        ttk.Label(filter_frame, text="Qualidade SEO:").pack(side=tk.LEFT, padx=(0, 5))
        self.quality_filter = tk.StringVar(value="Todos")
        quality_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.quality_filter,
            values=["Todos", "Excelente (>80)", "Bom (60-80)", "Regular (40-60)", "Ruim (<40)"],
            state='readonly',
            width=20
        )
        quality_combo.pack(side=tk.LEFT)
        quality_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_table())

        # Frame da tabela
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview com informações de SEO
        columns = (
            'domain', 'seo_score', 'domain_authority', 'page_authority',
            'global_rank', 'backlinks', 'domain_age', 'hosting', 'ssl_days'
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

        # Configurar colunas
        self.tree.column('#0', width=0, stretch=False)
        self.tree.heading('#0', text='')

        column_config = {
            'domain': ('Domínio', 250),
            'seo_score': ('SEO Score', 100),
            'domain_authority': ('Domain Authority', 120),
            'page_authority': ('Page Authority', 120),
            'global_rank': ('Ranking Global', 120),
            'backlinks': ('Backlinks', 100),
            'domain_age': ('Idade (dias)', 100),
            'hosting': ('Hosting', 150),
            'ssl_days': ('SSL (dias)', 100)
        }

        for col, (text, width) in column_config.items():
            self.tree.column(col, width=width, anchor='center' if col != 'domain' else 'w')
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_column(c))

        # Tags de cores
        self.tree.tag_configure('excellent', background='#0f4d0f', foreground='white')
        self.tree.tag_configure('good', background='#1a5f1a', foreground='white')
        self.tree.tag_configure('average', background='#5f5f1a', foreground='white')
        self.tree.tag_configure('poor', background='#5f1a1a', foreground='white')

        # Grid
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Bind duplo clique
        self.tree.bind('<Double-1>', self.show_details)

        # Bind seleção para atualizar painel de info
        self.tree.bind('<<TreeviewSelect>>', self.update_info_panel)

        # Frame de informações do domínio selecionado
        info_frame = ttk.LabelFrame(self.frame, text="📌 Informações do Domínio Selecionado", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Grid de informações
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)

        # Labels de informação
        self.info_labels = {}

        # Linha 1
        row = 0
        self._create_info_label(info_grid, "Tamanho:", "domain_length", row, 0)
        self._create_info_label(info_grid, "Facebook Pixel:", "fb_pixel", row, 2)
        self._create_info_label(info_grid, "Google Analytics:", "ga4", row, 4)

        # Linha 2
        row = 1
        self._create_info_label(info_grid, "Redirects:", "redirects", row, 0)
        self._create_info_label(info_grid, "Custo Anual:", "annual_cost", row, 2)
        self._create_info_label(info_grid, "Valor Estimado:", "domain_value", row, 4)

        # Frame de estatísticas
        stats_frame = ttk.Frame(self.frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.stats_label = ttk.Label(
            stats_frame,
            text="Carregue os dados para ver estatísticas",
            font=('Arial', 10)
        )
        self.stats_label.pack()

    def _create_info_label(self, parent, label_text, key, row, col):
        """Cria um par label/valor no grid de informações"""
        label_frame = ttk.Frame(parent)
        label_frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')

        ttk.Label(label_frame, text=label_text, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))

        value_label = ttk.Label(label_frame, text="-", font=('Arial', 9))
        value_label.pack(side=tk.LEFT)

        self.info_labels[key] = value_label

    def update_info_panel(self, event=None):
        """Atualiza o painel de informações com o domínio selecionado"""
        selection = self.tree.selection()

        if not selection:
            # Limpa info
            for label in self.info_labels.values():
                label.config(text="-", foreground='#aaa')
            return

        # Obtém dados do primeiro item selecionado
        item = selection[0]
        values = self.tree.item(item)['values']
        domain_name = values[0]

        # Busca dados completos
        domain_data = next((d for d in self.current_data if d['domain'] == domain_name), None)

        if not domain_data:
            return

        # Tamanho do domínio (número de caracteres)
        domain_length = len(domain_name)
        self.info_labels['domain_length'].config(
            text=f"{domain_length} caracteres",
            foreground='white'
        )

        # Facebook Pixel
        fb_pixel = domain_data.get('fb_pixel')
        if fb_pixel:
            self.info_labels['fb_pixel'].config(text="✓ Sim", foreground='#28a745')
        else:
            self.info_labels['fb_pixel'].config(text="✗ Não", foreground='#dc3545')

        # Google Analytics
        ga4 = domain_data.get('ga4_code')
        if ga4:
            self.info_labels['ga4'].config(text="✓ Sim", foreground='#28a745')
        else:
            self.info_labels['ga4'].config(text="✗ Não", foreground='#dc3545')

        # Redirects
        redirect_count = domain_data.get('redirect_count', 0)
        if redirect_count == 0:
            self.info_labels['redirects'].config(text="Nenhum", foreground='#28a745')
        elif redirect_count <= 2:
            self.info_labels['redirects'].config(text=f"{redirect_count} redirect(s)", foreground='#ffc107')
        else:
            self.info_labels['redirects'].config(text=f"{redirect_count} redirect(s)", foreground='#dc3545')

        # Custo anual estimado
        annual_cost = domain_data.get('estimated_annual_cost')
        if annual_cost:
            self.info_labels['annual_cost'].config(
                text=f"US$ {annual_cost}/ano",
                foreground='white'
            )
        else:
            self.info_labels['annual_cost'].config(text="-", foreground='#aaa')

        # Valor estimado do domínio
        domain_value = domain_data.get('estimated_domain_value')
        if domain_value:
            self.info_labels['domain_value'].config(
                text=f"US$ {domain_value:,}",
                foreground='white'
            )
        else:
            self.info_labels['domain_value'].config(text="-", foreground='#aaa')

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
        two_part_tlds = ['co.uk', 'com.br', 'com.au', 'co.nz', 'co.za', 'gov.br', 'org.br']

        # Verifica se termina com TLD de duas partes
        if len(parts) >= 3:
            potential_tld = '.'.join(parts[-2:])
            if potential_tld in two_part_tlds:
                # Retorna domínio + TLD de duas partes
                return '.'.join(parts[-3:]) if len(parts) >= 3 else domain

        # Caso padrão: últimas duas partes
        return '.'.join(parts[-2:])

    def _insert_domains_hierarchically(self, domains):
        """
        Insere domínios organizados hierarquicamente

        Args:
            domains: Lista de domínios para inserir
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

        # 2. Insere domínios raiz primeiro, depois seus subdomínios
        for root_name in sorted(root_domains.keys()):
            root_data = root_domains[root_name]

            # Insere domínio raiz
            parent_id = self._insert_domain(root_data, parent='')

            # Insere subdomínios abaixo
            if root_name in subdomains:
                for subdomain_data in sorted(subdomains[root_name], key=lambda x: x.get('domain', '')):
                    self._insert_domain(subdomain_data, parent=parent_id)

        # 3. Insere subdomínios órfãos (cujo domínio raiz não está na lista)
        for root_name in sorted(subdomains.keys()):
            if root_name not in root_domains:
                for subdomain_data in sorted(subdomains[root_name], key=lambda x: x.get('domain', '')):
                    self._insert_domain(subdomain_data, parent='')

    def populate_table(self, domains):
        """
        Popula a tabela com dados de SEO

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

        # Insere domínios hierarquicamente
        self._insert_domains_hierarchically(domains)

        # Re-habilita redesenho
        self.tree.configure(takefocus=True)

        # Pré-carrega favicons em background (não bloqueia UI)
        self.favicon_cache.prefetch_favicons(domains)

        # Atualiza estatísticas
        self._update_stats(domains)

    def _insert_domain(self, domain, parent=''):
        """Insere um domínio na tabela"""
        # Formata dados
        domain_name = domain.get('domain', '')
        seo_score = domain.get('seo_score', '-')
        domain_authority = domain.get('domain_authority', '-')
        page_authority = domain.get('page_authority', '-')
        global_rank = domain.get('global_rank', '-')
        backlinks = domain.get('backlinks_count', '-')
        domain_age = domain.get('domain_age_days', '-')
        hosting = domain.get('hosting_provider', '-') or '-'
        ssl_days = domain.get('ssl_expires_days', '-')

        # Formata números
        if isinstance(seo_score, (int, float)):
            seo_score = f"{seo_score:.1f}"
        if isinstance(domain_authority, (int, float)):
            domain_authority = f"{domain_authority:.0f}"
        if isinstance(page_authority, (int, float)):
            page_authority = f"{page_authority:.0f}"
        if isinstance(global_rank, int) and global_rank > 0:
            global_rank = f"#{global_rank:,}"
        if isinstance(backlinks, int):
            backlinks = f"{backlinks:,}"
        if isinstance(domain_age, int):
            domain_age = f"{domain_age:,}"

        # Define tag de cor baseado no SEO score
        tags = []
        score_val = domain.get('seo_score')
        if isinstance(score_val, (int, float)):
            if score_val >= 80:
                tags.append('excellent')
            elif score_val >= 60:
                tags.append('good')
            elif score_val >= 40:
                tags.append('average')
            else:
                tags.append('poor')

        # Obtém favicon do cache (sem download para não travar)
        favicon = self.favicon_cache.get_favicon(domain_name, size=16, download=False)

        # Insere (usa parent se fornecido)
        item_id = self.tree.insert(
            parent,  # Parent node ('' para nível raiz)
            tk.END,
            image=favicon if favicon else '',
            values=(
                domain_name,
                seo_score,
                domain_authority,
                page_authority,
                global_rank,
                backlinks,
                domain_age,
                hosting,
                ssl_days
            ),
            tags=tags
        )

        return item_id

    def filter_table(self):
        """Filtra a tabela"""
        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtém filtros
        search_term = self.search_var.get().lower()
        quality_filter = self.quality_filter.get()

        # Filtra dados
        filtered = []
        for domain in self.current_data:
            # Filtro de busca
            if search_term:
                domain_name = domain.get('domain', '').lower()
                if search_term not in domain_name:
                    continue

            # Filtro de qualidade (só aplica se tiver seo_score)
            if quality_filter != "Todos":
                seo_score = domain.get('seo_score')
                # Se não tem seo_score, não mostra quando filtro ativo
                if seo_score is None:
                    continue

                if quality_filter == "Excelente (>80)" and seo_score <= 80:
                    continue
                elif quality_filter == "Bom (60-80)" and not (60 <= seo_score <= 80):
                    continue
                elif quality_filter == "Regular (40-60)" and not (40 <= seo_score < 60):
                    continue
                elif quality_filter == "Ruim (<40)" and seo_score >= 40:
                    continue

            filtered.append(domain)

        # Insere hierarquicamente
        self._insert_domains_hierarchically(filtered)

        # Atualiza estatísticas
        self._update_stats(filtered)

    def _update_stats(self, domains):
        """Atualiza estatísticas"""
        if not domains:
            self.stats_label.config(text="Nenhum domínio com dados de SEO")
            return

        # Calcula estatísticas
        total = len(domains)

        scores = [d.get('seo_score', 0) for d in domains if d.get('seo_score') is not None]
        avg_seo = sum(scores) / len(scores) if scores else 0

        excellent = sum(1 for s in scores if s >= 80)
        good = sum(1 for s in scores if 60 <= s < 80)
        average = sum(1 for s in scores if 40 <= s < 60)
        poor = sum(1 for s in scores if s < 40)

        # Monta texto
        text = f"Total: {total} domínios | SEO Médio: {avg_seo:.1f} | "
        text += f"🟢 {excellent} excelente | 🟡 {good} bom | 🟠 {average} regular | 🔴 {poor} ruim"

        self.stats_label.config(text=text)

    def sort_column(self, column):
        """Ordena tabela por coluna"""
        # Alterna direção de ordenação
        self.sort_reverse[column] = not self.sort_reverse.get(column, False)
        reverse = self.sort_reverse[column]

        # Mapeia coluna para campo no dicionário
        column_map = {
            'domain': 'domain',
            'seo_score': 'seo_score',
            'domain_authority': 'domain_authority',
            'page_authority': 'page_authority',
            'global_rank': 'global_rank',
            'backlinks': 'backlinks_count',
            'domain_age': 'domain_age_days',
            'hosting': 'hosting_provider',
            'ssl_days': 'ssl_expires_days'
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
            self.filter_table()

        except Exception as e:
            logger.error(f"Erro ao ordenar por {column}: {e}")

    def show_details(self, event):
        """Mostra detalhes de um domínio"""
        selection = self.tree.selection()
        if not selection:
            return

        # Obtém dados do item selecionado
        item = selection[0]
        values = self.tree.item(item)['values']
        domain_name = values[0]

        # Busca dados completos
        domain_data = next((d for d in self.current_data if d['domain'] == domain_name), None)
        if not domain_data:
            return

        # Monta mensagem de detalhes
        details = f"Domínio: {domain_name}\n\n"
        details += "=== SEO ===\n"
        details += f"SEO Score: {domain_data.get('seo_score', '-')}\n"
        details += f"Domain Authority: {domain_data.get('domain_authority', '-')}\n"
        details += f"Page Authority: {domain_data.get('page_authority', '-')}\n"
        details += f"Global Rank: {domain_data.get('global_rank', '-')}\n"
        details += f"Backlinks: {domain_data.get('backlinks_count', '-')}\n\n"

        details += "=== Domínio ===\n"
        details += f"Idade: {domain_data.get('domain_age_days', '-')} dias\n"
        details += f"Registrador: {domain_data.get('registrar', '-')}\n"
        details += f"Hosting: {domain_data.get('hosting_provider', '-')}\n\n"

        details += "=== Segurança ===\n"
        details += f"SSL expira em: {domain_data.get('ssl_expires_days', '-')} dias\n"
        details += f"Status HTTP: {domain_data.get('status_code', '-')}\n"
        details += f"Redirects: {domain_data.get('redirect_count', '-')}\n\n"

        details += "=== Analytics ===\n"
        details += f"Google Analytics: {'✓' if domain_data.get('ga4_code') else '✗'}\n"
        details += f"Facebook Pixel: {'✓' if domain_data.get('fb_pixel') else '✗'}\n"

        messagebox.showinfo("Detalhes do Domínio", details)

    def refresh_data(self):
        """Atualiza dados da tabela (filtra domínios ocultos)"""
        try:
            domains = self.db.get_all_domains(include_hidden=False)
            self.populate_table(domains)
        except Exception as e:
            logger.error(f"Erro ao atualizar dados: {e}")
            messagebox.showerror("Erro", f"Erro ao atualizar dados: {e}")
