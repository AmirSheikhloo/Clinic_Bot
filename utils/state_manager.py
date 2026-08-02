# utils/state_manager.py

from typing import Any


class StateManager:

    def __init__(self) -> None:

        self._states: dict[int, str] = {}

        self._data: dict[
            int,
            dict[str, Any],
        ] = {}

        self._contexts: dict[
            int,
            dict[str, Any],
        ] = {}

    # =========================================================
    # State
    # =========================================================

    def set_state(
        self,
        user_id: int,
        state: str,
    ) -> None:

        self._states[user_id] = state

    def get_state(
        self,
        user_id: int,
    ) -> str | None:

        return self._states.get(
            user_id
        )

    def clear_state(
        self,
        user_id: int,
    ) -> None:

        self._states.pop(
            user_id,
            None,
        )

        self._data.pop(
            user_id,
            None,
        )

    # =========================================================
    # Temporary Data
    # =========================================================

    def set_data(
        self,
        user_id: int,
        key: str,
        value: Any,
    ) -> None:

        if user_id not in self._data:
            self._data[user_id] = {}

        self._data[user_id][key] = value

    def get_data(
        self,
        user_id: int,
        key: str,
        default: Any = None,
    ) -> Any:

        return self._data.get(
            user_id,
            {},
        ).get(
            key,
            default,
        )

    def get_all_data(
        self,
        user_id: int,
    ) -> dict[str, Any]:

        return self._data.get(
            user_id,
            {},
        ).copy()

    # =========================================================
    # Persistent Context
    # =========================================================

    def set_context(
        self,
        user_id: int,
        key: str,
        value: Any,
    ) -> None:

        if user_id not in self._contexts:
            self._contexts[user_id] = {}

        self._contexts[user_id][key] = value

    def get_context(
        self,
        user_id: int,
        key: str,
        default: Any = None,
    ) -> Any:

        return self._contexts.get(
            user_id,
            {},
        ).get(
            key,
            default,
        )

    def clear_context(
        self,
        user_id: int,
        key: str | None = None,
    ) -> None:

        if key is None:

            self._contexts.pop(
                user_id,
                None,
            )

            return

        context = self._contexts.get(
            user_id
        )

        if context is None:
            return

        context.pop(
            key,
            None,
        )

        if not context:

            self._contexts.pop(
                user_id,
                None,
            )

    def clear_all(
        self,
        user_id: int,
    ) -> None:

        self._states.pop(
            user_id,
            None,
        )

        self._data.pop(
            user_id,
            None,
        )

        self._contexts.pop(
            user_id,
            None,
        )


state_manager = StateManager()