from dataclasses import dataclass
from typing import Optional


@dataclass
class User:

    id: Optional[int] = None

    bale_user_id: Optional[int] = None

    username: Optional[str] = None

    first_name: Optional[str] = None

    last_name: Optional[str] = None

    phone_number: Optional[str] = None

    role: str = "patient"

    is_active: int = 1

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    @property
    def full_name(self) -> str:

        return (
            f"{self.first_name or ''} "
            f"{self.last_name or ''}"
        ).strip()