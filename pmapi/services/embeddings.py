import requests
from flask import current_app

from pmapi.config import BaseConfig


def embeddings_enabled():
    return bool(BaseConfig.ENABLE_EVENT_EMBEDDINGS and BaseConfig.EMBEDDING_API_KEY)


def build_event_embedding_text(name, description):
    parts = []
    if name:
        parts.append(name.strip())
    if description:
        parts.append(description.strip())
    return "\n\n".join([part for part in parts if part])


def _embedding_headers():
    return {
        "Authorization": "Bearer {}".format(BaseConfig.EMBEDDING_API_KEY),
        "Content-Type": "application/json",
    }


def generate_embedding(text):
    if not embeddings_enabled() or not text or not text.strip():
        return None

    payload = {
        "input": text,
        "model": BaseConfig.EMBEDDING_MODEL,
        "encoding_format": "float",
    }

    response = requests.post(
        BaseConfig.EMBEDDING_API_URL,
        headers=_embedding_headers(),
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()["data"][0]["embedding"]

    if (
        BaseConfig.EVENT_EMBEDDING_DIMENSIONS
        and len(data) != BaseConfig.EVENT_EMBEDDING_DIMENSIONS
    ):
        raise ValueError(
            "Embedding dimension mismatch. Expected {}, got {}.".format(
                BaseConfig.EVENT_EMBEDDING_DIMENSIONS, len(data)
            )
        )

    return data


def refresh_event_embedding(event, raise_on_error=False):
    text = build_event_embedding_text(event.name, event.description)

    try:
        event.search_embedding = generate_embedding(text)
    except Exception:
        event.search_embedding = None
        if raise_on_error:
            raise
        current_app.logger.exception(
            "Failed to refresh embedding for event %s", getattr(event, "id", None)
        )

    return event.search_embedding
