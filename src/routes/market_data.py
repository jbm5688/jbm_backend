from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, emit
import requests
import asyncio
import aiohttp
import threading
import time
import json
from datetime import datetime

market_data_bp = Blueprint('market_data', __name__)

# Configuração das APIs
API_CONFIGS = {
    'brapi': {
        'base_url': 'https://brapi.dev/api',
        'endpoints': {
            'quote': '/quote/{symbols}',
            'available': '/available'
        }
    },
    'awesomeapi': {
        'base_url': 'https://economia.awesomeapi.com.br',
        'endpoints': {
            'currencies': '/last/{currencies}'
        }
    }
}

# Cache simples em memória (em produção usar Redis)
data_cache = {}
last_update = {}

class MarketDataService:
    def __init__(self):
        self.running = False
        self.update_interval = 5  # segundos
        
    async def fetch_brapi_data(self, symbols):
        """Busca dados de ações brasileiras via BRAPI"""
        try:
            symbols_str = ','.join(symbols)
            url = f"{API_CONFIGS['brapi']['base_url']}/quote/{symbols_str}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.normalize_brapi_data(data)
                    return None
        except Exception as e:
            print(f"Erro ao buscar dados BRAPI: {e}")
            return None
    
    async def fetch_currency_data(self, currencies):
        """Busca dados de moedas via AwesomeAPI"""
        try:
            currencies_str = ','.join(currencies)
            url = f"{API_CONFIGS['awesomeapi']['base_url']}/last/{currencies_str}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.normalize_currency_data(data)
                    return None
        except Exception as e:
            print(f"Erro ao buscar dados de moedas: {e}")
            return None
    
    def normalize_brapi_data(self, data):
        """Normaliza dados da BRAPI para formato padrão"""
        normalized = {}
        if 'results' in data:
            for stock in data['results']:
                symbol = stock.get('symbol', '')
                normalized[symbol] = {
                    'symbol': symbol,
                    'price': stock.get('regularMarketPrice', 0),
                    'change': stock.get('regularMarketChange', 0),
                    'changePercent': stock.get('regularMarketChangePercent', 0),
                    'volume': stock.get('regularMarketVolume', 0),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'brapi'
                }
        return normalized
    
    def normalize_currency_data(self, data):
        """Normaliza dados de moedas para formato padrão"""
        normalized = {}
        for currency_pair, info in data.items():
            normalized[currency_pair] = {
                'symbol': currency_pair,
                'price': float(info.get('bid', 0)),
                'change': float(info.get('varBid', 0)),
                'changePercent': float(info.get('pctChange', 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'awesomeapi'
            }
        return normalized
    
    async def update_market_data(self):
        """Atualiza dados de mercado de todas as fontes"""
        # Símbolos para buscar
        stock_symbols = ['PETR4', 'ITUB4', 'VALE3', 'MGLU3', 'BBDC4', 'WEGE3']
        currency_pairs = ['USD-BRL', 'EUR-BRL', 'BTC-BRL']
        
        # Buscar dados de ações
        stock_data = await self.fetch_brapi_data(stock_symbols)
        if stock_data:
            data_cache.update(stock_data)
        
        # Buscar dados de moedas
        currency_data = await self.fetch_currency_data(currency_pairs)
        if currency_data:
            data_cache.update(currency_data)
        
        last_update['timestamp'] = datetime.now().isoformat()
        return data_cache
    
    def start_background_updates(self, socketio):
        """Inicia atualizações em background"""
        def update_loop():
            while self.running:
                try:
                    # Executar atualização assíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    updated_data = loop.run_until_complete(self.update_market_data())
                    
                    # Emitir dados via WebSocket
                    socketio.emit('market_update', {
                        'data': updated_data,
                        'timestamp': last_update.get('timestamp')
                    })
                    
                    time.sleep(self.update_interval)
                except Exception as e:
                    print(f"Erro no loop de atualização: {e}")
                    time.sleep(self.update_interval)
        
        self.running = True
        thread = threading.Thread(target=update_loop)
        thread.daemon = True
        thread.start()
    
    def stop_background_updates(self):
        """Para atualizações em background"""
        self.running = False

# Instância global do serviço
market_service = MarketDataService()

@market_data_bp.route('/quote/<symbols>')
def get_quote(symbols):
    """Endpoint para buscar cotações específicas"""
    symbol_list = symbols.split(',')
    result = {}
    
    for symbol in symbol_list:
        if symbol in data_cache:
            result[symbol] = data_cache[symbol]
    
    return jsonify({
        'success': True,
        'data': result,
        'timestamp': last_update.get('timestamp'),
        'cached': True
    })

@market_data_bp.route('/all')
def get_all_data():
    """Endpoint para buscar todos os dados em cache"""
    return jsonify({
        'success': True,
        'data': data_cache,
        'timestamp': last_update.get('timestamp'),
        'count': len(data_cache)
    })

@market_data_bp.route('/status')
def get_status():
    """Endpoint para verificar status do serviço"""
    return jsonify({
        'success': True,
        'running': market_service.running,
        'last_update': last_update.get('timestamp'),
        'cached_symbols': list(data_cache.keys()),
        'update_interval': market_service.update_interval
    })

@market_data_bp.route('/start')
def start_updates():
    """Endpoint para iniciar atualizações automáticas"""
    if not market_service.running:
        # Nota: SocketIO será inicializado no main.py
        return jsonify({
            'success': True,
            'message': 'Serviço de atualização iniciado',
            'running': True
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Serviço já está rodando',
            'running': True
        })

@market_data_bp.route('/stop')
def stop_updates():
    """Endpoint para parar atualizações automáticas"""
    market_service.stop_background_updates()
    return jsonify({
        'success': True,
        'message': 'Serviço de atualização parado',
        'running': False
    })

# Função para inicializar o serviço com SocketIO
def init_market_service(socketio):
    """Inicializa o serviço de dados de mercado com SocketIO"""
    market_service.start_background_updates(socketio)

