"""Exportador de dados em múltiplos formatos"""

import csv
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """Exporta dados de domínios em diferentes formatos"""

    @staticmethod
    def export_csv(domains, filepath):
        """
        Exporta domínios para CSV

        Args:
            domains: Lista de dicionários com informações dos domínios
            filepath: Caminho do arquivo de destino
        """
        if not domains:
            logger.warning("Nenhum domínio para exportar")
            return False

        try:
            # Define colunas principais
            fieldnames = [
                'domain', 'status_code', 'server', 'cloud_provider',
                'cms_detected', 'cms_version', 'ga4_code', 'fb_pixel',
                'ip_address', 'registrar', 'ssl_expires_days',
                'whois_created', 'whois_expires', 'is_spam', 'observations'
            ]

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for domain in domains:
                    # Converte listas para strings
                    row = domain.copy()
                    if isinstance(row.get('dns_servers'), list):
                        row['dns_servers'] = ', '.join(row['dns_servers'])

                    writer.writerow(row)

            logger.info(f"Dados exportados para CSV: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return False

    @staticmethod
    def export_json(domains, filepath):
        """
        Exporta domínios para JSON

        Args:
            domains: Lista de dicionários com informações dos domínios
            filepath: Caminho do arquivo de destino
        """
        if not domains:
            logger.warning("Nenhum domínio para exportar")
            return False

        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_domains': len(domains),
                'domains': domains
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Dados exportados para JSON: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao exportar JSON: {e}")
            return False

    @staticmethod
    def export_html(domains, filepath):
        """
        Exporta domínios para HTML

        Args:
            domains: Lista de dicionários com informações dos domínios
            filepath: Caminho do arquivo de destino
        """
        if not domains:
            logger.warning("Nenhum domínio para exportar")
            return False

        try:
            html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Domain Manager Pro - Relatório</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a2e;
            color: #eee;
            margin: 20px;
        }}
        h1 {{
            color: #0f3460;
            text-align: center;
        }}
        .meta {{
            text-align: center;
            color: #aaa;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #16213e;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #0f3460;
        }}
        th {{
            background: #0f3460;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background: #1a2332;
        }}
        .status-ok {{ color: #28a745; font-weight: bold; }}
        .status-redirect {{ color: #ffc107; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .cms {{ color: #17a2b8; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Domain Manager Pro - Relatório de Domínios</h1>
    <div class="meta">
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>Total de domínios: {len(domains)}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Domínio</th>
                <th>Status</th>
                <th>CMS</th>
                <th>Servidor</th>
                <th>IP</th>
                <th>SSL (dias)</th>
                <th>Registrar</th>
                <th>Observações</th>
            </tr>
        </thead>
        <tbody>
"""

            for domain in domains:
                status = domain.get('status_code', '-')
                status_class = 'status-ok' if status == 200 else (
                    'status-redirect' if 300 <= status < 400 else 'status-error'
                )

                cms = domain.get('cms_detected', '-')
                cms_version = domain.get('cms_version', '')
                cms_text = f"{cms} {cms_version}" if cms and cms != '-' else cms

                html += f"""
            <tr>
                <td><strong>{domain.get('domain', '-')}</strong></td>
                <td class="{status_class}">{status}</td>
                <td class="cms">{cms_text}</td>
                <td>{domain.get('server', '-')}</td>
                <td>{domain.get('ip_address', '-')}</td>
                <td>{domain.get('ssl_expires_days', '-')}</td>
                <td>{domain.get('registrar', '-')}</td>
                <td>{domain.get('observations', '-')}</td>
            </tr>
"""

            html += """
        </tbody>
    </table>
</body>
</html>
"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Dados exportados para HTML: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao exportar HTML: {e}")
            return False
