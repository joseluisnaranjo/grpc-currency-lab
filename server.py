import time
from concurrent import futures
import grpc
import requests

from proto import currency_pb2
from proto import currency_pb2_grpc


def fetch_rate_real(from_c: str, to_c: str) -> float:
    url = f"https://api.frankfurter.app/latest?from={from_c}&to={to_c}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    data = r.json()
    return float(data["rates"][to_c])


# Tasas simuladas
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "JPY": 150.0, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "JPY": 160.0, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "JPY": 190.0, "GBP": 1.0},
    "JPY": {"USD": 1/150.0, "EUR": 1/160.0, "GBP": 1/190.0, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]


class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):

    # Desafío: solo devuelve la tasa
    def GetRate(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()

        # 1) Intentar API real
        try:
            real_rate = fetch_rate_real(from_c, to_c)
            SIMULATED_RATES.setdefault(from_c, {})[to_c] = real_rate
            return currency_pb2.RateReply(rate=real_rate)

        except Exception:
            # 2) Fallback a simuladas
            rate = SIMULATED_RATES.get(from_c, {}).get(to_c)

            if rate is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Rate not found for {from_c} -> {to_c}")
                return currency_pb2.RateReply(rate=0)

            return currency_pb2.RateReply(rate=rate)

    # Conversión unary
    def Convert(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        amt = request.amount

        # 1) Intentar API real
        try:
            rate = fetch_rate_real(from_c, to_c)
            SIMULATED_RATES.setdefault(from_c, {})[to_c] = rate

        except Exception:
            # 2) Fallback simuladas
            rate = SIMULATED_RATES.get(from_c, {}).get(to_c)

        if rate is None:
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

    # Server-streaming: lista monedas soportadas
    def GetSupportedCurrencies(self, request, context):
        for code, name in SUPPORTED:
            yield currency_pb2.Currency(code=code, name=name)

    # Opcional: streaming de tasas simuladas
    # (usa ConvertReply porque tu proto original lo define así)
    def StreamRates(self, request, context):
        while True:
            for from_c, targets in SIMULATED_RATES.items():
                for to_c, rate in targets.items():
                    if from_c == to_c:
                        continue

                    yield currency_pb2.ConvertReply(
                        converted_amount=rate,  # aquí se usa como valor informativo
                        rate=rate,
                        from_currency=from_c,
                        to_currency=to_c
                    )
                    time.sleep(0.4)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(
        CurrencyConverterServicer(), server
    )

    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC CurrencyConverter server running on port 50051...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
