from flask import Blueprint
from flask_apispec import doc
from flask_apispec import MethodResource
import pmapi.services.controllers as services


services_blueprint = Blueprint("service", __name__)


@doc(tags=["reports"])
class IpLookupResource(MethodResource):
    @doc(
        summary="Get location from IP.",
    )
    def get(self, **kwargs):
        return services.get_location_from_ip(**kwargs)


services_blueprint.add_url_rule(
    "/ip_lookup", view_func=IpLookupResource.as_view("IpLookupResource")
)
