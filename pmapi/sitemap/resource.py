from flask import Blueprint, request, make_response, render_template, current_app

from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource

from urllib.parse import urlparse
from pmapi.exceptions import InvalidUsage
from pmapi.common.controllers import paginated_view_args

sitemap_blueprint = Blueprint("sitemap", __name__)

@doc(tags=["sitemap"])
class SiteMapResource(MethodResource):
    @doc(
        summary="Sitemap for SEO",
    )
    def get(self, **kwargs):
        host_components = urlparse(request.host_url)
        host_base = host_components.scheme + "://" + host_components.netloc
        
        # Collect URLs
        urls = []
        for rule in current_app.url_map.iter_rules():
            if "GET" in rule.methods and len(rule.arguments) == 0:
                urls.append(host_base + str(rule.rule))
        
        # Add dynamic content URLs here
        # For example, if you have blog posts:
        # posts = get_all_blog_posts()
        # for post in posts:
        #     urls.append({"loc": host_base + url_for("blog_post", post_id=post.id),
        #                  "lastmod": post.modified_date.strftime("%Y-%m-%d")})
        
        sitemap_xml = render_template("sitemap.xml", urls=urls)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        
        return response

sitemap_blueprint.add_url_rule(
    "/", view_func=SiteMapResource.as_view("SiteMapResource")
)
