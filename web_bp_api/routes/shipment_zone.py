from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import ShipmentMethod, ShipmentZone, UserRoleLevel
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/shipment-zones")
@authorize(UserRoleLevel.ADMIN)
def post_shipment_zones() -> Response:
    country_id, _ = json_get("country_id", int)
    order, _ = json_get("order", int, nullable=False)
    region_id, _ = json_get("region_id", int)

    with conn.begin() as s:
        # Get or restore shipment zone
        shipment_zone = (
            s.query(ShipmentZone)
            .filter(
                ShipmentZone.country_id == country_id,
                ShipmentZone.region_id == region_id,
            )
            .first()
        )
        if shipment_zone:
            if shipment_zone.is_deleted:
                shipment_zone.is_deleted = False
                return json_response()
            else:
                return json_response(409, HttpText.HTTP_409)

        # Insert shipment zone
        shipment_zone = ShipmentZone(
            order=order,
            country_id=country_id,
            region_id=region_id,
        )
        s.add(shipment_zone)

    return json_response()


@api_bp.patch("/shipment-zones/<int:shipment_zone_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_shipment_zones_id(shipment_zone_id: int) -> Response:
    country_id, has_country_id = json_get("country_id", int)
    order, has_order = json_get("order", int)
    region_id, has_region_id = json_get("region_id", int)

    with conn.begin() as s:
        # Get shipment zone
        shipment_zone = s.query(ShipmentZone).filter_by(id=shipment_zone_id).first()
        if not shipment_zone:
            return json_response(404, HttpText.HTTP_404)

        # Update shipment zone
        if has_order:
            shipment_zone.order = order
        if has_country_id:
            shipment_zone.country_id = country_id
        if has_region_id:
            shipment_zone.region_id = region_id

    return json_response()


@api_bp.delete("/shipment-zones/<int:shipment_zone_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_shipment_zones_id(shipment_zone_id: int) -> Response:
    with conn.begin() as s:
        # Delete shipment zone
        shipment_zone = s.query(ShipmentZone).filter_by(id=shipment_zone_id).first()
        if not shipment_zone:
            return json_response(404, HttpText.HTTP_404)
        shipment_zone.is_deleted = True

        # Delete shipment zones
        shipment_methods = (
            s.query(ShipmentMethod)
            .filter_by(zone_id=shipment_zone_id, is_deleted=False)
            .all()
        )
        for shipment_method in shipment_methods:
            shipment_method.is_deleted = True

    return json_response()


#
# Functions
#
