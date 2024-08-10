import sqlalchemy as sa
from sqlalchemy_continuum import make_versioned
from flask_admin.contrib.sqla import ModelView
import pmapi.extensions as extensions

# this needs to happen before models are declared
make_versioned(plugins=[extensions.flask_plugin, extensions.activity_plugin])

from pmapi.user.model import User
from pmapi.event_tag.model import EventTag, Tag
from pmapi.event_artist.model import EventDateArtist, Artist

from pmapi.media_item.model import MediaItem
from pmapi.event.model import Event, Rrule
from pmapi.event_date.model import EventDate
from pmapi.report.model import Report
from pmapi.feedback.model import Feedback

# from pmapi.event_artist.model import EventArtist
from pmapi.event_review.model import EventReview, event_review_downvotes, event_review_downvotes
from pmapi.notification.model import Notification, UserNotification
from pmapi.event_location.model import EventLocation
from pmapi.suggestions.model import SuggestedEdit

# then we configure mappers
sa.orm.configure_mappers()

# flask admin
extensions.admin.add_view(ModelView(User, extensions.db.session))
extensions.admin.add_view(ModelView(Event, extensions.db.session))
extensions.admin.add_view(ModelView(EventDate, extensions.db.session))
extensions.admin.add_view(ModelView(EventLocation, extensions.db.session))
