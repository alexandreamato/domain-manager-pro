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
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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
                'raw_metadata': {}
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

            # Adicionar timestamp
            data['last_checked'] = datetime.now()

            # INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO domains (
                    domain, status_code, server, cloud_provider, cms_detected,
                    cms_version, ga4_code, fb_pixel, ip_address, registrar,
                    ssl_expires_days, dns_servers, whois_created, whois_expires,
                    is_spam, observations, raw_headers, raw_metadata, last_checked
                ) VALUES (
                    :domain, :status_code, :server, :cloud_provider, :cms_detected,
                    :cms_version, :ga4_code, :fb_pixel, :ip_address, :registrar,
                    :ssl_expires_days, :dns_servers, :whois_created, :whois_expires,
                    :is_spam, :observations, :raw_headers, :raw_metadata, :last_checked
                )
            ''', data)

            conn.commit()
            logger.info(f"Domínio {data.get('domain')} salvo com sucesso")

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

    def get_all_domains(self):
        """Retorna todos os domínios do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM domains ORDER BY last_checked DESC')
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
