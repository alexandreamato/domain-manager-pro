# 🔧 Solução de Problemas - Domain Manager Pro

## Problema: Domínios não aparecem no dashboard

### Sintoma
O aplicativo executa, faz a análise, mas a tabela fica vazia.

### Causa
Erro ao salvar domínios no banco de dados.

### Solução

**ATUALIZAÇÃO:** Este problema foi corrigido na versão mais recente!

1. **Atualize o código:**
```bash
git pull
```

2. **Remova o banco antigo:**
```bash
rm -f data/domains.db
```

3. **Execute novamente:**
```bash
python3 main.py
```

---

## Problema: Erro "You did not supply a value for binding parameter"

### Sintoma
```
Erro ao salvar domínio: You did not supply a value for binding parameter :is_spam
Erro ao salvar domínio: You did not supply a value for binding parameter :raw_metadata
```

### Causa
Campos obrigatórios do banco de dados faltando nos dados coletados.

### Solução
**JÁ CORRIGIDO!** Se você ainda vê esse erro:

```bash
git pull origin claude/domain-manager-pro-gui-011CUvPmLVTLivcMKmB27XAC
rm -f data/domains.db
python3 main.py
```

---

## Problema: Muitos erros de rede/DNS

### Sintoma
```
Erro HTTP para domain.com: Failed to resolve
Erro DNS para domain.com: nodename nor servname provided, or not known
```

### Causa
**Normal!** Alguns domínios podem:
- Não existir mais
- Não ter DNS configurado
- Estar bloqueados por firewall
- Estar offline temporariamente

### O que fazer
**Nada!** Esses erros são esperados. O aplicativo:
- ✓ Salva o que conseguiu coletar
- ✓ Marca erros no campo "Observações"
- ✓ Continua processando outros domínios

Para reduzir erros:
1. Aumente o timeout em **Configurações** (padrão: 5s → 10s)
2. Reduza threads paralelas (padrão: 10 → 5)

---

## Problema: "ModuleNotFoundError"

### Sintoma
```
ModuleNotFoundError: No module named 'requests'
```

### Solução
```bash
pip3 install -r requirements.txt
```

Ou instale manualmente:
```bash
pip3 install requests dnspython python-whois pyOpenSSL matplotlib
```

---

## Problema: Gráficos não aparecem

### Sintoma
Aba "Relatórios" está vazia ou dá erro.

### Solução

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
pip3 install matplotlib
```

**macOS:**
```bash
brew install python-tk
pip3 install matplotlib
```

**Windows:**
Reinstale Python com opção "tcl/tk and IDLE" marcada.

---

## Problema: Interface não abre

### Sintoma
O aplicativo inicia mas a janela não aparece.

### Solução

1. **Verifique Tkinter:**
```bash
python3 -c "import tkinter; tkinter._test()"
```

2. **Se falhar, instale:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS
brew install python-tk@3.11  # use sua versão do Python
```

---

## Problema: Permissão negada no banco de dados

### Sintoma
```
sqlite3.OperationalError: unable to open database file
```

### Solução
```bash
chmod -R 755 domain-manager-pro/
mkdir -p data logs
chmod 755 data logs
```

---

## Problema: WHOIS não funciona

### Sintoma
Campos WHOIS sempre vazios (registrar, datas).

### Causa
**Parcialmente normal**. Alguns TLDs:
- Bloqueiam consultas automatizadas
- Requerem autenticação
- Têm rate limiting
- Não respondem ao python-whois

### Domínios que geralmente funcionam:
- ✓ .com, .net, .org
- ✓ .br (parcial)
- ✗ .pro, .club, .ninja (limitados)

---

## Problema: SSL timeout

### Sintoma
```
Erro SSL para domain.com: timed out
```

### Causa
- Certificado inválido/expirado
- Porta 443 bloqueada
- Timeout muito curto

### Solução
Em **Configurações**, aumente o timeout:
- Padrão: 5 segundos
- Recomendado: 10 segundos
- Máximo: 30 segundos

---

## Problema: Aplicativo trava durante análise

### Sintoma
Interface congela ao analisar muitos domínios.

### Solução

**Não deveria acontecer!** O processamento é paralelo e não bloqueia a UI.

Se travar:
1. Reduza threads em **Configurações** (10 → 5)
2. Analise menos domínios por vez (máx 50)
3. Aumente timeout (evita travamento em domínios lentos)

---

## Teste Rápido

Execute o script de teste:

```bash
python3 test.py
```

**Resultado esperado:**
```
✓ TODOS OS TESTES PASSARAM!
```

Se falhar, veja o erro e procure a solução acima.

---

## Logs

Sempre consulte os logs em caso de problemas:

```bash
cat logs/domain_manager_*.log
```

Ou visualize só erros:
```bash
grep -i error logs/domain_manager_*.log
```

---

## Limpar e Recomeçar

Se nada funcionar:

```bash
# 1. Limpa dados
rm -rf data/ logs/

# 2. Atualiza código
git pull

# 3. Reinstala dependências
pip3 install -r requirements.txt --force-reinstall

# 4. Executa
python3 main.py
```

---

## Ainda com problemas?

1. Execute `python3 test.py` e envie o resultado
2. Compartilhe os logs: `logs/domain_manager_*.log`
3. Informe sua versão do Python: `python3 --version`
4. Informe seu sistema: `uname -a` (Linux/Mac) ou `ver` (Windows)

---

**Última atualização:** 2024-11-08
