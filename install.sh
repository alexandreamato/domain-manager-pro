#!/bin/bash

# Script de instalação para Domain Manager Pro

echo "🌐 Domain Manager Pro - Instalação"
echo "=================================="
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"
echo ""

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale pip."
    exit 1
fi

echo "✅ pip3 encontrado"
echo ""

# Cria virtual environment (opcional)
read -p "Deseja criar um ambiente virtual? (s/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Ambiente virtual criado e ativado"
    echo ""
fi

# Instala dependências
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Instalação concluída com sucesso!"
    echo ""
    echo "Para executar o Domain Manager Pro:"
    echo "  python3 main.py"
    echo ""
    echo "Se você criou um ambiente virtual, ative-o primeiro:"
    echo "  source venv/bin/activate"
else
    echo ""
    echo "❌ Erro na instalação. Verifique os logs acima."
    exit 1
fi
