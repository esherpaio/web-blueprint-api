from web.api import API, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Region, UserRoleLevel
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class RegionAPI(API):
    model = Region
    post_columns = {
        Region.name,
    }
    get_columns = {
        Region.name,
        Region.id,
    }


#
# Endpoints
#


@api_bp.post("/regions")
@authorize(UserRoleLevel.ADMIN)
def post_regions() -> Response:
    api = RegionAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/regions")
def get_regions() -> Response:
    api = RegionAPI()
    with conn.begin() as s:
        models: list[Region] = api.list_(s)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/regions/<int:region_id>")
def get_regions_id(region_id: int) -> Response:
    api = RegionAPI()
    with conn.begin() as s:
        model: Region = api.get(s, region_id)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.delete("/regions/<int:region_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_regions_id(region_id: int) -> Response:
    api = RegionAPI()
    with conn.begin() as s:
        model: Region = api.get(s, region_id)
        api.delete(s, model)
    return json_response()


#
# Functions
#
