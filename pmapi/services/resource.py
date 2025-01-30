from flask import Blueprint
from flask_apispec import doc
from flask_apispec import MethodResource
import pmapi.services.ip_location as services


services_blueprint = Blueprint("service", __name__)


@doc(tags=["services"])
class IpLookupResource(MethodResource):
    @doc(
        summary="Get location from requesting users IP.",
    )
    def get(self):
        return services.get_location_from_ip()


services_blueprint.add_url_rule(
    "/ip_lookup", view_func=IpLookupResource.as_view("IpLookupResource")
)

