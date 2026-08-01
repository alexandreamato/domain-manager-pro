#!/bin/bash
#
# Domain Manager Pro - Launcher
# Este script pode ser colocado em qualquer pasta do seu computador
#

# Caminho do projeto (ajuste se necessário)
PROJECT_DIR="/Users/alexandreamato/Amato Dropbox/Alexandre Amato/Projects/Informatica/Software/domain-manager-pro"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "       Domain Manager Pro v1.0.0"
echo "=========================================="
echo ""

# Verifica se o diretório do projeto existe
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Erro: Diretório do projeto não encontrado!${NC}"
    echo "Esperado em: $PROJECT_DIR"
    echo ""
    echo "Pressione qualquer tecla para fechar..."
    read -n 1
    exit 1
fi

# Muda para o diretório do projeto
cd "$PROJECT_DIR"

# Verifica se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erro: Python3 não está instalado!${NC}"
    echo "Por favor, instale o Python3 primeiro."
    echo ""
    echo "Pressione qualquer tecla para fechar..."
    read -n 1
    exit 1
fi

# Função para criar/ativar ambiente virtual
setup_venv() {
    VENV_DIR="$PROJECT_DIR/venv"

    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${BLUE}Criando ambiente virtual...${NC}"
        python3 -m venv "$VENV_DIR"

        if [ $? -ne 0 ]; then
            echo -e "${RED}Erro ao criar ambiente virtual!${NC}"
            return 1
        fi

        echo -e "${GREEN}Ambiente virtual criado com sucesso!${NC}"
    fi

    # Ativa o ambiente virtual
    source "$VENV_DIR/bin/activate"

    return 0
}

# Função para instalar dependências
install_deps() {
    echo -e "${BLUE}Verificando dependências...${NC}"

    # Verifica se requests está instalado (um dos módulos principais)
    if ! python3 -c "import requests" &> /dev/null; then
        echo -e "${YELLOW}Instalando dependências necessárias...${NC}"
        echo ""
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r "$PROJECT_DIR/requirements.txt"

        if [ $? -ne 0 ]; then
            echo -e "${RED}Erro ao instalar dependências!${NC}"
            return 1
        fi

        echo ""
        echo -e "${GREEN}Dependências instaladas com sucesso!${NC}"
    else
        echo -e "${GREEN}Dependências OK!${NC}"
    fi

    return 0
}

# Configura ambiente virtual
setup_venv
if [ $? -ne 0 ]; then
    echo "Pressione qualquer tecla para fechar..."
    read -n 1
    exit 1
fi

# Instala dependências se necessário
install_deps
if [ $? -ne 0 ]; then
    echo "Pressione qualquer tecla para fechar..."
    read -n 1
    exit 1
fi

echo ""
echo -e "${GREEN}Iniciando aplicação...${NC}"
echo ""

# Executa o aplicativo
python3 "$PROJECT_DIR/main.py"

# Se o app fechar com erro, mantém a janela aberta
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}A aplicação fechou com erro.${NC}"
    echo "Pressione qualquer tecla para fechar..."
    read -n 1
fi
