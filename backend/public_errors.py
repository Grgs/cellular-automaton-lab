from __future__ import annotations


class PublicApiError(ValueError):
    """An expected client error whose message is safe to return over the API."""

    def __init__(self, public_message: str) -> None:
        self.public_message = public_message
        super().__init__(public_message)

    def to_payload(self) -> dict[str, str | int]:
        return {"error": self.public_message}
