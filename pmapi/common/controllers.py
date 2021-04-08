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
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    if page == 0:
        return {"items": query.all()}
    return query.paginate(page=page, per_page=per_page)
