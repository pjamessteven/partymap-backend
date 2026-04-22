import argparse

from flask.helpers import get_debug_flag

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


def main():
    args = parse_args()
    app = create_app(CONFIG)

    with app.app_context():
        processed = 0
        failed = 0
        last_id = 0

        while True:
            query = (
                db.session.query(Event)
                .filter(Event.id > last_id)
                .order_by(Event.id.asc())
                .limit(args.batch_size)
            )

            if not args.force:
                query = query.filter(Event.search_embedding.is_(None))

            batch = query.all()
            if not batch:
                break

            for event in batch:
                if args.limit and (processed + failed) >= args.limit:
                    batch = []
                    break

                try:
                    refresh_event_embedding(event, raise_on_error=True)
                    processed += 1
                except Exception as exc:
                    failed += 1
                    app.logger.exception(
                        "Failed to backfill embedding for event %s: %s", event.id, exc
                    )
                finally:
                    last_id = event.id

            db.session.commit()
            print("Processed {}, failed {}...".format(processed, failed))

            if args.limit and (processed + failed) >= args.limit:
                break

        db.session.commit()
        print("Finished. Processed {}, failed {}.".format(processed, failed))


if __name__ == "__main__":
    main()
