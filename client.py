import grpc
import currency_pb2
import currency_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = currency_pb2_grpc.CurrencyConverterStub(channel)

    print("=" * 60)
    print("Cliente gRPC - Conversor de Monedas")
    print("=" * 60)

    # Mostrar monedas soportadas
    print("\nMonedas soportadas:")
    supported = []
    try:
        for currency in stub.GetSupportedCurrencies(currency_pb2.Empty()):
            print(f"   - {currency.code}: {currency.name}")
            supported.append(currency.code)
    except grpc.RpcError as e:
        print("Error GetSupportedCurrencies:", e)
        return

    # Solicitar datos al usuario
    from_currency = input("\nMoneda origen: ").strip().upper()
    to_currency = input("Moneda destino: ").strip().upper()
    try:
        amount = float(input("Cantidad a convertir: "))
    except ValueError:
        print("Cantidad inválida.")
        return

    # Validar monedas
    if from_currency not in supported or to_currency not in supported:
        print("Moneda no soportada. Intenta con una de las mostradas.")
        return

    # Método Convert
    print("\nConversión:")
    req = currency_pb2.ConvertRequest(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount
    )
    try:
        reply = stub.Convert(req)
        print(f"   {amount} {from_currency} = {reply.converted_amount:.2f} {to_currency} (tasa: {reply.rate})")
    except grpc.RpcError as e:
        print(f"Error en conversión: {e.details()}")

    # Método GetRate
    print("\nTasa de cambio actual:")
    rate_req = currency_pb2.RateRequest(
        from_currency=from_currency,
        to_currency=to_currency
    )
    try:
        rate_reply = stub.GetRate(rate_req)
        print(f"   Tasa {from_currency} -> {to_currency}: {rate_reply.rate}")
    except grpc.RpcError as e:
        print(f"Error al obtener tasa: {e.details()}")

    # Método StreamRates (solo primer resultado)
    print("\nPrimer tasa en stream:")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        for item in stream:
            print(f"   {item.from_currency} -> {item.to_currency}: tasa={item.rate}")
            break
    except grpc.RpcError as e:
        print("Error en StreamRates:", e)

    print("\n" + "=" * 60)
    print("Fin de la consulta")
    print("=" * 60)

if __name__ == "__main__":
    run()
