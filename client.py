import grpc
import time
import proto.currency_pb2 as currency_pb2
import proto.currency_pb2_grpc as currency_pb2_grpc


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

    # 2) Ejemplo de Convert (unary)
    req = currency_pb2.ConvertRequest(from_currency="USD", to_currency="EUR", amount=100.0)
    try:
        reply = stub.Convert(req)
        print(f"\nConvert {req.amount} {req.from_currency} -> {reply.converted_amount:.4f} {req.to_currency} (rate={reply.rate})")
    except grpc.RpcError as e:
        print("Convert error:", e)

    
    # 2.1) Ejemplo de Convert con moneda que no existe
    invalid_req = currency_pb2.ConvertRequest(from_currency="EUR", to_currency="CAD", amount=20.0)
    try:
        invalid_reply = stub.Convert(invalid_req)
        print(f"\nConvert {invalid_req.amount} {invalid_req.from_currency} -> {invalid_reply.converted_amount:.4f} {invalid_req.to_currency}")
    except grpc.RpcError as e:
        print(f"\nError al convertir {invalid_req.from_currency} -> {invalid_req.to_currency}:")
        print(f"  Código del error: {e.code()}")
        print(f"  Detalles: {e.details()}")


    # 3) Escuchar StreamRates por 5 elementos (server stream)
    print("\nStream de tasas (ejemplo, 5 items):")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        for i, item in enumerate(stream):
            print(f" {i+1}) {item.from_currency} -> {item.to_currency} : rate={item.rate}")
            if i >= 4:
                break
    except grpc.RpcError as e:
        print("StreamRates error:", e)


    # 4) Obtener solo la tasa con GetRate (Nuevo metodo creado)
    print("\nGetRate (solo la tasa de cambio MXN -> JPY):")
    try:
        rate_reply = stub.GetRate(currency_pb2.RateRequest(
        from_currency="MXN",
        to_currency="JPY"
    ))
        print(f" Tasa MXN -> JPY: {rate_reply.rate}")
    except grpc.RpcError as e:
        print("Error GetRate:", e)


if __name__ == "__main__":
    run()
