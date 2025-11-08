# 🚀 Guia de Início Rápido - Domain Manager Pro

## Instalação Rápida

### Método 1: Script Automático (Linux/macOS)

```bash
chmod +x install.sh
./install.sh
```

### Método 2: Manual

```bash
# 1. Instalar dependências
pip3 install -r requirements.txt

# 2. Executar aplicativo
python3 main.py
```

## Primeiros Passos

### 1️⃣ Adicionar Domínios

1. Abra o Domain Manager Pro
2. Na aba **"🏠 Domínios"**, cole uma lista de domínios:

```
google.com
facebook.com
github.com
```

3. Clique em **"🔍 Analisar Domínios"**

### 2️⃣ Ver Resultados

- A tabela mostrará todos os dados coletados
- **Verde** = Domínio OK (status 200)
- **Amarelo** = Redirecionamento (3xx)
- **Vermelho** = Erro (4xx/5xx)

### 3️⃣ Filtrar e Buscar

Use os filtros no topo:

- **🔎 Buscar**: Digite parte do nome do domínio
- **Status**: Filtre por tipo de resposta HTTP
- **CMS**: Filtre por WordPress, Joomla, etc.

### 4️⃣ Ver Detalhes

**Clique duas vezes** em qualquer domínio para ver:

- Headers HTTP completos
- Informações detalhadas de DNS
- Dados de WHOIS
- Certificado SSL

### 5️⃣ Exportar Dados

1. Clique em **"💾 Exportar"**
2. Escolha o formato:
   - **CSV** → Para Excel/Google Sheets
   - **JSON** → Para programação
   - **HTML** → Relatório visual

### 6️⃣ Ver Relatórios

1. Vá para aba **"📊 Relatórios"**
2. Visualize gráficos de:
   - Distribuição de CMS
   - Status dos domínios
   - Provedores cloud
   - Expiração SSL

## Dicas Úteis

### ⚡ Importar Lista de Domínios

1. Crie um arquivo `.txt` com domínios (um por linha)
2. Clique em **"📂 Importar TXT"**
3. Selecione o arquivo

### 🔄 Reanalisar Domínios

- Selecione um ou mais domínios na tabela
- Clique em **"🔄 Atualizar"**
- Os domínios serão reanalisados

### ⚙️ Ajustar Configurações

Na aba **"⚙️ Configurações"**:

- **Timeout**: Aumente para sites lentos (padrão: 5s)
- **Threads**: Mais threads = análise mais rápida (padrão: 10)
- **API Keys**: Opcional, para métricas avançadas

## Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| Duplo clique | Ver detalhes do domínio |
| Ctrl+F | Focar na busca |
| Delete | Remover domínio selecionado |

## Solução de Problemas

### ❌ "ModuleNotFoundError"

```bash
pip3 install -r requirements.txt
```

### ❌ Gráficos não aparecem

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**macOS:**
```bash
brew install python-tk
```

### ❌ Erro de permissão

```bash
chmod -R 755 domain-manager-pro/
```

## Arquivos Importantes

- **`data/domains.db`** → Banco de dados (seus domínios ficam aqui)
- **`logs/`** → Logs de erro e debug
- **`data/config.json`** → Suas configurações

## Exemplo Prático

Teste com os domínios do arquivo `example_domains.txt`:

1. Abra o Domain Manager Pro
2. Clique em **"📂 Importar TXT"**
3. Selecione `example_domains.txt`
4. Clique em **"🔍 Analisar Domínios"**
5. Aguarde a análise completar
6. Explore os resultados!

## Próximos Passos

- ✅ Adicione seus próprios domínios
- ✅ Configure alertas para SSL expirando
- ✅ Exporte relatórios periódicos
- ✅ Monitore mudanças nos domínios

## Precisa de Ajuda?

Consulte o **README.md** completo ou abra uma issue no GitHub.

---

**Divirta-se gerenciando seus domínios! 🎉**
