import requests
from flask import current_app

from pmapi.config import BaseConfig


def embeddings_enabled():
    return bool(BaseConfig.ENABLE_EVENT_EMBEDDINGS and BaseConfig.EMBEDDING_API_KEY)


def _event_tag_text(event):
    if not event or not getattr(event, "event_tags", None):
        return None

    tags = sorted(
        {
            event_tag.tag_id.strip().lower()
            for event_tag in event.event_tags
            if getattr(event_tag, "tag_id", None)
        }
    )
    if not tags:
        return None

    return ", ".join(tags)


def _next_event_location_text(event):
    if not event:
        return None

    next_event_date = getattr(event, "next_event_date", None)
    if not next_event_date or not getattr(next_event_date, "location", None):
        return None

    location = next_event_date.location
    venue = getattr(location, "name", None)
    locality = getattr(getattr(location, "locality", None), "long_name", None)
    region = getattr(getattr(location, "region", None), "long_name", None)
    country = getattr(getattr(location, "country", None), "long_name", None)
    country_short = getattr(getattr(location, "country", None), "short_name", None)

    parts = []
    if venue:
        parts.append(venue.strip())
    if locality:
        parts.append(locality.strip())
    if region:
        parts.append(region.strip())

    if country:
        parts.append(country.strip() + ' ('+country_short.strip()+')')


    if not parts:
        return None

    return ", ".join(parts)


def build_event_embedding_text(name, description, tags_text=None, location_text=None):
    parts = []
    if name:
        parts.append(name.strip())
    if description:
        parts.append(description.strip())
    if tags_text:
        parts.append("Tags: {}".format(tags_text.strip()))
    if location_text:
        parts.append("Location: {}".format(location_text.strip()))
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
    text = build_event_embedding_text(
        event.name,
        event.description,
        tags_text=_event_tag_text(event),
        location_text=_next_event_location_text(event),
    )
    print(
        "Generated event embedding text for event {}:\n{}\n".format(
            getattr(event, "id", None), text
        )
    )

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


def mark_event_embedding_refresh(event):
    if event is not None:
        event.refresh_embedding_after_commit = True
