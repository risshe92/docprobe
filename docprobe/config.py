from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    url: str
    mode: str = "auto"
    concurrency: int = 4
    output_dir: Path = Path("./output")
    debug: str = "off"
