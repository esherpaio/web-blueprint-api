class TestCountryAPI:
    def test_post_countries_success(self, client, admin_auth, country_data_nl):
        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["code"] == country_data_nl["code"]
        assert data["in_sitemap"] == country_data_nl["in_sitemap"]
        assert data["name"] == country_data_nl["name"]
        assert data["currency_id"] == country_data_nl["currency_id"]
        assert data["region_id"] == country_data_nl["region_id"]
        assert "id" in data

    def test_post_countries_unauthorized_user(self, client, user_auth, country_data_nl):
        resp = client.post(
            "/api/v1/countries",
            headers=user_auth,
            json=country_data_nl,
        )

        assert resp.status_code == 403

    def test_post_countries_unauthorized_guest(
        self, client, guest_auth, country_data_nl
    ):
        resp = client.post(
            "/api/v1/countries",
            headers=guest_auth,
            json=country_data_nl,
        )

        assert resp.status_code == 403

    def test_post_countries_no_auth(self, client, country_data_nl):
        resp = client.post(
            "/api/v1/countries",
            json=country_data_nl,
        )

        assert resp.status_code == 401

    def test_post_countries_missing_required_fields(
        self, client, admin_auth, post_currency_eur, post_region_europe
    ):
        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json={
                "name": "Test Country",
                "currency_id": post_currency_eur.json["data"]["id"],
                "region_id": post_region_europe.json["data"]["id"],
            },
        )

        assert resp.status_code == 400

    def test_post_countries_invalid_currency_id(
        self, client, admin_auth, post_region_europe, INVALID_ID
    ):
        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json={
                "code": "XX",
                "name": "Test Country",
                "currency_id": {INVALID_ID},
                "region_id": post_region_europe.json["data"]["id"],
            },
        )

        assert resp.status_code == 400

    def test_post_countries_invalid_region_id(
        self, client, admin_auth, post_currency_eur, INVALID_ID
    ):
        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json={
                "code": "XX",
                "name": "Test Country",
                "currency_id": post_currency_eur.json["data"]["id"],
                "region_id": INVALID_ID,
            },
        )

        assert resp.status_code == 400

    def test_post_countries_duplicate_code(self, client, admin_auth, country_data_nl):
        response1 = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert response1.status_code == 200

        response2 = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert response2.status_code == 400

    def test_get_countries_success(
        self, client, admin_auth, country_data_nl, country_data_uk
    ):
        client.post("/api/v1/countries", headers=admin_auth, json=country_data_nl)
        client.post("/api/v1/countries", headers=admin_auth, json=country_data_uk)

        resp = client.get("/api/v1/countries")

        assert resp.status_code == 200
        data = resp.json["data"]

        assert isinstance(data, list)
        assert len(data) >= 2

        codes = [country["code"] for country in data]
        assert "NL" in codes
        assert "GB" in codes

    def test_get_countries_ordered_by_name(
        self, client, admin_auth, country_data_nl, country_data_uk
    ):
        client.post("/api/v1/countries", headers=admin_auth, json=country_data_nl)
        client.post("/api/v1/countries", headers=admin_auth, json=country_data_uk)

        resp = client.get("/api/v1/countries")

        assert resp.status_code == 200
        data = resp.json["data"]

        names = [country["name"] for country in data]
        if "the Netherlands" in names and "United Kingdom" in names:
            germany_index = names.index("the Netherlands")
            uk_index = names.index("United Kingdom")
            assert germany_index < uk_index

    def test_get_countries_no_auth_required(self, client, admin_auth, country_data_nl):
        client.post("/api/v1/countries", headers=admin_auth, json=country_data_nl)

        resp = client.get("/api/v1/countries")

        assert resp.status_code == 200
        data = resp.json["data"]

        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_countries_id_success(self, client, admin_auth, country_data_nl):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        resp = client.get(f"/api/v1/countries/{country_id}")

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["id"] == country_id
        assert data["code"] == country_data_nl["code"]
        assert data["name"] == country_data_nl["name"]

    def test_get_countries_id_not_found(self, client, INVALID_ID):
        resp = client.get(f"/api/v1/countries/{INVALID_ID}")

        assert resp.status_code == 404

    def test_get_countries_id_no_auth_required(
        self, client, admin_auth, country_data_nl
    ):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        resp = client.get(f"/api/v1/countries/{country_id}")

        assert resp.status_code == 200

    def test_patch_countries_id_success(self, client, admin_auth, country_data_nl):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        update_data = {
            "state_required": True,
            "vat_required": True,
        }

        resp = client.patch(
            f"/api/v1/countries/{country_id}",
            headers=admin_auth,
            json=update_data,
        )

        assert resp.status_code == 200

    def test_patch_countries_id_unauthorized_user(
        self, client, user_auth, admin_auth, country_data_nl
    ):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        resp = client.patch(
            f"/api/v1/countries/{country_id}",
            headers=user_auth,
            json={"state_required": True},
        )

        assert resp.status_code == 403

    def test_patch_countries_id_not_found(self, client, admin_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/countries/{INVALID_ID}",
            headers=admin_auth,
            json={"state_required": True},
        )

        assert resp.status_code == 404

    def test_patch_countries_id_no_auth(self, client):
        resp = client.patch(
            "/api/v1/countries/1",
            json={"state_required": True},
        )

        assert resp.status_code == 401

    def test_delete_countries_id_success(self, client, admin_auth, country_data_nl):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        resp = client.delete(
            f"/api/v1/countries/{country_id}",
            headers=admin_auth,
        )

        assert resp.status_code == 200

        get_response = client.get(f"/api/v1/countries/{country_id}")
        assert get_response.status_code == 404

    def test_delete_countries_id_unauthorized_user(
        self, client, user_auth, admin_auth, country_data_nl
    ):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        country_id = create_response.json["data"]["id"]

        resp = client.delete(
            f"/api/v1/countries/{country_id}",
            headers=user_auth,
        )

        assert resp.status_code == 403

    def test_delete_countries_id_not_found(self, client, admin_auth, INVALID_ID):
        resp = client.delete(
            f"/api/v1/countries/{INVALID_ID}",
            headers=admin_auth,
        )

        assert resp.status_code == 404

    def test_delete_countries_id_no_auth(self, client):
        resp = client.delete("/api/v1/countries/1")

        assert resp.status_code == 401

    def test_country_data_integrity(self, client, admin_auth, country_data_nl):
        create_response = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert create_response.status_code == 200
        created_data = create_response.json["data"]

        get_response = client.get(f"/api/v1/countries/{created_data['id']}")

        assert get_response.status_code == 200
        retrieved_data = get_response.json["data"]

        assert retrieved_data["code"] == country_data_nl["code"]
        assert retrieved_data["name"] == country_data_nl["name"]
        assert retrieved_data["in_sitemap"] == country_data_nl["in_sitemap"]
        assert retrieved_data["currency_id"] == country_data_nl["currency_id"]
        assert retrieved_data["region_id"] == country_data_nl["region_id"]

    def test_country_code_validation(
        self, client, admin_auth, post_currency_eur, post_region_europe
    ):
        currency_id = post_currency_eur.json["data"]["id"]
        region_id = post_region_europe.json["data"]["id"]

        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json={
                "code": "TOOLONG",
                "name": "Test Country",
                "currency_id": currency_id,
                "region_id": region_id,
            },
        )

        assert resp.status_code == 400

    def test_country_in_sitemap_boolean(self, client, admin_auth, country_data_nl):
        country_data_nl["in_sitemap"] = True

        resp = client.post(
            "/api/v1/countries",
            headers=admin_auth,
            json=country_data_nl,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["in_sitemap"] is True
