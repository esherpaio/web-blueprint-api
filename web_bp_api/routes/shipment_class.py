from web.api import HttpText, json_get, json_response
from web.app.blueprint.api_v1 import api_v1_bp
from web.auth import authorize
from web.database import conn
from web.database.model import ShipmentClass, ShipmentMethod, UserRoleLevel
from werkzeug import Response

#
# Configuration
#


#
# Endpoints
#


@api_v1_bp.post("/shipment-classes")
@authorize(UserRoleLevel.ADMIN)
def post_shipment_classes() -> Response:
    name, _ = json_get("name", str, nullable=False)
    order, _ = json_get("order", int, nullable=False)

    with conn.begin() as s:
        # Check if shipment class already exists
        shipment_class = (
            s.query(ShipmentClass).filter_by(name=name, is_deleted=False).first()
        )
        if shipment_class:
            return json_response(409, HttpText.HTTP_409)

        # Insert shipment class
        shipment_class = ShipmentClass(name=name, order=order)
        s.add(shipment_class)

    return json_response()


@api_v1_bp.patch("/shipment-classes/<int:shipment_class_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_shipment_classes_id(shipment_class_id: int) -> Response:
    order, has_order = json_get("order", int)

    with conn.begin() as s:
        # Get shipment zone
        shipment_zone = s.query(ShipmentClass).filter_by(id=shipment_class_id).first()
        if not shipment_zone:
            return json_response(404, HttpText.HTTP_404)

        # Update order
        if has_order:
            shipment_zone.order = order

    return json_response()


@api_v1_bp.delete("/shipment-classes/<int:shipment_class_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_shipment_classes_id(shipment_class_id: int) -> Response:
    with conn.begin() as s:
        # Delete shipment class
        shipment_class = s.query(ShipmentClass).filter_by(id=shipment_class_id).first()
        if not shipment_class:
            return json_response(404, HttpText.HTTP_404)
        shipment_class.is_deleted = True

        # Delete shipment zones
        shipment_methods = (
            s.query(ShipmentMethod)
            .filter_by(class_id=shipment_class_id, is_deleted=False)
            .all()
        )
        for shipment_method in shipment_methods:
            shipment_method.is_deleted = True

    return json_response()


#
# Functions
#
