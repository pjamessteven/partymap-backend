from marshmallow import fields
from marshmallow.validate import OneOf
from math import ceil
# kwargs params common to paginated views
common_pagination_args = {
    "per_page": fields.Int(missing=10, description="Items per page"),
    "page": fields.Int(
        missing=1,
        description=(
            "Page number (1 indexed). If the special "
            "page number 0 (zero) is given, then all "
            "items will be returned."
        ),
    ),
    "desc": fields.Bool(missing=False, description="Reverse sort results"),
}


def paginated_view_args(sort_options):
    return dict(
        sort=fields.Str(
            validate=OneOf(sort_options), description="Property to sort on"
        ),
        **common_pagination_args
    )


def paginated_results(
    model, query=None, page=1, per_page=10, sort=None, desc=False, **kwargs
):
    """Returns a paginated list of `model`, optionally sorted
    :param obj model: a db.model to query for items
    :param obj query: a (optional, possibly pre-filtered) db.model.query - it
                      will be sourced from `model` if not provided
    :param int page: page offset (starting at 1) on paginated results
    :param int per_page: how many items to include in results
    :param str sort: model property to sort once
    :param bool desc: results should be sorted in reverse
    """
    if not query:
        query = model.query
    if sort:
        sort_field = getattr(model, sort)
        if sort_field and desc:
            from sqlalchemy import desc

            sort_field = desc(sort_field)
        query = query.order_by(sort_field)
    if page == 0:
        return {"items": query.all()}
    return query.paginate(page=page, per_page=per_page)

class CustomPagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total

    @property
    def pages(self):
        return int(ceil(self.total / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

def paginate_json(json_data, page=0, per_page=10, **kwargs):
    total = len(json_data)
    offset = (page - 1) * per_page
    if page > 0:
        items = json_data[offset: offset + per_page]
    else: 
        items = json_data
        per_page = total
    return CustomPagination(items, page, per_page, total)
