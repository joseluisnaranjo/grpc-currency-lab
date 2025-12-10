# Laboratorio: Servicio de Conversión de Monedas con gRPC

Este laboratorio guía a los estudiantes en la creación, implementación y uso de un servicio gRPC en Python.

## Resumen del Laboratorio

**Objetivo:** Construir un servicio gRPC que convierta una cantidad entre monedas (p. ej. USD → EUR).

**RPCs:**
1.  **Convert** (Unary): Convierte una cantidad con una tasa dada por el servidor.
2.  **GetSupportedCurrencies** (Server-Streaming): El servidor envía la lista de monedas soportadas.
3.  **StreamRates** (Server-Streaming - Opcional): Envía actualizaciones periódicas de tasas simuladas.

## 1. Estructura del Proyecto

```
grpc-currency-lab/
├─ proto/
│  └─ currency.proto
├─ server.py
├─ client.py
├─ requirements.txt
└─ README.md
```

## 2. Definición del Servicio (.proto)

El archivo `proto/currency.proto` define los mensajes y servicios. Ver el archivo incluido para más detalles.

## 3. Preparación del Entorno

Se recomienda usar un entorno virtual (Conda o venv).

### Instalación de dependencias

```bash
pip install -r requirements.txt
```
O manualmente:
```bash
pip install grpcio grpcio-tools protobuf requests
```

## 4. Generación de Stubs (Código Python desde Proto)

Para que Python entienda el archivo `.proto`, debemos compilarlo. Desde la raíz del proyecto (`grpc-currency-lab/`), ejecuta:

```bash
python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. proto/currency.proto
```

Esto generará `currency_pb2.py` y `currency_pb2_grpc.py`.

## 5. Implementación del Servidor (`server.py`)

El servidor implementa la clase `CurrencyConverterServicer`.
- Usa un diccionario `SIMULATED_RATES` para las tasas de cambio.
- Escucha en el puerto `50051`.

Para iniciarlo:
```bash
python server.py
```

## 6. Implementación del Cliente (`client.py`)

El cliente se conecta al servidor y realiza llamadas a los métodos definidos.

Para ejecutarlo (en otra terminal):
```bash
python client.py
```

## 7. Actividades Sugeridas

1.  **Modificar Tasas:** Agrega soporte para una nueva moneda (ej. JPY) en `server.py`.
2.  **Manejo de Errores:** Observa qué pasa si pides una conversión de una moneda que no existe.
3.  **API Real (Extensión):** Intenta conectar el servidor a una API pública de tasas de cambio.
4.  **Desafío de Modificción de Protocolo (Importante):**
    *   **Objetivo:** Agregar una nueva función `GetRate` que solo devuelva la tasa de cambio (sin convertir una cantidad).
    *   **Pasos:**
        1.  Modificar `proto/currency.proto`:
            *   Crear mensajes `message RateRequest { string from_currency=1; string to_currency=2; }` y `message RateReply { double rate=1; }`.
            *   Agregar el método `rpc GetRate(RateRequest) returns (RateReply);` al servicio.
        2.  **Recompilar los stubs** (paso 4 de esta guía) para que se actualice `currency_pb2_grpc.py`.
        3.  Implementar el método `GetRate` en `server.py`.
        4.  Llamarlo desde `client.py`. (¡Si no recompilas, te dará error!)

## 8. Preguntas de Control

- ¿Qué diferencia hay entre una RPC unary y server-streaming?

        Una RPC unary es la forma más simple: el cliente envía una sola petición y espera una única respuesta del servidor, piensa en una llamada HTTP típica, es ideal para operaciones puntuales como convierte 10 USD a EUR porque la interacción termina cuando llega la respuesta. En cambio una RPC server-streaming mantiene abierta la conexión y el servidor envía una secuencia de mensajes uno tras otro hasta que decide terminar o el cliente la cancela, es usada cuando el servidor debe empujar actualizaciones periódicas por ejemplo, un stream de tasas que va publicando nuevos valores cada cierto tiempo.


- ¿Cómo manejarías el caso de una tasa no encontrada en el servidor?

        Si el servidor no encuentra una tasa, se maneja de forma predecible y explícita: primero validas rápido rechazar monedas desconocidas sin tocar la API, luego intentas obtener la tasa de la caché y si no está llama a la API externa con un timeout corto. Si la API falla, puedes devolver una tasa de fallback local o intentar un pivote ej. calcular A→C vía A→USD→C y, solo si todo eso falla, responder con un error gRPC claro incluyendo un mensaje descriptivo en details. 

## 9. Sugerencias de APIs para Tasas en Tiempo Real

Para la actividad de extensión (conectar a una API Real), los estudiantes pueden utilizar una de las siguientes opciones gratuitas:

1.  **Frankfurter API** (Muy recomendada para estudiantes)
    *   **Ventaja:** Totalmente gratuita, open-source, no requiere registro ni API Key.
    *   **Ejemplo:** `GET https://api.frankfurter.app/latest?from=USD&to=EUR`
    *   **Docs:** [frankfurter.app](https://www.frankfurter.app/docs/)

2.  **ExchangeRate-API**
    *   **Ventaja:** Respuesta JSON limpia y fácil de parsear.
    *   **Requisito:** Registro gratuito para obtener una API Key.
    *   **Sitio:** [exchangerate-api.com](https://www.exchangerate-api.com/)

3.  **Fixer.io**
    *   **Ventaja:** Estándar en la industria.
    *   **Requisito:** Registro (Plan gratuito con límite de requests).
    *   **Sitio:** [fixer.io](https://fixer.io/)

**Pista para la implementación:**
En `server.py`, pueden importar la librería `requests` (ya incluida en `requirements.txt`) para hacer un `requests.get(url)` dentro de una función auxiliar, y actualizar el diccionario `SIMULATED_RATES` con los valores reales recibidos.
