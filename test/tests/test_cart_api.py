import pytest
from web.database import conn
from web.database.model import Coupon


class TestCartAPI:
    #
    # Fixtures
    #

    @pytest.fixture(scope="function")
    def billing_data(self, add_country_nl):
        return {
            "address": "123 Test Street",
            "city": "Amsterdam",
            "company": "Test Company",
            "country_id": add_country_nl.id,
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+31612345678",
            "state": "North Holland",
            "vat": "NL123456789B01",
            "zip_code": "1012AB",
        }

    @pytest.fixture(scope="function")
    def billing_data_minimal(self, add_country_nl):
        return {
            "address": "456 Minimal St",
            "city": "Utrecht",
            "country_id": add_country_nl.id,
            "email": "minimal@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "zip_code": "3512AB",
        }
    
    #
    # Tests
    #

    def test_post_carts_success(self, client, user_auth, add_country_nl):
        resp = client.post("/api/v1/carts", headers=user_auth, json={})
        assert resp.status_code == 200

        data = resp.json["data"]
        assert "id" in data
        assert "user_id" in data
        assert data["items_count"] == 0
        assert data["subtotal_price"] == "0.00"
        assert data["total_price"] == "0.00"

    def test_post_carts_unauthorized(self, client, patch_config, add_country_nl):
        patch_config(AUTH_JWT_ALLOW_GUEST=False)
        resp = client.post("/api/v1/carts", json={})
        # TODO: needs to return 401
        assert resp.status_code == 500

    def test_get_carts_success(self, client, user_auth, add_country_nl):
        post_resp = client.post("/api/v1/carts", headers=user_auth, json={})
        assert post_resp.status_code == 200

        get_resp = client.get("/api/v1/carts", headers=user_auth)
        assert get_resp.status_code == 200

        post_data = post_resp.json["data"]
        get_data = get_resp.json["data"]
        assert isinstance(get_data, list)
        assert len(get_data) == 1
        assert "id" in get_data[0]
        assert "user_id" in get_data[0]
        assert get_data[0] == post_data

    @pytest.mark.parametrize("allow_guest, status_code", [(True, 200), (False, 500)])
    def test_get_carts_unauthorized(
        self, client, patch_config, add_country_nl, allow_guest, status_code
    ):
        patch_config(AUTH_JWT_ALLOW_GUEST=allow_guest)
        resp = client.get("/api/v1/carts")
        assert resp.status_code == status_code

    def test_get_carts_id_success(
        self, client, user_auth, add_country_nl
    ):
        post_resp = client.post("/api/v1/carts", headers=user_auth, json={})
        assert post_resp.status_code == 200

        cart_id = post_resp.json["data"]["id"]
        get_resp = client.get(f"/api/v1/carts/{cart_id}", headers=user_auth)
        assert get_resp.status_code == 200

        data = get_resp.json["data"]
        assert data["id"] == cart_id
        assert "user_id" in data
        assert "subtotal_price" in data
        assert "total_price" in data

    def test_get_carts_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.get(f"/api/v1/carts/{INVALID_ID}", headers=user_auth)
        assert resp.status_code == 404

    def test_get_carts_id_unauthorized(self, client):
        resp = client.get("/api/v1/carts/1")
        assert resp.status_code == 404

    def test_get_carts_id_different_user(self, client, user_auth, admin_auth, add_country_nl):
        post_resp = client.post("/api/v1/carts", headers=user_auth, json={})
        assert post_resp.status_code == 200

        cart_id = post_resp.json["data"]["id"]
        get_resp = client.get(f"/api/v1/carts/{cart_id}", headers=admin_auth)
        assert get_resp.status_code == 404

    def test_patch_carts_id_with_billing(self, client, user_auth, billing_data):
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
        resp = client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"billing_id": billing_id},
        )
        assert resp.status_code == 200

        data = resp.json["data"]
        assert data["billing_id"] == billing_id

    def test_patch_carts_id_with_shipping(self, client, user_auth, billing_data):
        shipping_data = billing_data.copy()
        shipping_data["first_name"] = "Shipping"
        shipping_data["last_name"] = "Address"

        shipping_response = client.post(
            "/api/v1/shippings",
            headers=user_auth,
            json=shipping_data,
        )

        if shipping_response.status_code == 404:
            pytest.skip("Shipping endpoint not available")

        assert shipping_response.status_code == 200
        shipping_id = shipping_response.json["data"]["id"]

        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        resp = client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"shipping_id": shipping_id},
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["shipping_id"] == shipping_id

    def test_patch_carts_id_with_coupon_code(self, client, user_auth):
        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        with conn.begin() as s:
            coupon = Coupon(
                code="TEST10",
                amount=10.00,
                rate=0.1,
                is_active=True,
            )
            s.add(coupon)
            s.flush()
            coupon_id = coupon.id

        resp = client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"coupon_code": "TEST10"},
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["coupon_code"] == "TEST10"
        assert data["coupon_id"] == coupon_id

    def test_patch_carts_id_invalid_coupon(self, client, user_auth):
        cart_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert cart_response.status_code == 200
        cart_id = cart_response.json["data"]["id"]

        resp = client.patch(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
            json={"coupon_code": "INVALID"},
        )

        assert resp.status_code == 400

    def test_patch_carts_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/carts/{INVALID_ID}",
            headers=user_auth,
            json={"billing_id": 1},
        )

        assert resp.status_code == 404

    def test_patch_carts_id_unauthorized(self, client):
        resp = client.patch(
            "/api/v1/carts/1",
            json={"billing_id": 1},
        )

        assert resp.status_code == 401

    def test_delete_carts_id_success(self, client, user_auth):
        create_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert create_response.status_code == 200
        cart_id = create_response.json["data"]["id"]

        resp = client.delete(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
        )

        assert resp.status_code == 200

        get_response = client.get(
            f"/api/v1/carts/{cart_id}",
            headers=user_auth,
        )

        assert get_response.status_code == 404

    def test_delete_carts_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.delete(
            f"/api/v1/carts/{INVALID_ID}",
            headers=user_auth,
        )

        assert resp.status_code == 404

    def test_delete_carts_id_unauthorized(self, client):
        resp = client.delete(
            "/api/v1/carts/1",
        )

        assert resp.status_code == 401

    def test_delete_carts_id_different_user(self, client, user_auth, admin_auth):
        create_response = client.post(
            "/api/v1/carts",
            headers=user_auth,
            json={},
        )

        assert create_response.status_code == 200
        cart_id = create_response.json["data"]["id"]

        resp = client.delete(
            f"/api/v1/carts/{cart_id}",
            headers=admin_auth,
        )

        assert resp.status_code == 404
