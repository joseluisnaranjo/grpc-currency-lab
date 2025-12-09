import time
from concurrent import futures
import grpc
import currency_pb2
import currency_pb2_grpc
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tasas simuladas iniciales: map[from][to] = rate (1 unit of from = rate units of to)
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "JPY": 149.50, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "JPY": 162.50, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "JPY": 190.50, "GBP": 1.0},
    "JPY": {"USD": 0.0067, "EUR": 0.0062, "GBP": 0.0053, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]

def fetch_real_rates(from_currency):
    
    # Obtener tasas reales desde una API pública
    
    try:
        url = f"https://api.frankfurter.app/latest?from={from_currency}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            logger.info(f"Tasas reales obtenidas para {from_currency}: {rates}")
            return rates
    except requests.RequestException as e:
        logger.warning(f"Error al obtener tasas reales: {e}. Usando tasas simuladas.")
    return None

class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        amt = request.amount
        
        # Intentar obtener tasas reales
        real_rates = fetch_real_rates(from_c)
        
        rate = None
        if real_rates and to_c in real_rates:
            rate = real_rates[to_c]
        elif from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
            rate = SIMULATED_RATES[from_c][to_c]
        elif to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
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

    def GetRate(self, request, context):
        # Obtener solo la tasa de cambio sin convertir cantidad
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        
        # Intentar obtener tasas reales
        real_rates = fetch_real_rates(from_c)
        
        rate = None
        if real_rates and to_c in real_rates:
            rate = real_rates[to_c]
        elif from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
            rate = SIMULATED_RATES[from_c][to_c]
        elif to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
            rate = 1.0 / SIMULATED_RATES[to_c][from_c]
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Rate not found for {from_c} -> {to_c}")
            return currency_pb2.RateReply()
        
        return currency_pb2.RateReply(
            rate=rate,
            from_currency=from_c,
            to_currency=to_c
        )

    def StreamRates(self, request, context):
        # Simula envíos periódicos de tasas (ejemplo didáctico)
        while True:
            for from_c, targets in SIMULATED_RATES.items():
                for to_c, rate in targets.items():
                    if from_c == to_c:
                        continue
                    reply = currency_pb2.ConvertReply(
                        converted_amount=rate,
                        rate=rate,
                        from_currency=from_c,
                        to_currency=to_c
                    )
                    yield reply
                    time.sleep(0.5)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    server.start()
    print(f"gRPC CurrencyConverter server started on {listen_addr}")
    print(": USD, EUR, GBP, JPY")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Server stopping")

if __name__ == "__main__":
    serve()
