"""Reproducible Phase 9 training/prediction demonstration.

Usage from backend/: py ../scripts/train_predictive_model.py
"""
import json
from pathlib import Path
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.config import settings
from app.ml.service import prediction_payload


with Session(create_engine(settings.database_url)) as session:
    print(json.dumps(prediction_payload(session), default=str, indent=2))
