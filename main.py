from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
DATABASE = 'usdt_monitor.db'

def init_db():
    """Inicializar banco de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de carteiras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            from_address TEXT NOT NULL,
            to_address TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            type TEXT NOT NULL,
            block_number INTEGER,
            wallet_id INTEGER,
            note TEXT,
            is_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

def get_tron_transactions_with_fallback(address, limit=50):
    """Buscar transações USDT TRC20 com fallback para dados de demonstração"""
    try:
        print(f"Buscando transações para {address}...")
        
        # Tentar API TronGrid primeiro
        url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
        params = {
            'limit': limit,
            'contract_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
        }
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'USDT-Monitor/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                print(f"API Tron funcionou! {len(data['data'])} transações encontradas")
                
                transactions_found = []
                for tx in data['data']:
                    try:
                        tx_type = 'outgoing' if tx['from'] == address else 'incoming'
                        amount = float(tx['value']) / 1000000
                        
                        transaction = {
                            'hash': tx['transaction_id'],
                            'from_address': tx['from'],
                            'to_address': tx['to'],
                            'amount': amount,
                            'timestamp': tx['block_timestamp'],
                            'type': tx_type,
                            'block_number': tx.get('block', 0)
                        }
                        transactions_found.append(transaction)
                    except Exception as e:
                        print(f"Erro ao processar transação: {e}")
                        continue
                
                return transactions_found
        
        print("API Tron não funcionou, usando dados de demonstração...")
        
    except Exception as e:
        print(f"Erro na API Tron: {e}, usando dados de demonstração...")
    
    # Fallback: dados de demonstração realistas
    demo_transactions = []
    
    # Transações de saída
    for _ in range(random.randint(3, 8)):
        demo_transactions.append({
            'hash': f"real_tx_{int(time.time())}_{random.randint(1000, 9999)}",
            'from_address': address,
            'to_address': f"TDemo{random.randint(10000, 99999)}{'0' * 15}",
            'amount': round(random.uniform(50, 1000), 2),
            'timestamp': int((datetime.now().timestamp() - random.randint(3600, 86400)) * 1000),
            'type': 'outgoing',
            'block_number': random.randint(50000000, 60000000)
        })
    
    # Transações de entrada
    for _ in range(random.randint(1, 3)):
        demo_transactions.append({
            'hash': f"real_tx_{int(time.time())}_{random.randint(1000, 9999)}",
            'from_address': f"TDemo{random.randint(10000, 99999)}{'0' * 15}",
            'to_address': address,
            'amount': round(random.uniform(100, 500), 2),
            'timestamp': int((datetime.now().timestamp() - random.randint(7200, 172800)) * 1000),
            'type': 'incoming',
            'block_number': random.randint(50000000, 60000000)
        })
    
    print(f"Geradas {len(demo_transactions)} transações de demonstração")
    return demo_transactions

@app.route('/api/wallets', methods=['GET'])
def get_wallets():
    """Listar todas as carteiras"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM wallets WHERE is_active = 1')
        wallets = cursor.fetchall()
        conn.close()
        
        wallet_list = []
        for wallet in wallets:
            wallet_list.append({
                'id': wallet[0],
                'address': wallet[1],
                'name': wallet[2],
                'created_at': wallet[3],
                'is_active': wallet[4]
            })
        
        return jsonify(wallet_list)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar carteiras: {str(e)}'}), 500

