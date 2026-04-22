import argparse
import os
import sys

from flask.helpers import get_debug_flag

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from pmapi.application import create_app
from pmapi.config import DevConfig, ProdConfig
from pmapi.event.model import Event
from pmapi.extensions import db
from pmapi.services.embeddings import refresh_event_embedding


CONFIG = DevConfig if get_debug_flag() else ProdConfig


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill event search embeddings.")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute embeddings for events that already have one.",
    )
    return parser.parse_args()


def run_backfill(batch_size=100, limit=None, force=False, logger=None):
    processed = 0
    failed = 0
    last_id = 0

    while True:
        query = (
            db.session.query(Event)
            .filter(Event.id > last_id)
            .order_by(Event.id.asc())
            .limit(batch_size)
        )

        if not force:
            query = query.filter(Event.search_embedding.is_(None))

        batch = query.all()
        if not batch:
            break

        for event in batch:
            if limit and (processed + failed) >= limit:
                batch = []
                break

            try:
                refresh_event_embedding(event, raise_on_error=True)
                processed += 1
            except Exception as exc:
                failed += 1
                if logger is not None:
                    logger.exception(
                        "Failed to backfill embedding for event %s: %s", event.id, exc
                    )
                else:
                    print(
                        "Failed to backfill embedding for event {}: {}".format(
                            event.id, exc
                        )
                    )
            finally:
                last_id = event.id

        db.session.commit()
        print("Processed {}, failed {}...".format(processed, failed))

        if limit and (processed + failed) >= limit:
            break

    db.session.commit()
    print("Finished. Processed {}, failed {}.".format(processed, failed))


def main():
    args = parse_args()
    app = create_app(CONFIG)

    with app.app_context():
        run_backfill(
            batch_size=args.batch_size,
            limit=args.limit,
            force=args.force,
            logger=app.logger,
        )


if __name__ == "__main__":
    main()
