from dataclasses import dataclass
from typing import Optional


@dataclass
class Setting:

    key: str

    value: Optional[str] = None

    updated_at: Optional[str] = None