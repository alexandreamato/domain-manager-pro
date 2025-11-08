#!/usr/bin/env python3
"""
Script de teste rápido para verificar se o Domain Manager Pro está funcionando
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.domain_collector import DomainCollector
from src.database.db_manager import DatabaseManager

def test_single_domain():
    """Testa coleta e salvamento de um domínio"""
    print("=" * 60)
    print("Teste do Domain Manager Pro")
    print("=" * 60)
    print()

    # Cria coletor
    print("1. Criando coletor...")
    collector = DomainCollector(timeout=5)
    print("   ✓ Coletor criado")
    print()

    # Testa coleta
    test_domain = "google.com"
    print(f"2. Coletando informações de {test_domain}...")
    result = collector.collect_all_info(test_domain)
    print(f"   ✓ Informações coletadas")
    print()

    # Mostra resultado
    print("3. Resultado:")
    print(f"   - Domínio: {result.get('domain')}")
    print(f"   - Status: {result.get('status_code')}")
    print(f"   - Servidor: {result.get('server')}")
    print(f"   - IP: {result.get('ip_address')}")
    print(f"   - CMS: {result.get('cms_detected')}")
    print(f"   - Cloud: {result.get('cloud_provider')}")
    print(f"   - SSL dias: {result.get('ssl_expires_days')}")
    print()

    # Testa banco de dados
    print("4. Testando salvamento no banco...")
    db = DatabaseManager()
    try:
        db.save_domain(result)
        print("   ✓ Domínio salvo com sucesso!")
    except Exception as e:
        print(f"   ✗ Erro ao salvar: {e}")
        return False
    print()

    # Testa recuperação
    print("5. Testando recuperação do banco...")
    saved = db.get_domain(test_domain)
    if saved:
        print(f"   ✓ Domínio recuperado: {saved.get('domain')}")
    else:
        print("   ✗ Erro ao recuperar domínio")
        return False
    print()

    print("=" * 60)
    print("✓ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print()
    print("Agora você pode executar o aplicativo completo:")
    print("  python3 main.py")
    print()

    return True

if __name__ == "__main__":
    try:
        success = test_single_domain()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
