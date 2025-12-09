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
python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/currency.proto
```

Esto generará `currency_pb2.py` y `currency_pb2_grpc.py`.

**Nota importante:** Si modificas el archivo `.proto`, debes recompilar los stubs con el comando anterior antes de ejecutar el servidor y cliente.

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

## 7. Actividades Implementadas

### 1.  Agregar soporte para JPY (Japanese Yen)
Se agregó soporte para la moneda JPY con tasas simuladas:
- 1 USD = 149.50 JPY
- 1 EUR = 162.50 JPY
- 1 GBP = 190.50 JPY

Ver cambios en `SUPPORTED` y `SIMULATED_RATES` en `server.py`.

### 2. Manejo de Errores
El servidor maneja adecuadamente conversiones de monedas no válidas:
- Retorna error `NOT_FOUND` con mensaje descriptivo
- El cliente captura y muestra el error apropiadamente
- Ver prueba en la sección 5 del cliente

### 3.  API Real - Frankfurter
El servidor ahora se conecta a la API pública **Frankfurter** para obtener tasas en tiempo real:
- **Ventaja:** No requiere API Key, es open-source
- **Fallback:** Si la API falla, usa tasas simuladas
- **Implementación:** Función `fetch_real_rates()` en `server.py`
- **URL:** `https://api.frankfurter.app/latest?from=USD&to=EUR`

El servidor intenta primero obtener tasas reales; si falla por timeout o error de red, usa las tasas simuladas.

### 4. Desafío: Nueva función GetRate
Se implementó una nueva RPC unary llamada **GetRate** que solo devuelve la tasa de cambio sin convertir cantidad.

**Cambios realizados:**

a) Modificar `proto/currency.proto`:
   - Agregados mensajes `RateRequest` y `RateReply`
   - Agregado método `rpc GetRate(RateRequest) returns (RateReply);`

b) Recompilar stubs:
   ```bash
   python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/currency.proto
   ```

c) Implementación en `server.py`:
   - Método `GetRate()` en clase `CurrencyConverterServicer`
   - Soporta tasas reales (API Frankfurter) y tasas simuladas

d) Cliente actualizado en `client.py`:
   - Sección 3: Demuestra uso de `GetRate`
   - Prueba tasas USD->JPY, EUR->GBP, GBP->EUR

## 8. Preguntas de Control

- ¿Qué diferencia hay entre una RPC unary y server-streaming?
 RPC unary es una llamada donde el cliente envía una solicitud y esta recibe una respuesta del servidor, en cambio el server-streaming el clinete también envía una solicitud pero el servidor contesta con múltiples respuestas
- ¿Cómo manejarías el caso de una tasa no encontrada en el servidor?
El servidor deberá devolver un error gRPC con el código y un mensaje explicando que la tasa no existe para esas monedas.
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
