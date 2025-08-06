from web.automation import SeedSyncer
from web.database.model import User, UserRoleId


class UserSeedSyncer(SeedSyncer):
    MODEL = User
    KEY = "api_key"
    SEEDS = [
        User(
            api_key="guest",
            email="guest@esherpa.io",
            is_active=True,
            role_id=UserRoleId.GUEST,
        ),
        User(
            api_key="user",
            email="user@esherpa.io",
            is_active=True,
            role_id=UserRoleId.USER,
        ),
        User(
            api_key="admin",
            email="admin@esherpa.io",
            is_active=True,
            role_id=UserRoleId.ADMIN,
        ),
    ]
