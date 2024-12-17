from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from ..prometheus.unifiedMetrics import create_unified_metrics_class
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def configure_monitor(app: FastAPI):
    UnifiedMetrics = create_unified_metrics_class(app)
    metrics = UnifiedMetrics(app)
    app.add_middleware(BaseHTTPMiddleware, dispatch=metrics.dispatch)
    FastAPIInstrumentor.instrument_app(app)
    return metrics
