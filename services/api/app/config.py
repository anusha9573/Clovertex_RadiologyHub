# services/api/app/config.py
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[4]  # repo root -> work-allocation
ENV_PATH = ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

DB_DIALECT = os.getenv("DB_DIALECT", "sqlite").lower()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpass")
DB_NAME = os.getenv("DB_NAME", "work_allocation")
DB_PORT = int(os.getenv("DB_PORT", 3306))
SQLITE_PATH = os.getenv(
    "SQLITE_PATH", str(ROOT / "infra" / "mysql_init" / "work_allocation.db")
)

HF_LLM_MODEL = os.getenv("HF_LLM_MODEL", "distilgpt2")
EMB_MODEL = os.getenv("EMB_MODEL", "all-MiniLM-L6-v2")
EMB_CACHE_DIR = os.getenv(
    "EMB_CACHE_DIR", str(ROOT / "infra" / "mysql_init" / "embeddings_cache")
)
