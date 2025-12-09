import grpc
from proto import currency_pb2
from proto import currency_pb2_grpc


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = currency_pb2_grpc.CurrencyConverterStub(channel)

        # 1) Monedas soportadas
        print("Monedas soportadas:")
        try:
            for currency in stub.GetSupportedCurrencies(currency_pb2.Empty()):
                print(f" - {currency.code}: {currency.name}")
        except grpc.RpcError as e:
            print("Error GetSupportedCurrencies:", e.code(), e.details())

        # 2) GetRate
        print("\nGetRate:")
        try:
            rate_reply = stub.GetRate(
                currency_pb2.RateRequest(from_currency="USD", to_currency="EUR")
            )
            print(" USD -> EUR rate:", rate_reply.rate)
        except grpc.RpcError as e:
            print("GetRate error:", e.code(), e.details())

        # 3) Convert
        print("\nConvert:")
        req = currency_pb2.ConvertRequest(from_currency="USD", to_currency="EUR", amount=100.0)
        try:
            reply = stub.Convert(req)
            print(f" {req.amount} {req.from_currency} -> {reply.converted_amount:.4f} {req.to_currency} (rate={reply.rate})")
        except grpc.RpcError as e:
            print("Convert error:", e.code(), e.details())

        # 4) Error controlado
        print("\nPrueba de error (moneda inexistente):")
        try:
            bad = currency_pb2.ConvertRequest(from_currency="USD", to_currency="ABC", amount=10)
            stub.Convert(bad)
        except grpc.RpcError as e:
            print(" ERROR esperado:", e.code(), e.details())

        # 5) StreamRates ( 5 items)
        print("\nStreamRates (5 items):")
        try:
            stream = stub.StreamRates(currency_pb2.Empty())
            for i, item in enumerate(stream):
                print(f" {i+1}) {item.from_currency} -> {item.to_currency} rate={item.rate}")
                if i >= 4:
                    break
        except grpc.RpcError as e:
            print("StreamRates error:", e.code(), e.details())


if __name__ == "__main__":
    run()
