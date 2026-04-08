from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    url: str
    export_as: str = "md"
    concurrency: int = 4
    output_dir: Path = None
    debug: str = "off"
