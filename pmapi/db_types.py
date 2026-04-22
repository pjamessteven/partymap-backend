import sqlalchemy as sa


class Vector(sa.types.UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions=None):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        if self.dimensions:
            return "vector({})".format(self.dimensions)
        return "vector"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return "[{}]".format(",".join(str(float(item)) for item in value))

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None or isinstance(value, list):
                return value
            if isinstance(value, str):
                stripped = value.strip()[1:-1]
                if not stripped:
                    return []
                return [float(item) for item in stripped.split(",")]
            return value

        return process
