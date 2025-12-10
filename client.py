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

    # 2) Ejemplo de Convert (unary) — USD -> EUR
    req = currency_pb2.ConvertRequest(from_currency="USD", to_currency="EUR", amount=100.0)
    try:
        reply = stub.Convert(req)
        print(f"\nConvert {req.amount} {req.from_currency} -> {reply.converted_amount:.4f} {req.to_currency} (rate={reply.rate})")
    except grpc.RpcError as e:
        print("Convert error (USD->EUR):", e)

    # 3) Conversión JPY -> USD (ejemplo solicitado)
    req_jpy_usd = currency_pb2.ConvertRequest(from_currency="JPY", to_currency="USD", amount=1000.0)
    try:
        reply_jpy_usd = stub.Convert(req_jpy_usd)
        print(f"Convert {req_jpy_usd.amount} {req_jpy_usd.from_currency} -> {reply_jpy_usd.converted_amount:.4f} {req_jpy_usd.to_currency} (rate={reply_jpy_usd.rate})")
    except grpc.RpcError as e:
        print("Convert error (JPY->USD):", e)

    # 4) Conversión USD -> JPY (ejemplo inverso)
    req_usd_jpy = currency_pb2.ConvertRequest(from_currency="USD", to_currency="JPY", amount=50.0)
    try:
        reply_usd_jpy = stub.Convert(req_usd_jpy)
        print(f"Convert {req_usd_jpy.amount} {req_usd_jpy.from_currency} -> {reply_usd_jpy.converted_amount:.4f} {req_usd_jpy.to_currency} (rate={reply_usd_jpy.rate})")
    except grpc.RpcError as e:
        print("Convert error (USD->JPY):", e)

    # -----------------------
    # NUEVO: Llamada GetRate (solo devuelve la tasa)
    # -----------------------
    print("\nObteniendo solo la tasa (GetRate) USD -> JPY:")
    try:
        rate_req = currency_pb2.RateRequest(from_currency="USD", to_currency="JPY")
        rate_reply = stub.GetRate(rate_req)
        print(f"Rate {rate_req.from_currency}->{rate_req.to_currency} = {rate_reply.rate}")
    except grpc.RpcError as e:
        print("GetRate error:", e.code(), e.details())

    # 5) Escuchar StreamRates por 5 elementos (server stream)
    print("\nStream de tasas (ejemplo, 5 items):")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        for i, item in enumerate(stream):
            print(f" {i+1}) {item.from_currency} -> {item.to_currency} : rate={item.rate}")
            if i >= 4:
                break
    except grpc.RpcError as e:
        print("StreamRates error:", e)

    # 6) Probar manejo de errores con moneda inexistente
    '''print("\nPrueba de error con moneda inválida:")
    #req = currency_pb2.ConvertRequest(from_currency="ABC", to_currency="USD", amount=10)
    try:
        r = stub.Convert(req)
        print("Unexpected reply:", r)
    except grpc.RpcError as e:
        print("Error code:", e.code(), "details:", e.details())'''


if __name__ == "__main__":
    run()
