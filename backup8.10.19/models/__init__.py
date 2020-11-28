from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin
import sqlalchemy as sa

make_versioned(plugins=[FlaskPlugin()])

from .User import *
from .EventTag import *
from .EventArtist import *
from .EventImage import *
from .Event import *


sa.orm.configure_mappers()
