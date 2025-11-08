# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-11-08

### Adicionado

- Interface gráfica completa com Tkinter e tema escuro
- Análise automática de domínios com coleta de informações:
  - Status HTTP e headers
  - Detecção de CMS (WordPress, Joomla, Shopify, Wix, etc.)
  - Versão do CMS quando disponível
  - Google Analytics 4 e Facebook Pixel
  - Informações DNS (IP e name servers)
  - Dados WHOIS (registrar, criação, expiração)
  - Certificado SSL e dias até expiração
  - Verificação em blacklists de spam
  - Detecção de cloud provider (Cloudflare, AWS, etc.)

- Banco de dados SQLite para cache local
- Processamento paralelo com ThreadPoolExecutor
- Tabela interativa com:
  - Ordenação por colunas
  - Filtros (busca, status, CMS)
  - Cores automáticas por status
  - Detalhes completos ao clicar

- Sistema de relatórios com gráficos:
  - Distribuição de CMS
  - Status HTTP dos domínios
  - Provedores cloud mais usados
  - Expiração de certificados SSL

- Exportação de dados em múltiplos formatos:
  - CSV
  - JSON
  - HTML

- Sistema de configurações:
  - Timeout personalizável
  - Número de threads configurável
  - API Keys opcionais (SEMrush, Moz, Estibot)

- Sistema de logging completo
- Importação de listas de domínios (.txt)
- Reanálise de domínios selecionados
- Remoção de domínios do banco
- Estatísticas gerais

### Funcionalidades

- Dashboard para monitoramento contínuo
- Interface responsiva e moderna
- Barras de progresso durante análise
- Tooltips informativos
- Cache inteligente de dados

### Documentação

- README completo em português
- Guia de início rápido
- Exemplos de uso
- Script de instalação
- Lista de domínios de exemplo

## [Futuras Versões]

### Planejado

- [ ] Alertas automáticos para SSL expirando
- [ ] Agendamento de verificações periódicas
- [ ] Integração com APIs de SEO (SEMrush, Moz)
- [ ] Exportação em PDF
- [ ] Gráficos de histórico de mudanças
- [ ] Notificações desktop
- [ ] Suporte a múltiplos idiomas
- [ ] Modo claro/escuro alternável
- [ ] Comparação entre domínios
- [ ] Detecção de tecnologias avançadas
