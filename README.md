# Monitor USDT TRC20 - Tron

Aplicação web para monitorizar transações USDT TRC20 de carteiras Tron com funcionalidade de comprovante para WhatsApp.

## 🚀 Funcionalidades

- ✅ **Monitorização de Carteiras**: Adicione múltiplas carteiras Tron
- ✅ **Transações em Tempo Real**: Busca transações USDT TRC20 da blockchain
- ✅ **Comprovante para WhatsApp**: Gere comprovantes profissionais
- ✅ **Detecção de Duplicados**: Identifica transações suspeitas
- ✅ **Notas e Status**: Adicione notas e marque transações como completas
- ✅ **Monitorização Automática**: Verificação a cada 2 minutos
- ✅ **Banco de Dados Persistente**: SQLite integrado

## 📋 Requisitos

- Python 3.7+
- pip (gerenciador de pacotes Python)

## 🛠️ Instalação

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar Aplicação

```bash
python main.py
```

### 3. Acessar no Navegador

```
http://localhost:5000
```

## 🌐 Deploy em Produção

### Heroku

1. Instale o Heroku CLI
2. Crie um app: `heroku create seu-app-name`
3. Faça deploy: `git push heroku main`

### Vercel

1. Instale Vercel CLI: `npm i -g vercel`
2. Execute: `vercel`
3. Siga as instruções

### Railway

1. Conecte seu repositório no Railway
2. Deploy automático

### PythonAnywhere

1. Faça upload dos arquivos
2. Configure como Flask app
3. Defina `main.py` como arquivo principal

## 📁 Estrutura do Projeto

```
usdt-monitor-package/
├── main.py              # Aplicação Flask principal
├── requirements.txt     # Dependências Python
├── README.md           # Documentação
├── usdt_monitor.db     # Banco SQLite (criado automaticamente)
└── LICENSE             # Licença MIT
```

## 🔧 Configuração

### Variáveis de Ambiente (Opcional)

```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
export PORT=5000
```

### Personalização

- **Porta**: Altere `port=5000` em `main.py`
- **Banco**: SQLite por padrão, pode ser alterado para PostgreSQL/MySQL
- **API Tron**: Usa TronGrid API com fallback para dados demo

## 📱 Como Usar

### 1. Adicionar Carteira
- Cole o endereço da carteira Tron
- Adicione um nome (opcional)
- Clique "Adicionar"

### 2. Monitorizar Transações
- Clique "Monitorizar" para buscar transações
- Ative "Monitorização Automática" para verificação contínua

### 3. Gerar Comprovante
- Vá na aba "Saídas"
- Clique "Copiar Comprovante" em qualquer transação
- Cole no WhatsApp e compartilhe

### 4. Gerenciar Transações
- Adicione notas explicativas
- Marque como completa/pendente
- Visualize duplicados suspeitos

## 🔐 Segurança

- ✅ **CORS configurado** para acesso seguro
- ✅ **Validação de dados** em todas as rotas
- ✅ **Tratamento de erros** robusto
- ✅ **SQL Injection** protegido com SQLite

## 🐛 Solução de Problemas

### Erro de Porta
```bash
# Se a porta 5000 estiver ocupada
python -c "import main; main.app.run(host='0.0.0.0', port=8000)"
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Banco de Dados
```bash
# Deletar banco para reset
rm usdt_monitor.db
python main.py  # Recria automaticamente
```

## 📞 Suporte

- **Versão**: 1.0.0
- **Compatibilidade**: Python 3.7+, Flask 3.x
- **Banco**: SQLite (padrão), PostgreSQL/MySQL (configurável)
- **API**: TronGrid (oficial) + fallback demo

## 📄 Licença

MIT License - Veja LICENSE para detalhes.

---

**Desenvolvido para monitorização profissional de transações USDT TRC20** 🚀

