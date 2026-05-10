import json
import os
from pathlib import Path


class Settings:
    def __init__(self):
        config_path = Path(__file__).parent.parent / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}. "
                "Create config.json from config.example.json."
            )

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        database = config.get("database", {})
        server = config.get("server", {})
        mavlink = config.get("mavlink", {})
        sitl = config.get("sitl", {})
        cors = config.get("cors", {})

        self.db_host = database.get("host", "127.0.0.1")
        self.db_port = database.get("port", 5432)
        self.db_name = database.get("name", "dcss")
        self.db_user = database.get("user", "postgres")
        self.db_password = database.get("password", "postgres")

        self.server_host = server.get("host", "0.0.0.0")
        self.server_port = server.get("port", 8000)
        self.public_base_url = server.get("public_base_url", f"http://127.0.0.1:{self.server_port}").rstrip("/")
        self.jwt_secret = server.get("jwt_secret", "change-me")
        self.jwt_algorithm = server.get("jwt_algorithm", "HS256")
        self.access_token_expire_minutes = server.get("access_token_expire_minutes", 60)
        self.internal_api_token = server.get("internal_api_token", "change-internal-token")
        self.max_quest = int(server.get("max_quest", 10))

        # Host, который видит Mission Planner на клиентском ПК.
        # Для локальной проверки можно оставить 127.0.0.1.
        # Для сети нужно указать IP или домен сервера.
        self.mavlink_public_host = mavlink.get("public_host", "127.0.0.1")
        self.sitl_port_start = int(mavlink.get("sitl_port_start", 14560))
        self.sitl_port_end = int(mavlink.get("sitl_port_end", 14600))
        self.proxy_port_start = int(mavlink.get("proxy_port_start", 14601))
        self.proxy_port_end = int(mavlink.get("proxy_port_end", 14700))

        self.sim_vehicle_path = sitl.get(
            "sim_vehicle_path",
            "/home/vladik/ardupilot/Tools/autotest/sim_vehicle.py"
        )
        self.sitl_vehicle = sitl.get("vehicle", "ArduCopter")
        self.sitl_startup_delay_sec = int(sitl.get("startup_delay_sec", 15))
        self.sitl_extra_args = sitl.get("extra_args", [])

        self.cors_origins = cors.get("allow_origins", ["http://localhost:5173"])


settings = Settings()
