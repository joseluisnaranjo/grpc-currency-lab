import time
from concurrent import futures
import grpc
import proto.currency_pb2 as currency_pb2
import proto.currency_pb2_grpc as currency_pb2_grpc
import requests  # Se añadió esta importación


# Tasas simuladas: map[from][to] = rate (1 unit of from = rate units of to)
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "GBP": 1.0},

    # NUEVAS MONEDAS
    "JPY": {"USD": 0.0067, "EUR": 0.0061, "GBP": 0.0052, "JPY": 1.0, "MXN": 0.11},
    "MXN": {"USD": 0.059, "EUR": 0.054, "GBP": 0.045, "JPY": 9.0, "MXN": 1.0}
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
    ("MXN", "Mexican Peso"),
]


class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    """
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
    """ 

    def Convert(self, request, context):
        moneda_origen = request.from_currency.upper()
        moneda_destino = request.to_currency.upper()
        monto = request.amount

        # URL de la API real
        url = f"https://open.er-api.com/v6/latest/{moneda_origen}"

        try:
            respuesta = requests.get(url, timeout=5)
            datos = respuesta.json()

            # Si la moneda origen no existe
            if datos.get("result") != "success":
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"La moneda {moneda_origen} no existe en la API")
                return currency_pb2.ConvertReply()

            tasas = datos.get("rates", {})

            # Si no existe la moneda destino
            if moneda_destino not in tasas:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"No existe tasa para {moneda_origen} -> {moneda_destino}")
                return currency_pb2.ConvertReply()

            # Tasa real
            tasa_conversion = tasas[moneda_destino]

            # Conversión
            monto_convertido = monto * tasa_conversion

            return currency_pb2.ConvertReply(
                converted_amount=monto_convertido,
                rate=tasa_conversion,
                from_currency=moneda_origen,
                to_currency=moneda_destino
            )

        except Exception as error:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error API: {str(error)}")
            return currency_pb2.ConvertReply()

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
                        converted_amount=rate,  
                        rate=rate,
                        from_currency=from_c,
                        to_currency=to_c
                    )
                    yield reply
                    time.sleep(0.5)  # espera simulada

    # NUEVO MÉTODO CREADO
    def GetRate(self, request, context):
        moneda_origen = request.from_currency.upper()
        moneda_destino = request.to_currency.upper()

        url = f"https://open.er-api.com/v6/latest/{moneda_origen}"

        try:
            r = requests.get(url, timeout=5)
            data = r.json()

            if data.get("result") != "success":
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"La moneda {moneda_origen} no existe en la API")
                return currency_pb2.RateReply()

            tasas = data.get("rates", {})

            if moneda_destino not in tasas:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"No existe tasa para {moneda_origen} -> {moneda_destino}")
                return currency_pb2.RateReply()

            tasa = tasas[moneda_destino]
            return currency_pb2.RateReply(rate=tasa)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error API: {str(e)}")
            return currency_pb2.RateReply()
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC CurrencyConverter server started on [::]:50051")

    try:
        server.wait_for_termination()  # Esto mantiene el servidor corriendo
    except KeyboardInterrupt:
        print("Servidor detenido manualmente")


if __name__ == "__main__":
    serve()
