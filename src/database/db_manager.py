"""Gerenciador de banco de dados SQLite para armazenar informações de domínios"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerencia o banco de dados SQLite para cache de domínios"""

    def __init__(self, db_path="data/domains.db"):
        """Inicializa o gerenciador de banco de dados"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Cria as tabelas se não existirem"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tabela principal de domínios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                status_code INTEGER,
                server TEXT,
                cloud_provider TEXT,
                cms_detected TEXT,
                cms_version TEXT,
                ga4_code TEXT,
                fb_pixel TEXT,
                ip_address TEXT,
                registrar TEXT,
                ssl_expires_days INTEGER,
                dns_servers TEXT,
                whois_created TEXT,
                whois_expires TEXT,
                is_spam INTEGER DEFAULT 0,
                observations TEXT,
                raw_headers TEXT,
                raw_metadata TEXT,
                redirect_count INTEGER DEFAULT 0,
                discovered_subdomains TEXT,
                estimated_annual_cost INTEGER,
                google_indexed_pages INTEGER,
                seo_score INTEGER,
                estimated_domain_value INTEGER,
                domain_authority INTEGER,
                page_authority INTEGER,
                global_rank INTEGER,
                backlinks_count INTEGER,
                domain_age_days INTEGER,
                hosting_provider TEXT,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Adiciona novos campos se não existirem (migração)
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN redirect_count INTEGER DEFAULT 0")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN discovered_subdomains TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN estimated_annual_cost INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN google_indexed_pages INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN seo_score INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN estimated_domain_value INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN domain_authority INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN page_authority INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN global_rank INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN backlinks_count INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN domain_age_days INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN hosting_provider TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE domains ADD COLUMN is_hidden INTEGER DEFAULT 0")
        except:
            pass

        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de logs de verificação
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS check_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                check_type TEXT,
                status TEXT,
                error_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico (para gráficos de evolução)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                status_code INTEGER,
                ssl_expires_days INTEGER,
                seo_score INTEGER,
                google_indexed_pages INTEGER,
                estimated_domain_value INTEGER,
                domain_authority INTEGER,
                page_authority INTEGER,
                global_rank INTEGER,
                backlinks_count INTEGER,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (domain) REFERENCES domains(domain)
            )
        ''')

        # Índice para buscas rápidas por domínio no histórico
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_domain ON domain_history(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_date ON domain_history(checked_at)')
        except:
            pass

        conn.commit()
        conn.close()
        logger.info("Banco de dados inicializado com sucesso")

    def get_connection(self):
        """Retorna uma conexão com o banco de dados"""
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def save_domain(self, domain_data):
        """
        Salva ou atualiza informações de um domínio

        Args:
            domain_data: Dicionário com informações do domínio
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Garantir que todos os campos obrigatórios existam com valores padrão
            defaults = {
                'status_code': None,
                'server': None,
                'cloud_provider': None,
                'cms_detected': None,
                'cms_version': None,
                'ga4_code': None,
                'fb_pixel': None,
                'ip_address': None,
                'registrar': None,
                'ssl_expires_days': None,
                'dns_servers': [],
                'whois_created': None,
                'whois_expires': None,
                'is_spam': 0,
                'observations': '',
                'raw_headers': {},
                'raw_metadata': {},
                'redirect_count': 0,
                'discovered_subdomains': [],
                'estimated_annual_cost': None,
                'google_indexed_pages': None,
                'seo_score': None,
                'estimated_domain_value': None,
                'domain_authority': None,
                'page_authority': None,
                'global_rank': None,
                'backlinks_count': None,
                'domain_age_days': None,
                'hosting_provider': None
            }

            # Mescla defaults com domain_data (domain_data sobrescreve defaults)
            data = {**defaults, **domain_data}

            # Converter listas/dicts para JSON
            if isinstance(data.get('dns_servers'), list):
                data['dns_servers'] = json.dumps(data['dns_servers'])

            if isinstance(data.get('raw_headers'), dict):
                data['raw_headers'] = json.dumps(data['raw_headers'])

            if isinstance(data.get('raw_metadata'), dict):
                data['raw_metadata'] = json.dumps(data['raw_metadata'])

            if isinstance(data.get('discovered_subdomains'), list):
                data['discovered_subdomains'] = json.dumps(data['discovered_subdomains'])

            # Adicionar timestamp
            data['last_checked'] = datetime.now()

            # INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO domains (
                    domain, status_code, server, cloud_provider, cms_detected,
                    cms_version, ga4_code, fb_pixel, ip_address, registrar,
                    ssl_expires_days, dns_servers, whois_created, whois_expires,
                    is_spam, observations, raw_headers, raw_metadata, redirect_count,
                    discovered_subdomains, estimated_annual_cost, google_indexed_pages,
                    seo_score, estimated_domain_value, domain_authority, page_authority,
                    global_rank, backlinks_count, domain_age_days, hosting_provider,
                    last_checked
                ) VALUES (
                    :domain, :status_code, :server, :cloud_provider, :cms_detected,
                    :cms_version, :ga4_code, :fb_pixel, :ip_address, :registrar,
                    :ssl_expires_days, :dns_servers, :whois_created, :whois_expires,
                    :is_spam, :observations, :raw_headers, :raw_metadata, :redirect_count,
                    :discovered_subdomains, :estimated_annual_cost, :google_indexed_pages,
                    :seo_score, :estimated_domain_value, :domain_authority, :page_authority,
                    :global_rank, :backlinks_count, :domain_age_days, :hosting_provider,
                    :last_checked
                )
            ''', data)

            conn.commit()
            logger.info(f"Domínio {data.get('domain')} salvo com sucesso")

            # Salva snapshot histórico em thread separada para não bloquear
            try:
                self.save_history_snapshot(data)
            except:
                pass  # Não falha se histórico falhar

        except Exception as e:
            logger.error(f"Erro ao salvar domínio {domain_data.get('domain', '?')}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_domain(self, domain):
        """
        Recupera informações de um domínio

        Args:
            domain: Nome do domínio

        Returns:
            Dicionário com informações ou None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM domains WHERE domain = ?', (domain,))
        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))

            # Converter JSON de volta para objetos
            if data.get('dns_servers'):
                try:
                    data['dns_servers'] = json.loads(data['dns_servers'])
                except:
                    pass

            if data.get('raw_headers'):
                try:
                    data['raw_headers'] = json.loads(data['raw_headers'])
                except:
                    pass

            if data.get('raw_metadata'):
                try:
                    data['raw_metadata'] = json.loads(data['raw_metadata'])
                except:
                    pass

            return data

        return None

    def get_all_domains(self, include_hidden=False):
        """
        Retorna todos os domínios do banco de dados

        Args:
            include_hidden: Se True, inclui domínios ocultos. Se False, filtra apenas visíveis.

        Returns:
            Lista de domínios
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if include_hidden:
            cursor.execute('SELECT * FROM domains ORDER BY last_checked DESC')
        else:
            cursor.execute('SELECT * FROM domains WHERE is_hidden = 0 ORDER BY last_checked DESC')

        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]
        conn.close()

        domains = []
        for row in rows:
            data = dict(zip(columns, row))

            # Converter JSON
            if data.get('dns_servers'):
                try:
                    data['dns_servers'] = json.loads(data['dns_servers'])
                except:
                    pass

            domains.append(data)

        return domains

    def delete_domain(self, domain):
        """Remove um domínio do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM domains WHERE domain = ?', (domain,))
        conn.commit()
        conn.close()

        logger.info(f"Domínio {domain} removido")

    def hide_domain(self, domain):
        """
        Oculta um domínio (marca como is_hidden=1)

        Args:
            domain: Nome do domínio a ocultar
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE domains SET is_hidden = 1 WHERE domain = ?', (domain,))
        conn.commit()
        conn.close()

        logger.info(f"Domínio {domain} ocultado")

    def unhide_domain(self, domain):
        """
        Restaura um domínio oculto (marca como is_hidden=0)

        Args:
            domain: Nome do domínio a restaurar
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE domains SET is_hidden = 0 WHERE domain = ?', (domain,))
        conn.commit()
        conn.close()

        logger.info(f"Domínio {domain} restaurado")

    def get_hidden_domains(self):
        """
        Retorna todos os domínios ocultos

        Returns:
            Lista de domínios ocultos
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM domains WHERE is_hidden = 1 ORDER BY last_checked DESC')
        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]
        conn.close()

        domains = []
        for row in rows:
            data = dict(zip(columns, row))

            # Converter JSON
            if data.get('dns_servers'):
                try:
                    data['dns_servers'] = json.loads(data['dns_servers'])
                except:
                    pass

            domains.append(data)

        return domains

    def save_history_snapshot(self, domain_data):
        """
        Salva um snapshot histórico do domínio

        Args:
            domain_data: Dicionário com informações do domínio
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO domain_history (
                    domain, status_code, ssl_expires_days, seo_score,
                    google_indexed_pages, estimated_domain_value,
                    domain_authority, page_authority, global_rank,
                    backlinks_count, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                domain_data.get('domain'),
                domain_data.get('status_code'),
                domain_data.get('ssl_expires_days'),
                domain_data.get('seo_score'),
                domain_data.get('google_indexed_pages'),
                domain_data.get('estimated_domain_value'),
                domain_data.get('domain_authority'),
                domain_data.get('page_authority'),
                domain_data.get('global_rank'),
                domain_data.get('backlinks_count'),
                datetime.now()
            ))

            conn.commit()
            logger.debug(f"Snapshot histórico salvo para {domain_data.get('domain')}")

        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_domain_history(self, domain, days=30):
        """
        Recupera histórico de um domínio

        Args:
            domain: Nome do domínio
            days: Últimos N dias

        Returns:
            Lista de snapshots históricos
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT *
            FROM domain_history
            WHERE domain = ?
            AND checked_at >= datetime('now', '-' || ? || ' days')
            ORDER BY checked_at ASC
        ''', (domain, days))

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()

        history = []
        for row in rows:
            history.append(dict(zip(columns, row)))

        return history

    def get_domains_with_issues(self):
        """
        Retorna domínios com problemas, ordenados por prioridade

        Returns:
            Lista de domínios com problemas
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Busca domínios com problemas
        cursor.execute('''
            SELECT *,
                CASE
                    -- Prioridade 1: Erros críticos
                    WHEN status_code >= 500 THEN 1
                    WHEN ssl_expires_days IS NOT NULL AND ssl_expires_days <= 7 THEN 1
                    WHEN is_spam = 1 THEN 1

                    -- Prioridade 2: Erros médios
                    WHEN status_code >= 400 THEN 2
                    WHEN ssl_expires_days IS NOT NULL AND ssl_expires_days <= 30 THEN 2
                    WHEN status_code IS NULL THEN 2

                    -- Prioridade 3: Avisos
                    WHEN ssl_expires_days IS NOT NULL AND ssl_expires_days <= 90 THEN 3
                    WHEN redirect_count > 3 THEN 3
                    WHEN seo_score IS NOT NULL AND seo_score < 50 THEN 3

                    -- Sem problemas
                    ELSE 999
                END as priority
            FROM domains
            WHERE priority < 999
            ORDER BY priority ASC, ssl_expires_days ASC, status_code DESC
        ''')

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()

        domains = []
        for row in rows:
            data = dict(zip(columns, row))

            # Converter JSON
            if data.get('dns_servers'):
                try:
                    data['dns_servers'] = json.loads(data['dns_servers'])
                except:
                    pass

            # Identifica o problema
            priority = data.get('priority', 999)
            if priority == 1:
                data['issue_type'] = 'CRÍTICO'
            elif priority == 2:
                data['issue_type'] = 'MÉDIO'
            elif priority == 3:
                data['issue_type'] = 'AVISO'

            domains.append(data)

        return domains

    def get_cache_age(self, domain):
        """Retorna há quantos dias um domínio foi verificado"""
        data = self.get_domain(domain)
        if data and data.get('last_checked'):
            try:
                last_check = datetime.fromisoformat(str(data['last_checked']))
                delta = datetime.now() - last_check
                return delta.days
            except:
                return None
        return None

    def save_setting(self, key, value):
        """Salva uma configuração"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now()))

        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        """Recupera uma configuração"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else default

    def log_check(self, domain, check_type, status, error_message=None):
        """Registra um log de verificação"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO check_logs (domain, check_type, status, error_message, checked_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (domain, check_type, status, error_message, datetime.now()))

        conn.commit()
        conn.close()

    def get_statistics(self):
        """Retorna estatísticas gerais do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total de domínios
        cursor.execute('SELECT COUNT(*) FROM domains')
        stats['total_domains'] = cursor.fetchone()[0]

        # Domínios por CMS
        cursor.execute('''
            SELECT cms_detected, COUNT(*) as count
            FROM domains
            WHERE cms_detected IS NOT NULL
            GROUP BY cms_detected
        ''')
        stats['cms_distribution'] = dict(cursor.fetchall())

        # Domínios por status
        cursor.execute('''
            SELECT
                CASE
                    WHEN status_code = 200 THEN 'OK'
                    WHEN status_code BETWEEN 300 AND 399 THEN 'Redirect'
                    WHEN status_code >= 400 THEN 'Error'
                    ELSE 'Unknown'
                END as status_group,
                COUNT(*) as count
            FROM domains
            GROUP BY status_group
        ''')
        stats['status_distribution'] = dict(cursor.fetchall())

        # Provedores cloud mais usados
        cursor.execute('''
            SELECT cloud_provider, COUNT(*) as count
            FROM domains
            WHERE cloud_provider IS NOT NULL
            GROUP BY cloud_provider
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['cloud_providers'] = dict(cursor.fetchall())

        conn.close()
        return stats
