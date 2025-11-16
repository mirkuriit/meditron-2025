#!/usr/bin/env python3
"""
Простой прокси-сервер для обхода CORS ограничений
Перенаправляет запросы с фронтенда на бэкенд
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

BACKEND_URL = "http://89.169.174.45:8010"

class CORSProxyHandler(SimpleHTTPRequestHandler):
    """HTTP обработчик с поддержкой CORS и проксирования API запросов"""
    
    def end_headers(self):
        """Добавляем CORS заголовки ко всем ответам"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Обработка preflight запросов"""
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Обработка POST запросов"""
        # Проверяем, это API запрос или обычный файл
        if self.path.startswith('/api/'):
            self.proxy_api_request()
        else:
            super().do_POST()
    
    def proxy_api_request(self):
        """Проксирование API запросов на бэкенд"""
        try:
            # Читаем тело запроса
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Формируем URL бэкенда (убираем /api/ префикс)
            backend_path = self.path.replace('/api/', '/')
            backend_full_url = f"{BACKEND_URL}{backend_path}"
            
            print(f"📤 Проксирование запроса: {backend_full_url}")
            print(f"📦 Данные: {post_data.decode('utf-8')[:200]}...")
            
            # Создаем запрос к бэкенду
            req = urllib.request.Request(
                backend_full_url,
                data=post_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                method='POST'
            )
            
            # Отправляем запрос
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    response_data = response.read()
                    
                    print(f"✅ Успешный ответ от бэкенда (статус: {response.status})")
                    
                    # Отправляем успешный ответ клиенту
                    self.send_response(response.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(response_data)
                    
            except urllib.error.HTTPError as e:
                # Бэкенд вернул ошибку
                error_data = e.read().decode('utf-8')
                print(f"❌ Ошибка от бэкенда (статус: {e.code}): {error_data}")
                
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(error_data.encode())
                
        except Exception as e:
            print(f"❌ Ошибка проксирования: {e}")
            
            # Отправляем ошибку клиенту
            error_response = json.dumps({
                'error': str(e),
                'message': 'Ошибка проксирования запроса'
            })
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def log_message(self, format, *args):
        """Логирование запросов"""
        if not self.path.startswith('/api/'):
            # Не логируем статические файлы
            return
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8080):
    """Запуск прокси-сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSProxyHandler)
    
    print("=" * 60)
    print(f"🚀 Прокси-сервер запущен на http://localhost:{port}")
    print(f"🔗 Проксирует запросы на {BACKEND_URL}")
    print("=" * 60)
    print("\n📋 Использование:")
    print(f"   - Откройте http://localhost:{port} в браузере")
    print(f"   - API запросы отправляйте на /api/reports/...")
    print("\n💡 Для остановки нажмите Ctrl+C\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Сервер остановлен")
        httpd.server_close()


if __name__ == '__main__':
    run_server(5500)

