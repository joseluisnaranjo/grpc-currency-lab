import grpc
import time
from proto import currency_pb2
from proto import currency_pb2_grpc

def run():
    print("Conectando al servidor gRPC...")
    channel = grpc.insecure_channel('localhost:50051')
    stub = currency_pb2_grpc.CurrencyConverterStub(channel)

    # ---------------------------------------------------------
    # 1. Obtener monedas soportadas
    # ---------------------------------------------------------
    print("\n--- 1. Monedas Soportadas ---")
    try:
        # Usamos Empty() porque el proto lo define así
        for currency in stub.GetSupportedCurrencies(currency_pb2.Empty()):
            print(f" {currency.name} ({currency.code})")
    except grpc.RpcError as e:
        print(f"Error: {e}")

    # ---------------------------------------------------------
    # 2. Conversión (Usando tasas reales si la API funcionó)
    # ---------------------------------------------------------
    print("\n--- 2. Prueba de Conversión (Datos Reales) ---")
    # Probamos una conversión típica (USD -> EUR)
    req = currency_pb2.ConvertRequest(from_currency="USD", to_currency="EUR", amount=50.0)
    try:
        reply = stub.Convert(req)
        print(f" {req.amount} {req.from_currency} = {reply.converted_amount:.4f} {req.to_currency}")
        print(f"    (Tasa de cambio actual: {reply.rate})")
    except grpc.RpcError as e:
        print(f" Error en conversión: {e.details()}")

    # ---------------------------------------------------------
    # 3. Stream de Tasas (Escuchar 5 actualizaciones)
    # ---------------------------------------------------------
    print("\n--- 3. Tasas en Vivo (Stream) ---")
    print("   Escuchando 5 actualizaciones...")
    try:
        stream = stub.StreamRates(currency_pb2.Empty())
        count = 0
        for item in stream:
            print(f" Tasa: 1 {item.from_currency} = {item.rate:.4f} {item.to_currency}")
            count += 1
            if count >= 5:
                print(" Finalizando escucha.")
                break
    except grpc.RpcError as e:
        print(f"Error en stream: {e}")

if __name__ == "__main__":
    run()