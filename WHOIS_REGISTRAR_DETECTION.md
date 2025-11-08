# Sistema de Detecção de Registrar - Domain Manager Pro

## Visão Geral

O Domain Manager Pro implementa um sistema robusto de detecção de registrar com múltiplos fallbacks para garantir a máxima compatibilidade com diferentes TLDs (Top-Level Domains).

## Estratégias de Detecção

O sistema tenta **3 estratégias sequenciais** até conseguir identificar o registrar:

### 1️⃣ Biblioteca python-whois (Rápido)

**Método:** Usa a biblioteca `python-whois` que já possui parsing pré-configurado para muitos TLDs.

**Vantagens:**
- Rápido e eficiente
- Funciona out-of-the-box para TLDs comuns (.com, .net, .org)
- Parsing já testado

**Quando falha:**
- TLDs menos comuns ou regionais
- Domínios com proteção de privacidade WHOIS
- Mudanças recentes nos formatos de resposta WHOIS

```python
w = whois.whois(domain)
registrar = w.registrar
```

---

### 2️⃣ Consulta via Socket + Parsing Manual (Robusto)

**Método:** Faz consulta direta ao servidor WHOIS via socket TCP (porta 43) e faz parsing manual com múltiplos padrões regex.

**Processo:**
1. Consulta `whois.iana.org` para descobrir o servidor WHOIS correto
2. Se falhar, usa tabela de fallback com 20+ TLDs
3. Faz consulta direta ao servidor WHOIS
4. Aplica 7+ padrões regex diferentes para extrair registrar

**Padrões de detecção:**
- `registrar:` (padrão geral)
- `registrar name:` (variação)
- `sponsoring registrar:` (.uk e outros)
- `registrar organization:` (alguns gTLDs)
- `registro criado por:` (.br em português)
- `responsible registrar:` (.br em inglês)
- `registrar whois server:` (informação alternativa)

**TLDs suportados na tabela de fallback:**
```
.com, .net, .org, .br, .info, .biz, .io, .co, .uk, .us, .ca,
.de, .eu, .nl, .fr, .au, .ru, .cn, .in, .jp
```

**Código:**
```python
whois_server = self._find_whois_server(domain)
whois_text = self._whois_query_socket(whois_server, domain)
registrar = self._parse_whois_registrar(whois_text, domain)
```

---

### 3️⃣ Fallback Especial para .br (Registro.br)

**Método:** Para domínios brasileiros, consulta diretamente o `whois.registro.br` com parsing específico para o formato brasileiro.

**Diferencial:**
- Formato de resposta em português
- Campos diferentes: `owner`, `responsible`, `owner-c`
- Datas em formato `YYYYMMDD` (convertido automaticamente)

**Quando usar:**
- Qualquer domínio terminado em `.br` ou `.com.br`
- Se as estratégias anteriores falharem

**Retorno especial:**
- Se não encontrar "registrar", retorna "Owner: [nome do proprietário]"
- Útil para identificar quem gerencia o domínio

```python
if domain.endswith('.br') and not info['registrar']:
    whois_text = self._whois_query_socket("whois.registro.br", domain)
    registrar = self._parse_whois_registrar(whois_text, domain)
```

---

## Tratamento de Casos Especiais

### Domínios com Privacidade WHOIS

Quando detectado:
- `"not disclosed"`
- `"redacted"`
- `"n/a"`
- `"none"`

**Comportamento:** O sistema ignora esses valores e tenta a próxima estratégia.

### Formatos de Data

O sistema detecta e converte automaticamente:

**Formato ISO (padrão):**
```
Creation Date: 2020-01-15
Expiration Date: 2025-01-15
```

**Formato brasileiro (.br):**
```
criado: 20200115
validade: 20250115
```
↓ Convertido automaticamente para ↓
```
2020-01-15
2025-01-15
```

### Registrar em Lista (Array)

Alguns servidores WHOIS retornam múltiplos registrars (histórico). O sistema sempre pega o **primeiro** (mais recente):

```python
if isinstance(w.registrar, list):
    info['registrar'] = w.registrar[0]
```

---

## Logs e Debug

O sistema gera logs detalhados em cada etapa:

```
INFO - WHOIS via biblioteca para example.com: registrar=NAMECHEAP INC
INFO - Tentando WHOIS via socket para example.org
INFO - WHOIS via socket para example.org: registrar=PUBLIC INTEREST REGISTRY
INFO - Tentando WHOIS específico .br para example.com.br
INFO - WHOIS .br para example.com.br: registrar=Owner: Example Corp
```

---

## Exemplos de Uso

### Domínio .com (Sucesso na 1ª tentativa)
```python
domain = "google.com"
info = collector.get_whois_info(domain)
# Result: {'registrar': 'MarkMonitor Inc.', ...}
```

### Domínio .br (Sucesso na 3ª tentativa)
```python
domain = "uol.com.br"
info = collector.get_whois_info(domain)
# Result: {'registrar': 'Owner: UNIVERSO ONLINE S/A', ...}
```

### Domínio .io (Sucesso na 2ª tentativa)
```python
domain = "example.io"
info = collector.get_whois_info(domain)
# Result: {'registrar': 'NAMECHEAP INC', ...}
```

---

## Limitações Conhecidas

1. **Rate Limiting:** Consultas WHOIS em massa podem ser bloqueadas. Use com moderação.

2. **GDPR/Privacidade:** Muitos registrars europeus ocultam dados por GDPR.

3. **TLDs Exóticos:** TLDs muito específicos podem não ter servidor WHOIS público.

4. **Timeout:** Consultas lentas são limitadas a 10 segundos (configurável).

---

## Configuração Avançada

### Ajustar Timeout

No `DomainCollector`:
```python
collector = DomainCollector(timeout=15)  # 15 segundos
```

### Adicionar Novo TLD

Edite a tabela `tld_servers` em `_find_whois_server()`:
```python
tld_servers = {
    'com': 'whois.verisign-grs.com',
    'xyz': 'whois.nic.xyz',  # Adicione aqui
    # ...
}
```

### Adicionar Novo Padrão de Parsing

Edite a lista `patterns` em `_parse_whois_registrar()`:
```python
patterns = [
    r'(?:^|\n)registrar:\s*(.+?)(?:\n|$)',
    r'(?:^|\n)seu_padrao_customizado:\s*(.+?)(?:\n|$)',  # Adicione aqui
    # ...
]
```

---

## Referências

- [IANA WHOIS Service](https://www.iana.org/whois)
- [Registro.br WHOIS](https://registro.br/tecnologia/ferramentas/whois/)
- [RFC 3912 - WHOIS Protocol](https://tools.ietf.org/html/rfc3912)
- [python-whois Documentation](https://github.com/richardpenman/whois)

---

**Última atualização:** 2025-11-08
**Versão:** 2.1
