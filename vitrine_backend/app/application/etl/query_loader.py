from pathlib import Path
from app.application.loaders.query_loader import BaseQueryLoader


class QueryLoader(BaseQueryLoader):
    BASE_DIR = Path(__file__).resolve().parent / "queries"