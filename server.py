import grpc
from concurrent import futures
import time
import requests  
from proto import currency_pb2
from proto import currency_pb2_grpc

# Estructura base de tasas (se actualizarán con datos reales al iniciar)
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "JPY": 150.0, "MXN": 17.5, "USD": 1.0},
    "EUR": {"USD": 1.08, "GBP": 0.85, "JPY": 163.5, "MXN": 18.9, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "JPY": 191.2, "MXN": 22.1, "GBP": 1.0},
    "JPY": {"USD": 0.006, "EUR": 0.006, "GBP": 0.005, "MXN": 0.11, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
    ("MXN", "Mexican Peso"),
]

def fetch_real_rates():
    """
    Se conecta a una API pública (Frankfurter) para obtener tasas reales.
    Si falla, el servidor seguirá funcionando con los valores por defecto.
    """
    print("Conectando a API externa para actualizar tasas...")
    try:
        # Consultamos tasas con base en USD
        url = "https://api.frankfurter.app/latest?from=USD"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "rates" in data:
                rates = data["rates"]
                # Actualizamos las tasas de USD a otras monedas
                for currency, rate in rates.items():
                    # Solo actualizamos si la moneda está en nuestro sistema
                    if currency in ["EUR", "GBP", "JPY", "MXN"]:
                        SIMULATED_RATES["USD"][currency] = rate
                        
                        # Calculamos la inversa aproximada (Ej: EUR -> USD)
                        if currency not in SIMULATED_RATES:
                            SIMULATED_RATES[currency] = {}
                        SIMULATED_RATES[currency]["USD"] = 1.0 / rate
                        # Aseguramos que la moneda se convierta a sí misma en 1.0
                        SIMULATED_RATES[currency][currency] = 1.0
                        
                print("Tasas actualizadas con datos reales de Frankfurter API.")
        else:
            print(f"La API respondió con código: {response.status_code}")
            
    except Exception as e:
        print(f"No se pudo conectar a la API (usando tasas simuladas): {e}")

class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        amt = request.amount
        
        rate = None
        
        # Lógica de búsqueda de tasa (Directa o Inversa)
        if from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
            rate = SIMULATED_RATES[from_c][to_c]
        elif to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
            rate = 1.0 / SIMULATED_RATES[to_c][from_c]
            
        if rate is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Tasa no encontrada para {from_c} -> {to_c}")
            return currency_pb2.ConvertReply()

        converted = amt * rate
        return currency_pb2.ConvertReply(
            converted_amount=converted,
            rate=rate,
            from_currency=from_c,
            to_currency=to_c
        )

    def GetSupportedCurrencies(self, request, context):
        for code, name in SUPPORTED:
            yield currency_pb2.Currency(code=code, name=name)

    def StreamRates(self, request, context):
        # Simula envíos periódicos de tasas
        print("📡 Iniciando stream de tasas...")
        try:
            while True:
                # Recorremos algunas tasas principales para enviarlas
                for from_c in ["USD", "EUR"]:
                    if from_c in SIMULATED_RATES:
                        for to_c, rate in SIMULATED_RATES[from_c].items():
                            if from_c == to_c: continue
                            
                            reply = currency_pb2.ConvertReply(
                                converted_amount=rate, 
                                rate=rate,
                                from_currency=from_c,
                                to_currency=to_c
                            )
                            yield reply
                            time.sleep(0.5) # Pausa para no saturar
        except Exception as e:
            print(f"Stream finalizado: {e}")

def serve():
    # 1. Llamamos a la API antes de iniciar el servidor
    fetch_real_rates()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    server.start()
    print(f"Servidor gRPC corriendo en {listen_addr}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Servidor detenido.")

if __name__ == "__main__":
    serve()