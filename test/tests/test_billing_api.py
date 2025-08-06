import pytest


class TestBillingAPI:
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

    def test_post_billings_success(self, client, user_auth, billing_data):
        resp = client.post("/api/v1/billings", headers=user_auth, json=billing_data)
        assert resp.status_code == 200

        data = resp.json["data"]
        assert "id" in data
        assert "user_id" in data
        assert data["address"] == billing_data["address"]
        assert data["city"] == billing_data["city"]
        assert data["company"] == billing_data["company"]
        assert data["country_id"] == billing_data["country_id"]
        assert data["email"] == billing_data["email"]
        assert data["first_name"] == billing_data["first_name"]
        assert data["last_name"] == billing_data["last_name"]
        assert data["phone"] == billing_data["phone"]
        assert data["state"] == billing_data["state"]
        assert data["vat"] == billing_data["vat"]
        assert data["zip_code"] == billing_data["zip_code"]

    def test_post_billings_minimal_data(self, client, user_auth, billing_data_minimal):
        resp = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data_minimal,
        )
        assert resp.status_code == 200

        data = resp.json["data"]
        assert data["address"] == billing_data_minimal["address"]
        assert data["city"] == billing_data_minimal["city"]
        assert data["company"] is None
        assert data["country_id"] == billing_data_minimal["country_id"]
        assert data["email"] == billing_data_minimal["email"]
        assert data["first_name"] == billing_data_minimal["first_name"]
        assert data["last_name"] == billing_data_minimal["last_name"]
        assert data["phone"] is None
        assert data["state"] is None
        assert data["vat"] is None
        assert data["zip_code"] == billing_data_minimal["zip_code"]

    @pytest.mark.parametrize("allow_guest, status_code", [(True, 200), (False, 401)])
    def test_post_billings_unauthorized(
        self, client, billing_data, patch_config, allow_guest, status_code
    ):
        patch_config(AUTH_JWT_ALLOW_GUEST=allow_guest)
        resp = client.post("/api/v1/billings", json=billing_data)
        assert resp.status_code == status_code

    def test_post_billings_invalid_country(
        self, client, user_auth, billing_data, INVALID_ID
    ):
        billing_data["country_id"] = INVALID_ID
        resp = client.post("/api/v1/billings", headers=user_auth, json=billing_data)
        assert resp.status_code == 409

    def test_post_billings_missing_required_fields(self, client, user_auth):
        resp = client.post("/api/v1/billings", headers=user_auth, json={})
        assert resp.status_code == 400

    def test_get_billings_id_success(self, client, user_auth, billing_data):
        resp1 = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )
        assert resp1.status_code == 200

        billing_id = resp1.json["data"]["id"]
        resp2 = client.get(f"/api/v1/billings/{billing_id}", headers=user_auth)
        assert resp2.status_code == 200

        data = resp2.json["data"]
        assert data["id"] == billing_id
        assert data["address"] == billing_data["address"]
        assert data["city"] == billing_data["city"]
        assert data["email"] == billing_data["email"]

    def test_get_billings_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.get(f"/api/v1/billings/{INVALID_ID}", headers=user_auth)
        assert resp.status_code == 404

    def test_get_billings_id_unauthorized(self, client, billing_data):
        resp = client.get("/api/v1/billings/1")
        assert resp.status_code == 404

    def test_get_billings_id_different_user(
        self, client, user_auth, admin_auth, billing_data
    ):
        resp1 = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )
        assert resp1.status_code == 200

        billing_id = resp1.json["data"]["id"]
        resp2 = client.get(f"/api/v1/billings/{billing_id}", headers=admin_auth)
        assert resp2.status_code == 404

    def test_patch_billings_id_success(self, client, user_auth, billing_data):
        resp1 = client.post("/api/v1/billings", headers=user_auth, json=billing_data)
        assert resp1.status_code == 200

        billing_id = resp1.json["data"]["id"]
        billing_data_updated = {
            "address": "999 Updated Street",
            "city": "Rotterdam",
            "phone": "+31687654321",
        }
        resp2 = client.patch(
            f"/api/v1/billings/{billing_id}",
            headers=user_auth,
            json=billing_data_updated,
        )
        assert resp2.status_code == 200

        data = resp2.json["data"]
        assert data["address"] == billing_data_updated["address"]
        assert data["city"] == billing_data_updated["city"]
        assert data["phone"] == billing_data_updated["phone"]
        assert data["first_name"] == billing_data["first_name"]
        assert data["last_name"] == billing_data["last_name"]

    def test_patch_billings_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/billings/{INVALID_ID}",
            headers=user_auth,
            json={"address": "New Address"},
        )
        assert resp.status_code == 404

    def test_patch_billings_id_unauthorized(self, client):
        resp = client.patch(
            "/api/v1/billings/1",
            json={"address": "New Address"},
        )
        assert resp.status_code == 404

    def test_patch_billings_id_invalid_country(
        self, client, user_auth, billing_data, INVALID_ID
    ):
        create_response = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )
        assert create_response.status_code == 200

        billing_id = create_response.json["data"]["id"]
        resp = client.patch(
            f"/api/v1/billings/{billing_id}",
            headers=user_auth,
            json={"country_id": INVALID_ID},
        )
        assert resp.status_code == 409
