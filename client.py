import time
import grpc
from proto import currency_pb2
from proto import currency_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = currency_pb2_grpc.CurrencyConverterStub(channel)

    # 1) Obtener monedas soportadas (server-stream)
    print("Monedas soportadas:")
    try:
        for currency in stub.GetSupportedCurrencies(currency_pb2.Empty()):
            print(f" - {currency.code}: {currency.name}")
    except grpc.RpcError as e:
        print("Error GetSupportedCurrencies:", e)

    # 2) Probar GetRate (nuevo método)
    print("\nProbando GetRate USD -> JPY:")
    try:
        rate_reply = stub.GetRate(
            currency_pb2.RateRequest(from_currency="USD", to_currency="JPY")
        )
        print(f"Tasa USD -> JPY = {rate_reply.rate}")
    except grpc.RpcError as e:
        print("GetRate error:", e)

    # 3) Ejemplo de Convert (unary)
    req = currency_pb2.ConvertRequest(from_currency="AAA", to_currency="EUR", amount=100.0)
    try:
        reply = stub.Convert(req)
        print(
            f"\nConvert {req.amount} {req.from_currency} -> "
            f"{reply.converted_amount:.4f} {reply.to_currency} (rate={reply.rate})"
        )
    except grpc.RpcError as e:
        print("Convert error:", e)

    # 4) Escuchar StreamRates por 5 elementos (server stream)
    print("\nStream de tasas (ejemplo, 5 items):")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        for i, item in enumerate(stream):
            print(f" {i+1}) {item.from_currency} -> {item.to_currency} : rate={item.rate}")
            if i >= 4:
                break
    except grpc.RpcError as e:
        print("StreamRates error:", e)


if __name__ == "__main__":
    run()
