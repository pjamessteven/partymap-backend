from flask import Blueprint, make_response, render_template, current_app

from flask_apispec import doc
from flask_apispec import MethodResource

from pmapi.event.model import Event
from pmapi.event_artist.model import Artist
from pmapi.extensions import db
from pmapi.utils import SUPPORTED_LANGUAGES 

sitemap_blueprint = Blueprint("sitemap", __name__)

@doc(tags=["sitemap"])
class SiteMapResource(MethodResource):
    @doc(
        summary="Sitemap for SEO purposes",
    )
    def get(self, **kwargs):

        urls = []

        events = db.session.query(Event).all()
        artists = db.session.query(Artist).all()

        urls.append({"loc": '/browse'})
        urls.append({"loc": '/?view=nearby'})
        urls.append({"loc": '/?view=explore'})
        urls.append({"loc": '/privacy_policy'})
        urls.append({"loc": '/support'})
        urls.append({"loc": '/terms_and_conditions'})
        urls.append({"loc": '/login'})
        urls.append({"loc": '/register'})
        urls.append({"loc": '/forgot'})
        urls.append({"loc": '/add/public_event/'})
    
        for event in events:
            urls.append({"loc": '/event/' + str(event.id) +  '?name=' + event.name,
                        "lastmod": event.updated_at.strftime("%Y-%m-%d")})
        for artist in artists:
            urls.append({"loc": '/artist/' + str(artist.id) +  '?name=' + artist.name})
        
        base_url = current_app.config["WEBSITE_URL"]

        sitemap_xml = render_template("sitemap.xml", urls=urls, base_url=base_url, supported_languages=SUPPORTED_LANGUAGES)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        
        return response

sitemap_blueprint.add_url_rule(
    "", view_func=SiteMapResource.as_view("SiteMapResource")
)
