import time
from concurrent import futures
import grpc
import currency_pb2
import currency_pb2_grpc
import requests  
import json

# Tasas simuladas: map[from][to] = rate (1 unit of from = rate units of to)
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "GBP": 1.0},
    "JPY": {"USD": 0.0066, "EUR": 0.0061, "GBP": 0.0052, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]

def fetch_live_rates():
    print("Conectando a API Frankfurter para actualizar tasas...")
    try:
        # Pedimos tasas con base en USD
        url = "https://api.frankfurter.app/latest?from=USD"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            rates = data['rates'] # Diccionario 
            
            # Actualizamos las tasas de USD en nuestro diccionario
            if 'EUR' in rates: SIMULATED_RATES['USD']['EUR'] = rates['EUR']
            if 'GBP' in rates: SIMULATED_RATES['USD']['GBP'] = rates['GBP']
            if 'JPY' in rates: SIMULATED_RATES['USD']['JPY'] = rates['JPY']
            
            # Recalculamos las inversas para mantener coherencia (opcional pero recomendado)
            SIMULATED_RATES['EUR']['USD'] = 1 / SIMULATED_RATES['USD']['EUR']
            SIMULATED_RATES['GBP']['USD'] = 1 / SIMULATED_RATES['USD']['GBP']
            SIMULATED_RATES['JPY']['USD'] = 1 / SIMULATED_RATES['USD']['JPY']
            
            print("¡Tasas actualizadas desde internet con éxito!")
            print(f"Nueva tasa USD -> EUR: {SIMULATED_RATES['USD']['EUR']}")
        else:
            print(f"Error en API: {response.status_code}")
    except Exception as e:
        print(f"No se pudo conectar a la API: {e}")

class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        amt = request.amount
        # rate lookup with simple fallback
        rate = None
        if from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
            rate = SIMULATED_RATES[from_c][to_c]
        elif to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
            # invert if stored the other way (not necessary here but safe)
            rate = 1.0 / SIMULATED_RATES[to_c][from_c]
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Rate not found for {from_c} -> {to_c}")
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
        # Simula envíos periódicos de tasas (ejemplo didáctico)
        while True:
            for from_c, targets in SIMULATED_RATES.items():
                for to_c, rate in targets.items():
                    if from_c == to_c:
                        continue
                    reply = currency_pb2.ConvertReply(
                        converted_amount=rate, # en este stream 'converted_amount' usaremos como valor de tasa
                        rate=rate,
                        from_currency=from_c,
                        to_currency=to_c
                    )
                    yield reply
                    time.sleep(0.5)  # espera simulada
            # repetir (podrías agregar lógica para salir si context.is_active() == False)

    def GetRate(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        
        # Buscamos la tasa 
        rate = None
        if from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
            rate = SIMULATED_RATES[from_c][to_c]
        elif to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
            rate = 1.0 / SIMULATED_RATES[to_c][from_c]
        
        if rate is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Tasa no encontrada")
            return currency_pb2.RateReply()

        return currency_pb2.RateReply(rate=rate)

def serve():
    fetch_live_rates()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    server.start()
    print(f"gRPC CurrencyConverter server started on {listen_addr}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Server stopping")

if __name__ == "__main__":
    serve()
