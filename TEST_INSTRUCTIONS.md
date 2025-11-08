# 🧪 Instruções de Teste - Domain Manager Pro

## Teste Básico (Sem Instalar Dependências)

Apenas para verificar a estrutura:

```bash
# Verificar sintaxe Python
python3 -m py_compile main.py

# Ver estrutura do projeto
ls -R
```

## Instalação Completa

### 1. Instalar Dependências

```bash
pip3 install -r requirements.txt
```

**Dependências necessárias:**
- requests
- dnspython
- python-whois
- pyOpenSSL
- matplotlib

### 2. Executar o Aplicativo

```bash
python3 main.py
```

## Teste Funcional

### Teste 1: Adicionar Domínios Manualmente

1. Abra o aplicativo
2. Na aba "Domínios", digite:
   ```
   google.com
   github.com
   python.org
   ```
3. Clique em "Analisar Domínios"
4. Aguarde a análise completar

**Resultado esperado:** Tabela preenchida com informações dos 3 domínios

### Teste 2: Importar Lista de Domínios

1. Clique em "Importar TXT"
2. Selecione `example_domains.txt`
3. Clique em "Analisar Domínios"

**Resultado esperado:** 8 domínios analisados

### Teste 3: Filtros

1. Na busca, digite "google"
2. No filtro de Status, selecione "OK (200)"
3. No filtro de CMS, selecione "WordPress" (se houver)

**Resultado esperado:** Tabela filtra os resultados corretamente

### Teste 4: Detalhes do Domínio

1. Dê duplo clique em qualquer domínio na tabela
2. Veja as abas "Informações Gerais" e "HTTP Headers"

**Resultado esperado:** Janela modal com detalhes completos

### Teste 5: Exportação

1. Clique em "Exportar"
2. Escolha formato CSV
3. Salve o arquivo

**Resultado esperado:** Arquivo CSV criado com os dados

### Teste 6: Relatórios

1. Vá para aba "Relatórios"
2. Visualize os gráficos

**Resultado esperado:** 4 gráficos aparecem (CMS, Status, Cloud, SSL)

### Teste 7: Configurações

1. Vá para aba "Configurações"
2. Altere o timeout para 10
3. Clique em "Salvar Configurações"

**Resultado esperado:** Configurações salvas em `data/config.json`

### Teste 8: Reanálise

1. Selecione um ou mais domínios na tabela
2. Clique em "Atualizar"

**Resultado esperado:** Domínios selecionados são reanalisados

### Teste 9: Remoção

1. Selecione um domínio
2. Clique em "Remover"
3. Confirme

**Resultado esperado:** Domínio removido da tabela e banco

## Verificação de Arquivos Gerados

Após executar o aplicativo, verifique:

```bash
# Banco de dados
ls -lh data/domains.db

# Logs
ls -lh logs/

# Configurações
cat data/config.json
```

## Teste de Performance

### Teste de Carga

1. Crie um arquivo com 50+ domínios
2. Importe e analise
3. Observe o uso de CPU/memória

**Resultado esperado:** Análise completa sem travar a interface

## Problemas Conhecidos

### Tkinter não instalado

**Sintoma:** `ModuleNotFoundError: No module named '_tkinter'`

**Solução:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS
brew install python-tk

# Windows
Reinstale Python com opção "tcl/tk" marcada
```

### WHOIS falha para alguns domínios

**Sintoma:** Campos WHOIS vazios

**Causa:** Alguns TLDs não respondem bem ao python-whois

**Solução:** Normal, não é bug

### SSL timeout

**Sintoma:** Alguns domínios não retornam info de SSL

**Causa:** Firewall ou SSL mal configurado

**Solução:** Aumente o timeout nas configurações

## Teste de Integração

Execute todos os testes em sequência:

```bash
# 1. Verificar sintaxe
python3 -m py_compile main.py

# 2. Executar aplicativo
python3 main.py

# 3. Testar cada funcionalidade conforme lista acima

# 4. Verificar logs
cat logs/domain_manager_*.log
```

## Checklist de Teste

- [ ] Aplicativo inicia sem erros
- [ ] Análise de domínios funciona
- [ ] Filtros funcionam
- [ ] Detalhes abrem corretamente
- [ ] Exportação CSV funciona
- [ ] Exportação JSON funciona
- [ ] Exportação HTML funciona
- [ ] Gráficos aparecem na aba Relatórios
- [ ] Configurações são salvas
- [ ] Reanálise funciona
- [ ] Remoção funciona
- [ ] Importação de TXT funciona
- [ ] Banco de dados persiste entre execuções
- [ ] Logs são gerados

## Suporte

Se encontrar problemas:

1. Verifique os logs em `logs/`
2. Consulte o README.md
3. Abra uma issue no GitHub

## Próximos Passos

Após testes bem-sucedidos:

- Adicione seus próprios domínios
- Configure API Keys se disponível
- Agende verificações periódicas (manual)
- Exporte relatórios regularmente

---

**Boa sorte com os testes!** 🚀
