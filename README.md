# Laboratorio gRPC: Conversor de Monedas

Este repositorio contiene la implementación de una práctica de laboratorio sobre **gRPC** y **Protocol Buffers** utilizando Python. El proyecto simula un servicio de conversión de divisas que permite comunicación síncrona (Unary) y transmisión de datos en flujo (Server Streaming).

**Estudiante:** Josue Alexander Cuenca Mendoza  
**Asignatura:** Arquitectura y Servicios Distribuidos  
**Rama de desarrollo:** `josue-cuenca`

---

## Descripción del Proyecto

El sistema consta de un servidor y un cliente que se comunican mediante gRPC para realizar las siguientes operaciones:

1.  **Conversión de Moneda (Unary):** El cliente envía una cantidad y dos códigos de moneda (origen y destino), y el servidor responde con el monto convertido.
2.  **Listado de Monedas (Server Streaming):** El servidor envía una lista de monedas soportadas una por una.
3.  **Monitor de Tasas (Server Streaming):** Simulación de un flujo continuo de actualizaciones de tasas de cambio en tiempo real.

---

## Requisitos Previos

* **Lenguaje:** Python 3.8 o superior.
* **Entorno Virtual:** Recomendado (`venv`).

## Arquitectura de las carpetas
```
GRPC-CURRENCY-LAB/
├── proto/
│   └── currency.proto       # Definición del servicio y mensajes
├── img/                     # Carpeta de capturas para el README
│   ├── server_running.png
│   └── client_running.png
├── server.py                # Lógica del servidor
├── client.py                # Script del cliente
├── currency_pb2.py          # Código generado (Mensajes)
├── currency_pb2_grpc.py     # Código generado (Stubs)
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación
```

### Dependencias
Las librerías necesarias son `grpcio` y `grpcio-tools`.

```bash
pip install -r requirements.txt
# O manualmente:
pip install grpcio grpcio-tools
```

# Iniciar el Servidor
En una terminal, ejecuta:
```bash
python server.py
```

# Iniciar el Cliente
Abre una nueva terminal (manteniendo el servidor abierto) y ejecuta:
```bash
python client.py
```

# Generar los Stubs (Código gRPC)
Si realizas cambios en el archivo .proto o si es la primera vez que ejecutas el proyecto, debes generar el código de Python. Ejecuta este comando desde la raíz del proyecto:
```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. currency.proto
```

# Evidencias de Ejecución
Las capturas de pantalla que demuestran el funcionamiento correcto del laboratorio se muestran dentro de la carpeta /capturas.

