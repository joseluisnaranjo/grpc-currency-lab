import time
from concurrent import futures
import requests
import grpc
import currency_pb2
import currency_pb2_grpc

URL = "https://api.frankfurter.dev/v1"

# Tasas simuladas: map[from][to] = rate (1 unit of from = rate units of to)
SIMULATED_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "USD": 1.0, "JPY": 156.8},
    "EUR": {"USD": 1.087, "GBP": 0.85, "EUR": 1.0, "JPY": 182.3},
    "GBP": {"USD": 1.28, "EUR": 1.17, "GBP": 1.0, "JPY": 208.6},
    "JPY": {"USD": 0.0064, "EUR": 0.0055, "GBP": 0.0048, "JPY": 1.0},
}

SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]

class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        amt = request.amount
        # rate lookup with simple fallback
        rate = None

        try:
            if from_c == to_c:
                rate = 1.0
            else:
                response = requests.get(f"{URL}/latest", params={"base": from_c, "symbols": to_c})
                data = response.json()
                if "rates" in data and to_c in data["rates"]:
                    rate = data["rates"][to_c]
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
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error during conversion: {e}")
            return currency_pb2.ConvertReply()



    def GetSupportedCurrencies(self, request, context):
        try:
            response = requests.get(URL+"/currencies")
            data = response.json()
            for code, name in data.items():
                yield currency_pb2.Currency(code=code, name=name)
        except Exception as e:
            print("Error fetching currencies from API, using simulated list:", e)

    def GetRate(self, request, context):
        from_c = request.from_currency.upper()
        to_c = request.to_currency.upper()
        # rate lookup with simple fallback
        rate = None
        try:
            if from_c == to_c:
                rate = 1.0
            else:
                response = requests.get(f"{URL}/latest", params={"base": from_c, "symbols": to_c})
                data = response.json()
                if "rates" in data and to_c in data["rates"]:
                    rate = data["rates"][to_c]
                else:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Rate not found for {from_c} -> {to_c}")
                    return currency_pb2.RateReply()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error fetching rate: {e}")
            return currency_pb2.RateReply()

        return currency_pb2.RateReply(rate=rate)

    def StreamRates(self, request, context):
        # Simula envíos periódicos de tasas (ejemplo didáctico)
        while True:
            try:
                response = requests.get(URL+"/currencies")
                data = response.json()
                data = {k: list(data.keys()) for k in data.keys()}
                print(data)  # preparar estructura simple                
                for (from_c, targets) in data.items():
                    for target in targets:
                        to_c = target
                        if from_c == to_c:
                            continue
                        response2 = requests.get(f"{URL}/latest", params={"base": from_c, "symbols": to_c})
                        data2 = response2.json()
                        if "rates" in data2 and to_c in data2["rates"]:
                            rate = data2["rates"][to_c]
                        reply = currency_pb2.ConvertReply(
                            converted_amount=rate, # en este stream 'converted_amount' usaremos como valor de tasa
                            rate=rate,
                            from_currency=from_c,
                            to_currency=to_c
                        )
                        yield reply
                        time.sleep(0.5)  # espera simulada
            # repetir (podrías agregar lógica para salir si context.is_active() == False)
            except Exception as e:
                print("Error during StreamRates:", e)
                break

def serve():
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
