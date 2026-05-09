from app.config.settings import get_settings
import os

# Mock environment
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000, http://127.0.0.1:3000"

settings = get_settings()
print(f"Allowed Origins: {settings.cors_origins}")
