# services/api/app/services/faiss_builder.py
"""
Helper script to build FAISS index for resources.
Usage:
    python -m services.api.app.services.faiss_builder
Or run the functions programmatically.
"""

import logging
import os
import sys
from pathlib import Path

# Make sure to be able to import repository modules (adjust if you run from repo root)
ROOT = Path(__file__).resolve().parents[5]  # adjust to reach repo root
sys.path.append(str(ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from services.api.app.db.repositories import (
    ResourcesRepo,
)  # import repo to fetch resources
from services.api.app.services.embeddings import build_faiss_index


def build_index_from_db():
    logger.info("Fetching resources from DB...")
    resources = ResourcesRepo.list_resources()
    if not resources:
        logger.warning("No resources found in DB to index.")
        return
    logger.info("Building FAISS index for %d resources...", len(resources))
    index, ids = build_faiss_index(resources, rebuild=True)
    logger.info("FAISS index built and saved. Indexed IDs: %d", len(ids))


if __name__ == "__main__":
    build_index_from_db()
