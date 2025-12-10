# server.py
import os
import time
import threading
from concurrent import futures

import grpc
import requests
from cachetools import TTLCache, cached

import currency_pb2
import currency_pb2_grpc

# ---------------------
# Config
# ---------------------
API_BASE = os.getenv("EXCHANGE_API_BASE", "https://api.frankfurter.app")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hora por defecto
CACHE_MAX_ITEMS = 1000

# Caché: key = "FROM:TO" -> rate
_rate_cache = TTLCache(maxsize=CACHE_MAX_ITEMS, ttl=CACHE_TTL_SECONDS)
_cache_lock = threading.Lock()

# Fallback local (si la API falla)
FALLBACK_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.78, "JPY": 150.0, "USD": 1.0},
    "EUR": {"USD": 1.087, "GBP": 0.85, "JPY": 163.0, "EUR": 1.0},
    "GBP": {"USD": 1.28, "EUR": 1.17, "JPY": 192.0, "GBP": 1.0},
    "JPY": {"USD": 1.0/150.0, "EUR": 1.0/163.0, "GBP": 1.0/192.0, "JPY": 1.0},
}

# Opcional: lista inicial de soportadas; se puede poblar dinámicamente con /symbols
STATIC_SUPPORTED = [
    ("USD", "United States Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
]

# ---------------------
# Helpers
# ---------------------
def _cache_key(frm: str, to: str) -> str:
    return f"{frm.upper()}:{to.upper()}"

def fetch_rate_from_api(frm: str, to: str) -> float | None:
    """
    Consulta Frankfurter (sin api key).
    Endpoint usado: GET https://api.frankfurter.app/latest?from=USD&to=EUR
    Retorna la tasa (float) o None si falla.
    """
    url = f"{API_BASE}/latest"
    params = {"from": frm, "to": to}
    try:
        print(f"[API] requesting {url} params={params}")
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        print(f"[API] response for {frm}->{to}: {data}")
        # Frankfurter devuelve {"amount":1,"base":"USD","date":"YYYY-MM-DD","rates":{"EUR":0.92}}
        rates = data.get("rates")
        if isinstance(rates, dict) and to.upper() in {k.upper(): v for k, v in rates.items()}:
            # Frankfurter returns keys as codes in correct case; use direct access
            # But to be safe, normalize key lookup:
            for code, val in rates.items():
                if code.upper() == to.upper():
                    return float(val)
        return None
    except Exception as e:
        print(f"[fetch_rate_from_api] error fetching {frm}->{to}: {e}")
        return None

def get_rate(frm: str, to: str) -> float:
    frm = frm.upper()
    to = to.upper()
    key = _cache_key(frm, to)

    # 1) chequeo caché
    with _cache_lock:
        cached_rate = _rate_cache.get(key)
    if cached_rate is not None:
        print(f"[RATE] cache HIT {frm}->{to} = {cached_rate}")
        return cached_rate

    # 2) intentar desde API
    rate = fetch_rate_from_api(frm, to)
    if rate is not None:
        with _cache_lock:
            _rate_cache[key] = rate
        print(f"[RATE] from API {frm}->{to} = {rate}")
        return rate

    # 3) intentar usar fallback directo
    if frm in FALLBACK_RATES and to in FALLBACK_RATES[frm]:
        fallback_rate = FALLBACK_RATES[frm][to]
        print(f"[RATE] fallback DIRECT {frm}->{to} = {fallback_rate}")
        return fallback_rate

    # 4) intentar inversión de fallback (si existe el otro sentido)
    if to in FALLBACK_RATES and frm in FALLBACK_RATES[to]:
        inv = FALLBACK_RATES[to][frm]
        if inv != 0:
            rate_calc = 1.0 / inv
            print(f"[RATE] fallback INVERT {frm}->{to} = {rate_calc}")
            return rate_calc

    # 5) intentar pivote vía USD (API o fallback parcial)
    pivot = "USD"
    try:
        try:
            f_to_p = get_rate(frm, pivot) if frm != pivot else 1.0
        except ValueError:
            f_to_p = None
        try:
            p_to_t = get_rate(pivot, to) if to != pivot else 1.0
        except ValueError:
            p_to_t = None

        if f_to_p is not None and p_to_t is not None:
            rate = f_to_p * p_to_t
            with _cache_lock:
                _rate_cache[key] = rate
            print(f"[RATE] pivot USD {frm}->{to} via USD = {rate}")
            return rate
    except RecursionError:
        pass

    # 6) si todo falla, error
    print(f"[RATE] NO RATE for {frm}->{to}")
    raise ValueError(f"Tasa no disponible para {frm} -> {to}")

def fetch_supported_symbols() -> list[tuple[str, str]]:
    """
    Llama a /currencies y devuelve lista de (code, name).
    Si falla, devuelve STATIC_SUPPORTED.
    Frankfurter: GET https://api.frankfurter.app/currencies
    devuelve: {"USD":"United States Dollar","EUR":"Euro", ...}
    """
    url = f"{API_BASE}/currencies"
    try:
        print(f"[API] requesting supported currencies {url}")
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            out = [(code, name) for code, name in data.items()]
            # opcional: ordenar por código
            out.sort(key=lambda x: x[0])
            return out
    except Exception as e:
        print(f"[fetch_supported_symbols] error: {e}")
    return STATIC_SUPPORTED

# ---------------------
# gRPC Servicer
# ---------------------
class CurrencyConverterServicer(currency_pb2_grpc.CurrencyConverterServicer):
    def Convert(self, request, context):
        frm = request.from_currency.upper()
        to = request.to_currency.upper()
        amt = request.amount
        try:
            rate = get_rate(frm, to)
        except ValueError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return currency_pb2.ConvertReply()
        converted = amt * rate
        return currency_pb2.ConvertReply(
            converted_amount=converted,
            rate=rate,
            from_currency=frm,
            to_currency=to
        )

    def GetSupportedCurrencies(self, request, context):
        """
        Implementado como server-streaming: emitimos lista (uno por mensaje).
        Si prefieres unary que devuelve SupportedReply, avísame y adapto.
        """
        symbols = fetch_supported_symbols()
        for code, name in symbols:
            if not context.is_active():
                return
            yield currency_pb2.Currency(code=code, name=name)
            
    

    def StreamRates(self, request, context):
        # similar a antes, pero consultando el cache/API según necesidad
        while context.is_active():
            # iterar combinaciones simples para enviar updates
            codes = list({k for k in list(FALLBACK_RATES.keys())})
            # mejor: obtener símbolos de la API (o STATIC_SUPPORTED)
            # aqui usamos STATIC_SUPPORTED para ejemplo
            codes = [c for c, _ in STATIC_SUPPORTED]
            for frm in codes:
                for to in codes:
                    if frm == to:
                        continue
                    try:
                        rate = get_rate(frm, to)
                        if not context.is_active():
                            return
                        yield currency_pb2.ConvertReply(
                            converted_amount=rate,
                            rate=rate,
                            from_currency=frm,
                            to_currency=to
                        )
                    except Exception:
                        # si falla para un par, saltarlo
                        continue
                    time.sleep(0.2)
            # pausa más larga entre rondas
            time.sleep(1.0)
            
    def GetRate(self, request, context):
        frm = request.from_currency.upper()
        to = request.to_currency.upper()
        try:
            rate = get_rate(frm, to)  # usa la función helper que ya tienes
        except ValueError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return currency_pb2.RateReply()  # reply vacío con código de error
        return currency_pb2.RateReply(rate=rate)
            
            

# ---------------------
# Server boot
# ---------------------
def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    currency_pb2_grpc.add_CurrencyConverterServicer_to_server(CurrencyConverterServicer(), server)
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    server.start()
    print(f"gRPC CurrencyConverter server started on {listen_addr} - API base: {API_BASE}")
    return server

if __name__ == "__main__":
    _rate_cache.clear()
    print("[DEBUG] rate cache cleared on startup")
    s = serve()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        s.stop(0)
