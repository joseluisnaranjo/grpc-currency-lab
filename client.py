import grpc
import currency_pb2
import currency_pb2_grpc
import time

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
    req = currency_pb2.ConvertRequest(from_currency="USD", to_currency="JPY", amount=100.0)
    try:
        reply = stub.Convert(req)
        print(f"Convert {req.amount} {req.from_currency} -> {reply.converted_amount:.4f} {req.to_currency} (rate={reply.rate})")
    except grpc.RpcError as e:
        print("Convert error:", e)

    # 3) Obtener tasa específica (unary)
    rate_req = currency_pb2.RateRequest(from_currency="GBP", to_currency="USD")
    try:
        rate_reply = stub.GetRate(rate_req)
        print(f"\nTasa {rate_req.from_currency} -> {rate_req.to_currency} : rate={rate_reply.rate}")
    except grpc.RpcError as e:
        print("GetRate error:", e)

    # 4) Escuchar StreamRates por 5 elementos (server stream)
    print("\nStream de tasas (ejemplo, 5 items):")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        for i, item in enumerate(stream):
            print(f" {i+1}) {item.from_currency} -> {item.to_currency} : rate={item.rate}")
            #if i >= 4:
            #    break
    except grpc.RpcError as e:
        print("StreamRates error:", e)
    
    

if __name__ == "__main__":
    run()
