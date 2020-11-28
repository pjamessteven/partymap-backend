from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin
import sqlalchemy as sa


from .EventContribution import *
from .EventTag import *
from .EventArtist import *
from .EventImage import *
from .User import *
make_versioned(plugins=[FlaskPlugin()], user_cls=User)
from .Event import *


sa.orm.configure_mappers()
