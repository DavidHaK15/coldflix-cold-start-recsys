import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sample"
MIN_USER_INTERACTIONS = 20
LEARNING_CURVE_POINTS = [0, 1, 2, 5, 10, 20]
DEFAULT_TOP_N = 10
MF_FACTORS = 24

# Cho phép cấu hình CORS qua biến môi trường (hữu ích khi chạy Docker / đổi cổng).
_env_origins = os.getenv("CORS_ORIGINS", "").strip()
CORS_ORIGINS = (
    [origin.strip() for origin in _env_origins.split(",") if origin.strip()]
    if _env_origins
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]
)
