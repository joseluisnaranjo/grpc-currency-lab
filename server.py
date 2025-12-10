import time
from concurrent import futures
import grpc
import requests  # ✅ NUEVO
from proto import currency_pb2
from proto import currency_pb2_grpc

# Endpoint base de la Frankfurter API
FRANKFURTER_URL = "https://api.frankfurter.app/latest"

# Tasas simuladas: map[from][to] = rate (1 unit of from = rate units of to)
# Ahora sirven como "cache" / respaldo si la API falla.
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "JPY": 150.0, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "JPY": 163.0, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "JPY": 190.0, "GBP": 1.0},
    "JPY": {"USD": 0.0067, "EUR": 0.0061, "GBP": 0.0053, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]


def fetch_rate_from_api(from_c: str, to_c: str):
    """
    Llama a la Frankfurter API para obtener la tasa from_c -> to_c.
    Devuelve la tasa (float) o None si hay error.
    """
    try:
        params = {"from": from_c, "to": to_c}
        resp = requests.get(FRANKFURTER_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # La API devuelve algo como: {"amount":1.0,"base":"USD","date":"2024-01-01","rates":{"EUR":0.92}}
        rate = data.get("rates", {}).get(to_c)
        if rate is None:
            return None

        # Guardamos en el diccionario como cache
        if from_c not in SIMULATED_RATES:
            SIMULATED_RATES[from_c] = {}
        SIMULATED_RATES[from_c][to_c] = rate

        return rate
    except Exception as e:
        print(f"[WARN] Error llamando a Frankfurter API ({from_c}->{to_c}): {e}")
        return None


def _get_rate(from_c: str, to_c: str, context):
    """
    Busca la tasa usando primero la API real y, si falla, el diccionario local.
    Si no existe, setea error en el contexto y devuelve None.
    """
    from_c = from_c.upper()
    to_c = to_c.upper()

    # 1) Intentar obtener tasa en tiempo real desde la API
    api_rate = fetch_rate_from_api(from_c, to_c)
    if api_rate is not None:
        return api_rate

    # 2) Respaldo: usar las tasas simuladas locales
    if from_c in SIMULATED_RATES and to_c in SIMULATED_RATES[from_c]:
        return SIMULATED_RATES[from_c][to_c]

    if to_c in SIMULATED_RATES and from_c in SIMULATED_RATES[to_c]:
        return 1.0 / SIMULATED_RATES[to_c][from_c]

    # 3) Si no encontramos nada, marcamos NOT_FOUND
    context.set_code(grpc.StatusCode.NOT_FOUND)
    context.set_details(f"Rate not found for {from_c} -> {to_c}")
    return None


class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        from_c = request.from_currency
        to_c = request.to_currency
        amt = request.amount

        rate = _get_rate(from_c, to_c, context)
        if rate is None:
            # Ya se seteó el error en el contexto
            return currency_pb2.ConvertReply()

        converted = amt * rate
        return currency_pb2.ConvertReply(
            converted_amount=converted,
            rate=rate,
            from_currency=from_c.upper(),
            to_currency=to_c.upper()
        )

    def GetSupportedCurrencies(self, request, context):
        for code, name in SUPPORTED:
            yield currency_pb2.Currency(code=code, name=name)

    def StreamRates(self, request, context):
        # Simula envíos periódicos de tasas (ejemplo didáctico)
        while context.is_active():
            for from_c, targets in SIMULATED_RATES.items():
                for to_c, rate in targets.items():
                    if from_c == to_c:
                        continue
                    reply = currency_pb2.ConvertReply(
                        converted_amount=rate,  # aquí usamos converted_amount como "valor de tasa"
                        rate=rate,
                        from_currency=from_c,
                        to_currency=to_c
                    )
                    yield reply
                    time.sleep(0.5)

    # ✅ Nuevo método GetRate
    def GetRate(self, request, context):
        rate = _get_rate(request.from_currency, request.to_currency, context)
        if rate is None:
            return currency_pb2.RateReply()
        return currency_pb2.RateReply(rate=rate)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(
        CurrencyConverterServicer(), server
    )
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
