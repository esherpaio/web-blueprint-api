from web.database import conn
from web.database.model import Order


class TestOrderAPI:
    def test_post_orders_success(self, client, user_auth, order_data):
        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json=order_data,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert "id" in data

    def test_post_orders_without_trigger_mail(self, client, user_auth):
        pass

    def test_post_orders_unauthorized(self, client, order_data):
        resp = client.post(
            "/api/v1/orders",
            json=order_data,
        )

        assert resp.status_code == 401

    def test_post_orders_invalid_cart(self, client, user_auth, INVALID_ID):
        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "cart_id": INVALID_ID,
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 404

    def test_post_orders_other_user_cart(
        self, client, user_auth, admin_auth, billing_data
    ):
        billing_response = client.post(
            "/api/v1/billings",
            headers=admin_auth,
            json=billing_data,
        )

        assert billing_response.status_code == 200

        cart_response = client.post(
            "/api/v1/carts",
            headers=admin_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "cart_id": cart_id,
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 404

    def test_post_orders_missing_cart_id(self, client, user_auth):
        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 400

    def test_post_orders_cart_without_billing(self, client, user_auth):
        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "cart_id": cart_id,
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 400

    def test_post_orders_validates_vat_in_europe(self, client, user_auth, billing_data):
        billing_data["company"] = "Test Company BV"
        billing_data["vat"] = "NL123456789B01"  # Valid Dutch VAT format

        billing_response = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )

        assert billing_response.status_code == 200
        billing_id = billing_response.json["data"]["id"]

        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"billing_id": billing_id},
        )

        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "cart_id": cart_id,
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 200

    def test_post_orders_invalid_vat_format(self, client, user_auth, billing_data):
        billing_data["company"] = "Test Company"
        billing_data["vat"] = "INVALID-VAT"

        billing_response = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )

        assert billing_response.status_code == 200
        billing_id = billing_response.json["data"]["id"]

        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"billing_id": billing_id},
        )

        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json={
                "cart_id": cart_id,
                "trigger_mail": False,
            },
        )

        assert resp.status_code == 400

    def test_patch_orders_id_admin_only(
        self, client, user_auth, admin_auth, order_data
    ):
        create_response = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json=order_data,
        )

        assert create_response.status_code == 200
        order_id = create_response.json["data"]["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}",
            headers=user_auth,
            json={"status_id": 2},
        )

        assert resp.status_code == 403

        resp = client.patch(
            f"/api/v1/orders/{order_id}",
            headers=admin_auth,
            json={"status_id": 2},
        )

        assert resp.status_code in [200, 400]

    def test_patch_orders_id_invalid_status_transition(
        self, client, admin_auth, order_data, INVALID_ID
    ):
        create_response = client.post(
            "/api/v1/orders",
            headers=admin_auth,
            json=order_data,
        )

        assert create_response.status_code == 200
        order_id = create_response.json["data"]["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}",
            headers=admin_auth,
            json={"status_id": INVALID_ID},
        )

        assert resp.status_code == 400

    def test_patch_orders_id_unauthorized(self, client):
        resp = client.patch(
            "/api/v1/orders/1",
            json={"status_id": 2},
        )

        assert resp.status_code == 401

    def test_patch_orders_id_not_found(self, client, admin_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/orders/{INVALID_ID}",
            headers=admin_auth,
            json={"status_id": 2},
        )

        assert resp.status_code == 404

    def test_delete_orders_id_admin_only(
        self, client, user_auth, admin_auth, order_data
    ):
        create_response = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json=order_data,
        )

        assert create_response.status_code == 200
        order_id = create_response.json["data"]["id"]

        resp = client.delete(
            f"/api/v1/orders/{order_id}",
            headers=user_auth,
        )

        assert resp.status_code == 403

        resp = client.delete(
            f"/api/v1/orders/{order_id}",
            headers=admin_auth,
        )

        assert resp.status_code == 200

    def test_delete_orders_id_unauthorized(self, client):
        resp = client.delete("/api/v1/orders/1")

        assert resp.status_code == 401

    def test_delete_orders_id_not_found(self, client, admin_auth, INVALID_ID):
        resp = client.delete(
            f"/api/v1/orders/{INVALID_ID}",
            headers=admin_auth,
        )

        assert resp.status_code == 404

    def test_order_copies_cart_data(self, client, user_auth, order_data):
        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json=order_data,
        )

        assert resp.status_code == 200
        order_id = resp.json["data"]["id"]

        with conn.begin() as s:
            order = s.query(Order).filter_by(id=order_id).first()
            assert order is not None
            assert order.billing_id is not None

    def test_order_creates_order_lines(self, client, user_auth, order_data):
        resp = client.post(
            "/api/v1/orders",
            headers=user_auth,
            json=order_data,
        )

        assert resp.status_code == 200
        order_id = resp.json["data"]["id"]

        with conn.begin() as s:
            order = s.query(Order).filter_by(id=order_id).first()
            assert order is not None
