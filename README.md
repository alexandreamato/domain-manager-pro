# 🌐 Domain Manager Pro

> **⚠️ ARQUIVADO (ago/2026)** — Este projeto (v1, Python/Tkinter) foi substituído pela **v2**, um app nativo macOS em Tauri 2 (Rust + React), desenvolvido em `~/Developer/domain-manager-pro-v2`. Este repositório permanece apenas como referência histórica e como fonte da migração de dados (`data/domains.db`). Tag de arquivamento: `v1-archive`.

Sistema completo de gerenciamento e monitoramento de domínios com interface gráfica moderna em Python.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Descrição

**Domain Manager Pro** é um aplicativo desktop que permite analisar, monitorar e gerenciar múltiplos domínios de forma automatizada. O sistema coleta informações técnicas detalhadas sobre cada domínio e apresenta os dados em uma interface intuitiva com gráficos, filtros e relatórios.

### ✨ Características Principais

- 🔍 **Análise Automática** - Coleta informações completas de domínios automaticamente
- 💾 **Cache Local** - Banco de dados SQLite para armazenamento persistente
- 📊 **Relatórios Visuais** - Gráficos e estatísticas em tempo real
- 🎨 **Interface Moderna** - Design limpo com tema escuro
- ⚡ **Processamento Paralelo** - Análise simultânea de múltiplos domínios
- 💿 **Exportação** - CSV, JSON e HTML
- 🔔 **Dashboard** - Monitoramento contínuo de todos os domínios

## 🎯 Funcionalidades

### Coleta de Informações

Para cada domínio, o sistema detecta automaticamente:

| Categoria | Informações Coletadas |
|-----------|----------------------|
| **HTTP** | Código de status (200, 301, 404, etc.) |
| **Servidor** | Nome do servidor, cloud provider (Cloudflare, AWS, etc.) |
| **CMS** | WordPress, Joomla, Shopify, Wix, etc. + versão |
| **Analytics** | Google Analytics 4 (GA4), Facebook Pixel |
| **DNS** | Endereço IP, name servers |
| **WHOIS** | Registrar, data de criação, data de expiração |
| **SSL** | Dias até expiração do certificado |
| **Segurança** | Verificação em blacklists de spam |

### Interface

- ✅ Tabela interativa com ordenação e filtros
- ✅ Cores automáticas (verde=OK, amarelo=redirect, vermelho=erro)
- ✅ Busca em tempo real
- ✅ Detalhes completos ao clicar
- ✅ Importação de listas (.txt)
- ✅ Gráficos de distribuição (CMS, status, cloud providers, SSL)

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/domain-manager-pro.git
cd domain-manager-pro
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Execute o aplicativo**
```bash
python main.py
```

## 📖 Como Usar

### 1. Adicionar Domínios

Na aba **"Domínios"**:

1. Digite ou cole uma lista de domínios (um por linha)
2. Clique em **"🔍 Analisar Domínios"**
3. Aguarde a análise (barra de progresso mostra o andamento)

**Exemplo:**
```
amato.com.br
vascular.pro
sbugg.com
google.com
```

### 2. Visualizar Resultados

Os resultados aparecem na tabela com:

- ✅ Status HTTP colorido
- ✅ CMS detectado
- ✅ Informações de servidor e cloud
- ✅ Dados de SSL e WHOIS

**Dica:** Clique duas vezes em uma linha para ver detalhes completos!

### 3. Filtrar e Buscar

Use os filtros no topo da tabela:

- 🔎 **Buscar**: Digite parte do domínio
- **Status**: Filtre por OK, Redirect ou Erro
- **CMS**: Filtre por WordPress, Joomla, etc.

### 4. Exportar Dados

Clique em **"💾 Exportar"** e escolha o formato:

- CSV (Excel, Google Sheets)
- JSON (programação, APIs)
- HTML (relatório visual)

### 5. Ver Relatórios

Na aba **"📊 Relatórios"**, você encontra:

- Distribuição de CMS
- Status HTTP dos domínios
- Provedores cloud mais usados
- Expiração de certificados SSL

### 6. Configurações

Na aba **"⚙️ Configurações"**, ajuste:

- Timeout de requisições
- Número de threads paralelas
- API Keys (SEMrush, Moz, Estibot) - opcional

## 📁 Estrutura do Projeto

```
domain-manager-pro/
│
├── main.py                 # Arquivo principal
├── requirements.txt        # Dependências
├── README.md              # Este arquivo
│
├── src/
│   ├── __init__.py
│   │
│   ├── database/          # Banco de dados
│   │   ├── __init__.py
│   │   └── db_manager.py
│   │
│   ├── collectors/        # Coletores de informação
│   │   ├── __init__.py
│   │   └── domain_collector.py
│   │
│   ├── ui/                # Interface gráfica
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── domains_tab.py
│   │   ├── reports_tab.py
│   │   └── settings_tab.py
│   │
│   ├── reports/           # Relatórios e exportação
│   │   ├── __init__.py
│   │   ├── exporter.py
│   │   └── charts.py
│   │
│   └── utils/             # Utilitários
│       ├── __init__.py
│       ├── logger.py
│       └── config.py
│
├── data/                  # Dados persistentes
│   ├── domains.db         # Banco SQLite
│   └── config.json        # Configurações
│
└── logs/                  # Logs da aplicação
    └── domain_manager_*.log
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Tkinter** - Interface gráfica
- **SQLite** - Banco de dados local
- **Requests** - Requisições HTTP
- **DNSPython** - Consultas DNS
- **python-whois** - Informações WHOIS
- **pyOpenSSL** - Verificação SSL
- **Matplotlib** - Gráficos e visualizações

## ⚙️ Configurações Avançadas

### Personalizar Timeout

Por padrão, o timeout é de 5 segundos. Para sites lentos, aumente em **Configurações**.

### Threads Paralelas

O padrão é 10 threads. Você pode aumentar para analisar mais domínios simultaneamente.

### API Keys (Opcional)

Para funcionalidades avançadas de SEO, configure as chaves em **Configurações**:

- **SEMrush** - Métricas de tráfego
- **Moz** - Domain Authority
- **Estibot** - Avaliação de domínios

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### Erro: "Permission denied" no SQLite

Certifique-se de que a pasta `data/` tem permissões de escrita.

### Gráficos não aparecem

Instale o Tkinter:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
brew install python-tk
```

## 📝 Logs

Os logs são salvos automaticamente em `logs/domain_manager_YYYYMMDD.log`

Para debug, consulte os logs para identificar problemas.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Domain Manager Pro Team**

## 🙏 Agradecimentos

- Comunidade Python
- Desenvolvedores das bibliotecas utilizadas
- Todos os contribuidores

## 📞 Suporte

Para reportar bugs ou solicitar funcionalidades:

- Abra uma [Issue](https://github.com/seu-usuario/domain-manager-pro/issues)
- Entre em contato por email

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub!

**Versão:** 1.0.0
**Última atualização:** 2024
