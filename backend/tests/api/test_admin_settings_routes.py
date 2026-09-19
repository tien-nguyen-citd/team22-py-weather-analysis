from httpx import Client


SETTING_KEY = "forecast.cacheDurationMinutes"


def login(client: Client) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "adminpw"},
    )
    assert response.status_code == 200


def test_list_settings_requires_login(client: Client) -> None:
    response = client.get("/api/admin/settings")

    assert response.status_code == 401
    assert response.json() == {"detail": "Bạn cần đăng nhập"}


def test_list_settings_returns_definitions_and_default(client: Client) -> None:
    login(client)

    response = client.get("/api/admin/settings")

    assert response.status_code == 200
    assert response.json() == [
        {
            "key": SETTING_KEY,
            "category": "Dự báo thời tiết",
            "title": "Thời gian lưu cache (phút)",
            "description": (
                "Thời gian lưu kết quả dự báo và nhiệt độ hiện tại từ "
                "Open-Meteo. Thay đổi chỉ "
                "áp dụng cho lần gọi Open-Meteo mới, không làm thay đổi thời "
                "hạn của dữ liệu đã có trong cache."
            ),
            "type": "integer",
            "value": 30,
            "defaultValue": 30,
            "minimum": 1,
            "maximum": 1440,
            "isModified": False,
        }
    ]


def test_update_setting_persists_value(client: Client) -> None:
    login(client)

    response = client.put(
        f"/api/admin/settings/{SETTING_KEY}", json={"value": 5}
    )

    assert response.status_code == 200
    assert response.json()["value"] == 5
    assert response.json()["isModified"] is True
    assert client.get("/api/admin/settings").json()[0]["value"] == 5


def test_update_setting_rejects_invalid_value(client: Client) -> None:
    login(client)

    response = client.put(
        f"/api/admin/settings/{SETTING_KEY}", json={"value": True}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Giá trị phải là số nguyên"}


def test_update_unknown_setting_returns_not_found(client: Client) -> None:
    login(client)

    response = client.put(
        "/api/admin/settings/khong.ton.tai", json={"value": 5}
    )

    assert response.status_code == 404


def test_reset_setting_returns_default(client: Client) -> None:
    login(client)
    client.put(f"/api/admin/settings/{SETTING_KEY}", json={"value": 5})

    response = client.delete(f"/api/admin/settings/{SETTING_KEY}")

    assert response.status_code == 200
    assert response.json()["value"] == 30
    assert response.json()["isModified"] is False


def test_reset_unknown_setting_returns_not_found(client: Client) -> None:
    login(client)

    response = client.delete("/api/admin/settings/khong.ton.tai")

    assert response.status_code == 404