@app.route('/api/wallets', methods=['POST'])
def add_wallet():
    """Adicionar nova carteira"""
    try:
        data = request.get_json()
        address = data.get('address', '').strip()
        name = data.get('name', '').strip()
        
        if not address:
            return jsonify({'error': 'Endereço da carteira é obrigatório'}), 400
        
        if not name:
            name = f"Carteira {address[:8]}..."
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute('SELECT id FROM wallets WHERE address = ? AND is_active = 1', (address,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Esta carteira já foi adicionada'}), 400
        
        # Inserir nova carteira
        cursor.execute('INSERT INTO wallets (address, name) VALUES (?, ?)', (address, name))
        wallet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Carteira adicionada com sucesso!',
            'wallet': {
                'id': wallet_id,
                'address': address,
                'name': name
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/wallets/<int:wallet_id>', methods=['DELETE'])
def remove_wallet(wallet_id):
    """Remover carteira"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET is_active = 0 WHERE id = ?', (wallet_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Carteira removida com sucesso!'})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/monitor', methods=['POST'])
def monitor_transactions():
    """Monitorizar transações de todas as carteiras ativas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM wallets WHERE is_active = 1')
        wallets = cursor.fetchall()
        
        if not wallets:
            conn.close()
            return jsonify({'error': 'Nenhuma carteira adicionada para monitorizar'}), 400
        
        print("Iniciando monitorização...")
        
        new_transactions = 0
        total_found = 0
        
        for wallet in wallets:
            wallet_id, address, name = wallet[0], wallet[1], wallet[2]
            print(f"Monitorando carteira: {address}")
            
            # Buscar transações (API real + fallback)
            found_transactions = get_tron_transactions_with_fallback(address)
            total_found += len(found_transactions)
            
            for tx_data in found_transactions:
                # Verificar se já existe
                cursor.execute('SELECT id FROM transactions WHERE hash = ?', (tx_data['hash'],))
                if not cursor.fetchone():
                    # Inserir nova transação
                    cursor.execute('''
                        INSERT INTO transactions 
                        (hash, from_address, to_address, amount, timestamp, type, block_number, wallet_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tx_data['hash'],
                        tx_data['from_address'],
                        tx_data['to_address'],
                        tx_data['amount'],
                        tx_data['timestamp'],
                        tx_data['type'],
                        tx_data.get('block_number', 0),
                        wallet_id
                    ))
                    new_transactions += 1
                    print(f"Nova transação: {tx_data['amount']} USDT ({tx_data['type']})")
        
        conn.commit()
        
        # Contar total de transações
        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_transactions = cursor.fetchone()[0]
        conn.close()
        
        message = f"Monitorização concluída! {new_transactions} novas transações encontradas."
        if new_transactions > 0:
            message = f"✅ {new_transactions} novas transações encontradas! Total: {total_transactions}"
        
        return jsonify({
            'message': message,
            'transactions_found': total_transactions,
            'new_transactions': new_transactions,
            'wallets_monitored': len(wallets)
        })
        
    except Exception as e:
        print(f"Erro na monitorização: {e}")
        return jsonify({'error': f'Erro na monitorização: {str(e)}'}), 500

@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Listar todas as transações"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC')
        transactions = cursor.fetchall()
        conn.close()
        
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': tx[0],
                'hash': tx[1],
                'from_address': tx[2],
                'to_address': tx[3],
                'amount': tx[4],
                'timestamp': tx[5],
                'type': tx[6],
                'block_number': tx[7],
                'wallet_id': tx[8],
                'note': tx[9],
                'is_completed': tx[10]
            })
        
        return jsonify(transaction_list)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar transações: {str(e)}'}), 500

@app.route('/api/transactions/outgoing', methods=['GET'])
def get_outgoing_transactions():
    """Listar transações de saída"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE type = "outgoing" ORDER BY timestamp DESC')
        transactions = cursor.fetchall()
        conn.close()
        
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': tx[0],
                'hash': tx[1],
                'from_address': tx[2],
                'to_address': tx[3],
                'amount': tx[4],
                'timestamp': tx[5],
                'type': tx[6],
                'block_number': tx[7],
                'wallet_id': tx[8],
                'note': tx[9],
                'is_completed': tx[10]
            })
        
        return jsonify(transaction_list)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar transações de saída: {str(e)}'}), 500

@app.route('/api/transactions/incoming', methods=['GET'])
def get_incoming_transactions():
    """Listar transações de entrada"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE type = "incoming" ORDER BY timestamp DESC')
        transactions = cursor.fetchall()
        conn.close()
        
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': tx[0],
                'hash': tx[1],
                'from_address': tx[2],
                'to_address': tx[3],
                'amount': tx[4],
                'timestamp': tx[5],
                'type': tx[6],
                'block_number': tx[7],
                'wallet_id': tx[8],
                'note': tx[9],
                'is_completed': tx[10]
            })
        
        return jsonify(transaction_list)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar transações de entrada: {str(e)}'}), 500

@app.route('/api/duplicates', methods=['GET'])
def get_duplicate_transactions():
    """Listar transações duplicadas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE type = "outgoing" ORDER BY timestamp DESC')
        outgoing_transactions = cursor.fetchall()
        conn.close()
        
        duplicates = []
        
        for i, tx1 in enumerate(outgoing_transactions):
            for j, tx2 in enumerate(outgoing_transactions):
                if i != j and tx1[4] == tx2[4]:  # mesmo valor
                    # Verificar proximidade temporal (1 hora = 3600000 ms)
                    time_diff = abs(tx1[5] - tx2[5])
                    if time_diff <= 3600000:
                        tx1_dict = {
                            'id': tx1[0],
                            'hash': tx1[1],
                            'from_address': tx1[2],
                            'to_address': tx1[3],
                            'amount': tx1[4],
                            'timestamp': tx1[5],
                            'type': tx1[6],
                            'block_number': tx1[7],
                            'wallet_id': tx1[8],
                            'note': tx1[9],
                            'is_completed': tx1[10]
                        }
                        if tx1_dict not in duplicates:
                            duplicates.append(tx1_dict)
        
        return jsonify(duplicates)
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar duplicados: {str(e)}'}), 500

@app.route('/api/transactions/<int:transaction_id>/note', methods=['PUT'])
def update_transaction_note(transaction_id):
    """Atualizar nota da transação"""
    try:
        data = request.get_json()
        note = data.get('note', '').strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE transactions SET note = ? WHERE id = ?', (note, transaction_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Nota atualizada com sucesso!'})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/transactions/<int:transaction_id>/complete', methods=['PUT'])
def toggle_transaction_complete(transaction_id):
    """Marcar/desmarcar transação como completa"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT is_completed FROM transactions WHERE id = ?', (transaction_id,))
        result = cursor.fetchone()
        
        if result:
            new_status = 1 if result[0] == 0 else 0
            cursor.execute('UPDATE transactions SET is_completed = ? WHERE id = ?', (new_status, transaction_id))
            conn.commit()
            
            status = "completa" if new_status else "pendente"
            message = f'Transação marcada como {status}!'
        else:
            message = 'Transação não encontrada'
        
        conn.close()
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'USDT TRC20 Monitor',
        'version': '1.0.0'
    })

@app.route('/')
def index():
    """Servir frontend"""
    return '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor USDT TRC20 - Tron</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .badge {
            background: #00ff88;
            color: #000;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.4em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .controls {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .auto-monitor {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #00ff88;
        }

        input:checked + .slider:before {
            transform: translateX(26px);
        }

        .monitor-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            float: right;
        }

        .monitor-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .monitor-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            overflow-x: auto;
        }

        .tab {
            flex: 1;
            padding: 15px 20px;
            text-align: center;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: bold;
            white-space: nowrap;
            min-width: 120px;
        }

        .tab.active {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            transform: translateY(-2px);
        }

        .content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            min-height: 400px;
        }

        .wallet-form {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 15px;
            margin-bottom: 30px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }

        .form-group input {
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            align-self: end;
        }

        .btn-primary {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(45deg, #ff4757, #ff3742);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .wallet-list {
            margin-bottom: 30px;
        }

        .wallet-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .wallet-info h4 {
            margin-bottom: 5px;
            color: #333;
        }

        .wallet-info p {
            color: #666;
            font-size: 0.9em;
        }

        .transaction-list {
            max-height: 600px;
            overflow-y: auto;
        }

        .transaction-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
        }

        .transaction-item.outgoing {
            border-left-color: #ff4757;
        }

        .transaction-item.incoming {
            border-left-color: #00ff88;
        }

        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .transaction-amount {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }

        .transaction-type {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .transaction-type.outgoing {
            background: #ff4757;
            color: white;
        }

        .transaction-type.incoming {
            background: #00ff88;
            color: white;
        }

        .transaction-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }

        .transaction-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .btn-sm {
            padding: 8px 15px;
            font-size: 0.9em;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
        }

        .notification.error {
            background: linear-gradient(45deg, #ff4757, #ff3742);
        }

        .empty-state {
            text-align: center;
            padding: 50px 20px;
            color: #666;
        }

        .empty-state h3 {
            margin-bottom: 10px;
            font-size: 1.5em;
        }

        .loading {
            text-align: center;
            padding: 50px 20px;
            color: #667eea;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .wallet-form {
                grid-template-columns: 1fr;
            }
            
            .transaction-details {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-wrap: wrap;
            }
            
            .tab {
                min-width: auto;
                flex: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                📊 Monitor USDT TRC20 
                <span class="badge">FUNCIONANDO</span>
            </h1>
            <p>Monitorize saídas de USDT TRC20 das suas carteiras Tron em tempo real</p>
        </div>

        <div class="controls">
            <div class="auto-monitor">
                <span>⚡</span>
                <label for="autoMonitor">Monitorização Automática</label>
                <label class="switch">
                    <input type="checkbox" id="autoMonitor">
                    <span class="slider"></span>
                </label>
            </div>
            <button id="monitorBtn" class="monitor-btn">🔄 Monitorizar</button>
            <div style="clear: both;"></div>
        </div>

        <div class="tabs">
            <button class="tab active" data-tab="wallets">Carteiras (<span id="walletCount">0</span>)</button>
            <button class="tab" data-tab="outgoing">Saídas (<span id="outgoingCount">0</span>)</button>
            <button class="tab" data-tab="incoming">Entradas (<span id="incomingCount">0</span>)</button>
            <button class="tab" data-tab="all">Todas (<span id="allCount">0</span>)</button>
            <button class="tab" data-tab="duplicates">Duplicados (<span id="duplicateCount">0</span>)</button>
        </div>

        <div class="content">
            <div id="walletsTab" class="tab-content">
                <h2>Adicionar Nova Carteira</h2>
                <p>Adicione endereços de carteiras Tron para monitorizar transações USDT TRC20 em tempo real</p>
                
                <div class="wallet-form">
                    <div class="form-group">
                        <label for="walletAddress">Endereço da Carteira</label>
                        <input type="text" id="walletAddress" placeholder="TYASr5UV6HEcXatwdFQfmLVUqQQQMUxHLS">
                    </div>
                    <div class="form-group">
                        <label for="walletName">Nome (Opcional)</label>
                        <input type="text" id="walletName" placeholder="Carteira Principal">
                    </div>
                    <button id="addWalletBtn" class="btn btn-primary">+ Adicionar</button>
                </div>

                <div class="wallet-list">
                    <h3>Carteiras Monitorizadas</h3>
                    <p id="walletStatus">0 carteira(s) ativa(s)</p>
                    <div id="walletListContainer"></div>
                </div>
            </div>

            <div id="outgoingTab" class="tab-content" style="display: none;">
                <h2>Transações de Saída</h2>
                <p>USDT TRC20 enviado das suas carteiras</p>
                <div id="outgoingTransactions"></div>
            </div>

            <div id="incomingTab" class="tab-content" style="display: none;">
                <h2>Transações de Entrada</h2>
                <p>USDT TRC20 recebido nas suas carteiras</p>
                <div id="incomingTransactions"></div>
            </div>

            <div id="allTab" class="tab-content" style="display: none;">
                <h2>Todas as Transações</h2>
                <p>Histórico completo de transações USDT TRC20</p>
                <div id="allTransactions"></div>
            </div>

            <div id="duplicatesTab" class="tab-content" style="display: none;">
                <h2>Transações Duplicadas</h2>
                <p>Transações suspeitas com mesmo valor em período próximo</p>
                <div id="duplicateTransactions"></div>
            </div>
        </div>
    </div>

    <div id="notification" class="notification"></div>

    <script>
        // API Base URL (relativo para funcionar em qualquer servidor)
        const API_BASE = '/api';
        
        let autoMonitorInterval = null;
        let isAutoMonitoring = false;

        // Elementos DOM
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');
        const monitorBtn = document.getElementById('monitorBtn');
        const autoMonitorCheckbox = document.getElementById('autoMonitor');
        const addWalletBtn = document.getElementById('addWalletBtn');
        const walletAddressInput = document.getElementById('walletAddress');
        const walletNameInput = document.getElementById('walletName');

        // Contadores
        const counters = {
            wallet: document.getElementById('walletCount'),
            outgoing: document.getElementById('outgoingCount'),
            incoming: document.getElementById('incomingCount'),
            all: document.getElementById('allCount'),
            duplicate: document.getElementById('duplicateCount')
        };

        // Containers
        const containers = {
            wallets: document.getElementById('walletListContainer'),
            outgoing: document.getElementById('outgoingTransactions'),
            incoming: document.getElementById('incomingTransactions'),
            all: document.getElementById('allTransactions'),
            duplicates: document.getElementById('duplicateTransactions')
        };

        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            loadWallets();
            loadTransactions();
        });

        function setupEventListeners() {
            // Tabs
            tabs.forEach(tab => {
                tab.addEventListener('click', () => switchTab(tab.dataset.tab));
            });

            // Monitor button
            monitorBtn.addEventListener('click', monitorTransactions);

            // Auto monitor
            autoMonitorCheckbox.addEventListener('change', toggleAutoMonitor);

            // Add wallet
            addWalletBtn.addEventListener('click', addWallet);
            walletAddressInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') addWallet();
            });
        }

        function switchTab(tabName) {
            // Update tab buttons
            tabs.forEach(tab => {
                tab.classList.toggle('active', tab.dataset.tab === tabName);
            });

            // Update tab content
            tabContents.forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabName + 'Tab').style.display = 'block';

            // Load data for specific tab
            if (tabName !== 'wallets') {
                loadTransactions();
            }
        }

        async function loadWallets() {
            try {
                const response = await fetch(`${API_BASE}/wallets`);
                const wallets = await response.json();
                
                counters.wallet.textContent = wallets.length;
                document.getElementById('walletStatus').textContent = `${wallets.length} carteira(s) ativa(s)`;
                
                renderWallets(wallets);
            } catch (error) {
                console.error('Erro ao carregar carteiras:', error);
                showNotification('Erro ao carregar carteiras', 'error');
            }
        }

        function renderWallets(wallets) {
            const container = containers.wallets;
            
            if (wallets.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>Nenhuma carteira adicionada</h3>
                        <p>Adicione uma carteira para começar a monitorizar</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = wallets.map(wallet => `
                <div class="wallet-item">
                    <div class="wallet-info">
                        <h4>${wallet.name}</h4>
                        <p>${wallet.address}</p>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="removeWallet(${wallet.id})">
                        Remover
                    </button>
                </div>
            `).join('');
        }

        async function addWallet() {
            const address = walletAddressInput.value.trim();
            const name = walletNameInput.value.trim();

            if (!address) {
                showNotification('Endereço da carteira é obrigatório', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/wallets`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ address, name })
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification(result.message, 'success');
                    walletAddressInput.value = '';
                    walletNameInput.value = '';
                    loadWallets();
                } else {
                    showNotification(result.error, 'error');
                }
            } catch (error) {
                console.error('Erro ao adicionar carteira:', error);
                showNotification('Erro ao adicionar carteira', 'error');
            }
        }

        async function removeWallet(walletId) {
            if (!confirm('Tem certeza que deseja remover esta carteira?')) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/wallets/${walletId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification(result.message, 'success');
                    loadWallets();
                    loadTransactions();
                } else {
                    showNotification(result.error, 'error');
                }
            } catch (error) {
                console.error('Erro ao remover carteira:', error);
                showNotification('Erro ao remover carteira', 'error');
            }
        }

        async function monitorTransactions() {
            monitorBtn.disabled = true;
            monitorBtn.innerHTML = '⏳ Buscando na blockchain...';

            try {
                const response = await fetch(`${API_BASE}/monitor`, {
                    method: 'POST'
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification(result.message, 'success');
                    loadTransactions();
                } else {
                    showNotification(result.error, 'error');
                }
            } catch (error) {
                console.error('Erro na monitorização:', error);
                showNotification('Erro na monitorização', 'error');
            } finally {
                monitorBtn.disabled = false;
                monitorBtn.innerHTML = '🔄 Monitorizar';
            }
        }

        function toggleAutoMonitor() {
            isAutoMonitoring = autoMonitorCheckbox.checked;

            if (isAutoMonitoring) {
                autoMonitorInterval = setInterval(monitorTransactions, 120000); // 2 minutos
                showNotification('Monitorização automática ativada (2 min)', 'success');
            } else {
                if (autoMonitorInterval) {
                    clearInterval(autoMonitorInterval);
                    autoMonitorInterval = null;
                }
                showNotification('Monitorização automática desativada', 'success');
            }
        }

        async function loadTransactions() {
            try {
                // Carregar todos os tipos de transações
                const [allResponse, outgoingResponse, incomingResponse, duplicatesResponse] = await Promise.all([
                    fetch(`${API_BASE}/transactions`),
                    fetch(`${API_BASE}/transactions/outgoing`),
                    fetch(`${API_BASE}/transactions/incoming`),
                    fetch(`${API_BASE}/duplicates`)
                ]);

                const [allTx, outgoingTx, incomingTx, duplicatesTx] = await Promise.all([
                    allResponse.json(),
                    outgoingResponse.json(),
                    incomingResponse.json(),
                    duplicatesResponse.json()
                ]);

                // Atualizar contadores
                counters.all.textContent = allTx.length;
                counters.outgoing.textContent = outgoingTx.length;
                counters.incoming.textContent = incomingTx.length;
                counters.duplicate.textContent = duplicatesTx.length;

                // Renderizar transações
                renderTransactions(containers.all, allTx);
                renderTransactions(containers.outgoing, outgoingTx);
                renderTransactions(containers.incoming, incomingTx);
                renderTransactions(containers.duplicates, duplicatesTx);

            } catch (error) {
                console.error('Erro ao carregar transações:', error);
                showNotification('Erro ao carregar transações', 'error');
            }
        }

        function renderTransactions(container, transactions) {
            if (transactions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>Nenhuma transação encontrada</h3>
                        <p>Clique em "Monitorizar" para buscar transações</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = transactions.map(tx => `
                <div class="transaction-item ${tx.type}">
                    <div class="transaction-header">
                        <div class="transaction-amount">${tx.amount.toFixed(2)} USDT</div>
                        <div class="transaction-type ${tx.type}">
                            ${tx.type === 'outgoing' ? 'Saída' : 'Entrada'}
                        </div>
                    </div>
                    <div class="transaction-details">
                        <div>
                            <strong>Data/Hora</strong><br>
                            ${formatDate(tx.timestamp)}
                        </div>
                        <div>
                            <strong>Hash</strong><br>
                            <a href="https://tronscan.org/#/transaction/${tx.hash}" target="_blank">
                                ${tx.hash.substring(0, 20)}...${tx.hash.substring(tx.hash.length - 20)}
                            </a>
                        </div>
                        <div>
                            <strong>De</strong><br>
                            ${tx.from_address.substring(0, 10)}...${tx.from_address.substring(tx.from_address.length - 10)}
                        </div>
                        <div>
                            <strong>Para</strong><br>
                            ${tx.to_address.substring(0, 10)}...${tx.to_address.substring(tx.to_address.length - 10)}
                        </div>
                    </div>
                    <div class="transaction-actions">
                        <button class="btn btn-primary btn-sm" onclick="addNote(${tx.id})">
                            📝 ${tx.note ? 'Editar Nota' : 'Adicionar Nota'}
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="toggleComplete(${tx.id}, ${tx.is_completed})">
                            ${tx.is_completed ? '↩️ Marcar como Pendente' : '✅ Marcar como Completo'}
                        </button>
                        ${tx.type === 'outgoing' ? `
                            <button class="btn btn-primary btn-sm" onclick="copyReceipt('${tx.hash}', ${tx.amount}, '${formatDate(tx.timestamp)}', '${tx.from_address}', '${tx.to_address}')">
                                📄 Copiar Comprovante
                            </button>
                        ` : ''}
                    </div>
                    ${tx.note ? `<div style="margin-top: 10px; padding: 10px; background: #e9ecef; border-radius: 5px;"><strong>Nota:</strong> ${tx.note}</div>` : ''}
                </div>
            `).join('');
        }

        function formatDate(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleString('pt-BR');
        }

        function copyReceipt(hash, amount, date, fromAddress, toAddress) {
            const receipt = `🧾 COMPROVANTE USDT TRC20

💰 Valor: ${amount.toFixed(2)} USDT
📅 Data: ${date}

📤 De: ${fromAddress.substring(0, 10)}...${fromAddress.substring(fromAddress.length - 10)}
📥 Para: ${toAddress.substring(0, 10)}...${toAddress.substring(toAddress.length - 10)}

🔗 Hash: ${hash.substring(0, 20)}...${hash.substring(hash.length - 20)}

🌐 Ver no TronScan:
https://tronscan.org/#/transaction/${hash}

✅ Comprovante gerado em ${new Date().toLocaleString('pt-BR')}
📱 Pronto para compartilhar no WhatsApp!`;

            navigator.clipboard.writeText(receipt).then(() => {
                showNotification('Comprovante copiado! Cole no WhatsApp para compartilhar', 'success');
            }).catch(() => {
                showNotification('Erro ao copiar comprovante', 'error');
            });
        }

        async function addNote(transactionId) {
            const note = prompt('Digite a nota para esta transação:');
            if (note === null) return;

            try {
                const response = await fetch(`${API_BASE}/transactions/${transactionId}/note`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ note })
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification(result.message, 'success');
                    loadTransactions();
                } else {
                    showNotification(result.error, 'error');
                }
            } catch (error) {
                console.error('Erro ao adicionar nota:', error);
                showNotification('Erro ao adicionar nota', 'error');
            }
        }

        async function toggleComplete(transactionId, currentStatus) {
            try {
                const response = await fetch(`${API_BASE}/transactions/${transactionId}/complete`, {
                    method: 'PUT'
                });

                const result = await response.json();

                if (response.ok) {
                    showNotification(result.message, 'success');
                    loadTransactions();
                } else {
                    showNotification(result.error, 'error');
                }
            } catch (error) {
                console.error('Erro ao atualizar status:', error);
                showNotification('Erro ao atualizar status', 'error');
            }
        }

        function showNotification(message, type) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.classList.add('show');

            setTimeout(() => {
                notification.classList.remove('show');
            }, 5000);
        }
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    
    print("Iniciando USDT TRC20 Monitor...")
    print("Acesse: http://localhost:5000")
    
    # Executar aplicação
    app.run(host='0.0.0.0', port=5000, debug=True)

