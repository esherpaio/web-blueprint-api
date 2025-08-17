import pytest


class TestShippingAPI:
    #
    # Fixtures
    #

    @pytest.fixture(scope="function")
    def shipping_data(self, add_country_nl):
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
            "zip_code": "1012AB",
        }

    @pytest.fixture(scope="function")
    def shipping_data_minimal(self, add_country_nl):
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

    def test_post_shippings_success(self, client, user_auth, shipping_data):
        resp = client.post("/api/v1/shippings", headers=user_auth, json=shipping_data)
        assert resp.status_code == 200

        data = resp.json["data"]
        assert "id" in data
        assert "user_id" in data
        assert data["address"] == shipping_data["address"]
        assert data["city"] == shipping_data["city"]
        assert data["company"] == shipping_data["company"]
        assert data["country_id"] == shipping_data["country_id"]
        assert data["email"] == shipping_data["email"]
        assert data["first_name"] == shipping_data["first_name"]
        assert data["last_name"] == shipping_data["last_name"]
        assert data["phone"] == shipping_data["phone"]
        assert data["state"] == shipping_data["state"]
        assert data["zip_code"] == shipping_data["zip_code"]

    def test_post_shippings_minimal_data(
        self, client, user_auth, shipping_data_minimal
    ):
        resp = client.post(
            "/api/v1/shippings",
            headers=user_auth,
            json=shipping_data_minimal,
        )
        assert resp.status_code == 200

        data = resp.json["data"]
        assert data["address"] == shipping_data_minimal["address"]
        assert data["city"] == shipping_data_minimal["city"]
        assert data["company"] is None
        assert data["country_id"] == shipping_data_minimal["country_id"]
        assert data["email"] == shipping_data_minimal["email"]
        assert data["first_name"] == shipping_data_minimal["first_name"]
        assert data["last_name"] == shipping_data_minimal["last_name"]
        assert data["phone"] is None
        assert data["state"] is None
        assert data["zip_code"] == shipping_data_minimal["zip_code"]

    @pytest.mark.parametrize("allow_guest, status_code", [(True, 200), (False, 401)])
    def test_post_shippings_unauthorized(
        self, client, shipping_data, patch_config, allow_guest, status_code
    ):
        patch_config(AUTH_JWT_ALLOW_GUEST=allow_guest)
        resp = client.post("/api/v1/shippings", json=shipping_data)
        assert resp.status_code == status_code

    def test_post_shippings_invalid_country(
        self, client, user_auth, shipping_data, INVALID_ID
    ):
        shipping_data["country_id"] = INVALID_ID
        resp = client.post("/api/v1/shippings", headers=user_auth, json=shipping_data)
        assert resp.status_code == 409

    def test_post_shippings_missing_required_fields(self, client, user_auth):
        resp = client.post("/api/v1/shippings", headers=user_auth, json={})
        assert resp.status_code == 400

    def test_get_shippings_id_success(self, client, user_auth, shipping_data):
        resp1 = client.post(
            "/api/v1/shippings",
            headers=user_auth,
            json=shipping_data,
        )
        assert resp1.status_code == 200

        shipping_id = resp1.json["data"]["id"]
        resp2 = client.get(f"/api/v1/shippings/{shipping_id}", headers=user_auth)
        assert resp2.status_code == 200

        data = resp2.json["data"]
        assert data["id"] == shipping_id
        assert data["address"] == shipping_data["address"]
        assert data["city"] == shipping_data["city"]
        assert data["email"] == shipping_data["email"]

    def test_get_shippings_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.get(f"/api/v1/shippings/{INVALID_ID}", headers=user_auth)
        assert resp.status_code == 404

    def test_get_shippings_id_unauthorized(self, client, shipping_data):
        resp = client.get("/api/v1/shippings/1")
        assert resp.status_code == 404

    def test_get_shippings_id_different_user(
        self, client, user_auth, admin_auth, shipping_data
    ):
        resp1 = client.post(
            "/api/v1/shippings",
            headers=user_auth,
            json=shipping_data,
        )
        assert resp1.status_code == 200

        shipping_id = resp1.json["data"]["id"]
        resp2 = client.get(f"/api/v1/shippings/{shipping_id}", headers=admin_auth)
        assert resp2.status_code == 404

    def test_patch_shippings_id_success(self, client, user_auth, shipping_data):
        resp1 = client.post("/api/v1/shippings", headers=user_auth, json=shipping_data)
        assert resp1.status_code == 200

        shipping_id = resp1.json["data"]["id"]
        shipping_data_updated = {
            "address": "999 Updated Street",
            "city": "Rotterdam",
            "phone": "+31687654321",
        }
        resp2 = client.patch(
            f"/api/v1/shippings/{shipping_id}",
            headers=user_auth,
            json=shipping_data_updated,
        )
        assert resp2.status_code == 200

        data = resp2.json["data"]
        assert data["address"] == shipping_data_updated["address"]
        assert data["city"] == shipping_data_updated["city"]
        assert data["phone"] == shipping_data_updated["phone"]
        assert data["first_name"] == shipping_data["first_name"]
        assert data["last_name"] == shipping_data["last_name"]

    def test_patch_shippings_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/shippings/{INVALID_ID}",
            headers=user_auth,
            json={"address": "New Address"},
        )
        assert resp.status_code == 404

    def test_patch_shippings_id_unauthorized(self, client):
        resp = client.patch(
            "/api/v1/shippings/1",
            json={"address": "New Address"},
        )
        assert resp.status_code == 404

    def test_patch_shippings_id_invalid_country(
        self, client, user_auth, shipping_data, INVALID_ID
    ):
        create_response = client.post(
            "/api/v1/shippings",
            headers=user_auth,
            json=shipping_data,
        )
        assert create_response.status_code == 200

        shipping_id = create_response.json["data"]["id"]
        resp = client.patch(
            f"/api/v1/shippings/{shipping_id}",
            headers=user_auth,
            json={"country_id": INVALID_ID},
        )
        assert resp.status_code == 409
