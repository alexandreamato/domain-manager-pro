# 📦 Guia de Atualização - v1.0 → v2.0

## ⚠️ Avisos Importantes

1. **O banco de dados NÃO é compatível** entre versões
2. **Você perderá os dados antigos** se não exportar antes
3. **Nova dependência** precisa ser instalada

---

## 🔄 Passos para Atualizar

### 1. Exportar Dados Antigos (Opcional)

Se quiser manter um backup dos domínios antigos:

```bash
# Antes de atualizar, execute o aplicativo v1.0
python3 main.py

# Na interface:
# 1. Clique em "Exportar"
# 2. Escolha JSON ou CSV
# 3. Salve como backup_v1.json
```

### 2. Atualizar o Código

```bash
cd domain-manager-pro
git pull origin claude/domain-manager-pro-gui-011CUvPmLVTLivcMKmB27XAC
```

### 3. Instalar Nova Dependência

```bash
pip install beautifulsoup4
```

**Ou reinstale tudo:**
```bash
pip install -r requirements.txt
```

### 4. Remover Banco de Dados Antigo

**CRÍTICO:** O banco antigo não funciona com v2.0!

```bash
rm -f data/domains.db
```

Se não remover, verá erros como:
```
sqlite3.OperationalError: table domains has no column named redirect_count
```

### 5. Executar Nova Versão

```bash
python3 main.py
```

O aplicativo criará automaticamente o novo banco de dados com todos os campos.

---

## 🔄 Reimportar Dados Antigos (Opcional)

Se exportou seus domínios antigos, pode reimportá-los:

### Opção 1: Via Interface

1. Abra o arquivo de backup (JSON ou CSV)
2. Copie a coluna/campo "domain"
3. Cole na área de texto do app
4. Clique em "Analisar Domínios"

### Opção 2: Script Python

```python
import json
from src.collectors.domain_collector import DomainCollector
from src.database.db_manager import DatabaseManager

# Carrega backup
with open('backup_v1.json', 'r') as f:
    old_data = json.load(f)

# Extrai apenas os nomes dos domínios
domains = [d['domain'] for d in old_data['domains']]

# Reanalisar
collector = DomainCollector()
db = DatabaseManager()

print(f"Reprocessando {len(domains)} domínios...")

for i, domain in enumerate(domains, 1):
    print(f"{i}/{len(domains)}: {domain}")
    result = collector.collect_all_info(domain)
    db.save_domain(result)

print("Concluído!")
```

---

## 🆕 Novos Recursos Disponíveis

Após atualizar, você terá acesso a:

### ✅ Na Interface

- **Ordenação de colunas** (clique nos cabeçalhos)
- **Subdomínios descobertos** (veja nos detalhes)
- **Custo anual estimado** (em observações)

### ✅ No Banco de Dados

```sql
SELECT domain, redirect_count, estimated_annual_cost,
       seo_score, estimated_domain_value
FROM domains;
```

### ✅ Programaticamente

```python
from src.collectors.seo_collector import SEOCollector

seo = SEOCollector()
info = seo.collect_all_seo_info('seu-dominio.com')

print(f"SEO Score: {info['seo_score']}/100")
print(f"Valor estimado: ${info['estimated_domain_value']}")
```

---

## 🐛 Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'bs4'"

**Solução:**
```bash
pip install beautifulsoup4
```

### Erro: "table domains has no column named redirect_count"

**Causa:** Banco antigo não foi removido.

**Solução:**
```bash
rm -f data/domains.db
# Execute o app novamente
python3 main.py
```

### Domínios desapareceram

**Causa:** Banco foi recriado zerado.

**Solução:** Reimporte seus domínios (veja seção "Reimportar Dados Antigos")

### Análise está muito lenta

**Causa:** Descoberta de subdomínios testa 30+ subdomínios.

**Solução:**
1. Vá em **Configurações**
2. Reduza **Threads** de 10 para 5
3. Aumente **Timeout** para 10 segundos

---

## 🔍 Verificar Versão

Para confirmar que está na v2.0:

```bash
# Ver commit atual
git log -1 --oneline

# Deve mostrar:
# dfc2038 Adicionar funcionalidades avançadas de análise de domínios
```

Ou na interface, vá em **Configurações** → **Sobre** → Deve mostrar "v2.0"

---

## 📊 Comparação de Funcionalidades

| Funcionalidade | v1.0 | v2.0 |
|----------------|------|------|
| Análise básica de domínios | ✅ | ✅ |
| URLs completas | ❌ | ✅ |
| Subdomínios | ❌ | ✅ |
| Remoção de duplicatas | ❌ | ✅ |
| Contador de redirects | ❌ | ✅ |
| Custo anual | ❌ | ✅ |
| SEO Score | ❌ | ✅ |
| Valor estimado | ❌ | ✅ |
| Ordenação de colunas | ❌ | ✅ |
| Descoberta de subdomínios | ❌ | ✅ |

---

## 💡 Dicas

### Análise Incremental

Se você tem muitos domínios:

1. Analise em lotes de 20-30
2. Exporte após cada lote
3. Evita perder progresso se algo falhar

### Backup Regular

```bash
# Automatize backups diários
cp data/domains.db backups/domains_$(date +%Y%m%d).db
```

### Configuração Otimizada

Para análises mais rápidas:

```
Timeout: 5 segundos
Threads: 8-10
```

Para análises mais completas:

```
Timeout: 10 segundos
Threads: 5
```

---

## 🎯 Próximos Passos

Após atualizar:

1. ✅ Teste com 2-3 domínios primeiro
2. ✅ Verifique se subdomínios são descobertos
3. ✅ Teste a ordenação de colunas
4. ✅ Exporte e veja os novos campos
5. ✅ Reimporte seus domínios antigos

---

## 📞 Suporte

Se encontrar problemas:

1. Consulte `TROUBLESHOOTING.md`
2. Veja os logs em `logs/domain_manager_*.log`
3. Abra uma issue no GitHub com:
   - Versão do Python (`python3 --version`)
   - Sistema operacional
   - Erro completo dos logs

---

**Boa sorte com a atualização! 🚀**
