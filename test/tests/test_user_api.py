class TestUserAPI:
    def test_post_users_success(self, client, user_data):
        resp = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["email"] == user_data["email"]
        assert data["bulk_email"] == user_data["bulk_email"]
        assert "id" in data
        assert "is_active" in data
        assert "role_id" in data

        assert "password" not in data
        assert "password_hash" not in data

    def test_post_users_minimal_data(self, client, user_data_minimal):
        resp = client.post(
            "/api/v1/users",
            json=user_data_minimal,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["email"] == user_data_minimal["email"]
        assert "id" in data

        assert "bulk_email" in data

    def test_post_users_missing_email(self, client):
        resp = client.post(
            "/api/v1/users",
            json={
                "password": "password123",
                "password_eval": "password123",
            },
        )

        assert resp.status_code == 400

    def test_post_users_missing_password(self, client):
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
            },
        )

        assert resp.status_code == 400

    def test_post_users_invalid_email(self, client):
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "invalid-email",
                "password": "password123",
                "password_eval": "password123",
            },
        )

        assert resp.status_code == 400

    def test_post_users_password_too_short(self, client):
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
                "password": "short",
                "password_eval": "short",
            },
        )

        assert resp.status_code == 400

    def test_post_users_password_mismatch(self, client):
        resp = client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
                "password": "password123",
                "password_eval": "different123",
            },
        )

        assert resp.status_code == 400

    def test_post_users_duplicate_email(self, client, user_data):
        response1 = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert response1.status_code == 200

        response2 = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert response2.status_code == 409

    def test_post_users_case_insensitive_email(self, client, user_data):
        response1 = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert response1.status_code == 200

        user_data_upper = user_data.copy()
        user_data_upper["email"] = user_data["email"].upper()

        response2 = client.post(
            "/api/v1/users",
            json=user_data_upper,
        )

        assert response2.status_code == 409

    def test_get_users_with_email_filter(self, client, user_data):
        create_response = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert create_response.status_code == 200

        resp = client.get(
            f"/api/v1/users?email={user_data['email']}",
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert isinstance(data, list)
        assert len(data) <= 1
        if len(data) > 0:
            assert data[0]["email"] == user_data["email"]

    def test_get_users_without_filter(self, client):
        resp = client.get("/api/v1/users")

        assert resp.status_code == 400

    def test_get_users_id_success(self, client, user_auth, user_data):
        resp = client.get(
            "/api/v1/users/2",
            headers=user_auth,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert "id" in data
        assert "email" in data
        assert "is_active" in data
        assert "role_id" in data

    def test_get_users_id_different_user(self, client, user_auth):
        resp = client.get(
            "/api/v1/users/1",
            headers=user_auth,
        )

        assert resp.status_code == 404

    def test_get_users_id_unauthorized(self, client):
        resp = client.get("/api/v1/users/1")

        assert resp.status_code == 401

    def test_get_users_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.get(
            f"/api/v1/users/{INVALID_ID}",
            headers=user_auth,
        )

        assert resp.status_code == 404

    def test_patch_users_id_success(self, client, user_auth):
        resp = client.patch(
            "/api/v1/users/2",
            headers=user_auth,
            json={"bulk_email": False},
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert not data["bulk_email"]

    def test_patch_users_id_with_billing(self, client, user_auth, billing_data):
        billing_response = client.post(
            "/api/v1/billings",
            headers=user_auth,
            json=billing_data,
        )

        assert billing_response.status_code == 200
        billing_id = billing_response.json["data"]["id"]

        resp = client.patch(
            "/api/v1/users/2",
            headers=user_auth,
            json={"billing_id": billing_id},
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert data["billing_id"] == billing_id

    def test_patch_users_id_different_user(self, client, user_auth):
        resp = client.patch(
            "/api/v1/users/1",
            headers=user_auth,
            json={"bulk_email": False},
        )

        assert resp.status_code == 404

    def test_patch_users_id_unauthorized(self, client):
        resp = client.patch(
            "/api/v1/users/1",
            json={"bulk_email": False},
        )

        assert resp.status_code == 401

    def test_patch_users_id_not_found(self, client, user_auth, INVALID_ID):
        resp = client.patch(
            f"/api/v1/users/{INVALID_ID}",
            headers=user_auth,
            json={"bulk_email": False},
        )

        assert resp.status_code == 404

    def test_patch_users_id_invalid_billing_id(self, client, user_auth, INVALID_ID):
        resp = client.patch(
            "/api/v1/users/2",
            headers=user_auth,
            json={"billing_id": INVALID_ID},
        )

        assert resp.status_code == 400

    def test_user_role_assignment(self, client, user_data):
        resp = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert "role_id" in data
        assert data["role_id"] is not None

    def test_user_activation_status(self, client, user_data):
        resp = client.post(
            "/api/v1/users",
            json=user_data,
        )

        assert resp.status_code == 200
        data = resp.json["data"]

        assert "is_active" in data
        assert isinstance(data["is_active"], bool)
