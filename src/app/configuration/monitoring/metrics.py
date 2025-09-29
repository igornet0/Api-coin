from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

# Common, reusable metrics registry objects

request_counter = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency_seconds = Histogram(
    'http_request_latency_seconds',
    'Latency of HTTP requests in seconds',
    ['endpoint', 'method']
)


def export_prometheus() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


