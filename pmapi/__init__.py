import sqlalchemy as sa
from sqlalchemy_continuum import make_versioned
from flask_admin.contrib.sqla import ModelView

import pmapi.extensions

# this needs to happen before models are declared
make_versioned(plugins=[extensions.flask_plugin, extensions.activity_plugin])

from pmapi.user.model import User
from pmapi.event_tag.model import EventTag, Tag
from pmapi.event_image.model import EventImage
from pmapi.event.model import Event, Rrule
from pmapi.event_date.model import EventDate
# from pmapi.event_artist.model import EventArtist
# from pmapi.event_contribution.model import EventContribution
from pmapi.notification.model import Notification, UserNotification
from pmapi.event_location.model import EventLocation

# then we configure mappers
sa.orm.configure_mappers()

# flask admin
extensions.admin.add_view(ModelView(User, extensions.db.session))
extensions.admin.add_view(ModelView(Event, extensions.db.session))
extensions.admin.add_view(ModelView(EventDate, extensions.db.session))
extensions.admin.add_view(ModelView(EventLocation, extensions.db.session))
