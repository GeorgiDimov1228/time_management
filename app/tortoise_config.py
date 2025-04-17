# app/tortoise_config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- MODIFIED DATABASE_URL ---
# Updated the default value to reflect PostgreSQL and the asyncpg driver.
# Tortoise ORM will still prioritize the DATABASE_URL found in your .env file or environment.
# Ensure your actual DATABASE_URL environment variable uses the correct format, e.g.:
# postgresql+asyncpg://your_user:your_password@your_host:your_port/your_db_name
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://yourusername:yourpassword@db:5432/time_management_db" # Updated default
)
# --- END MODIFICATION ---


TORTOISE_ORM_CONFIG = {
    "connections": {
        # Uses the DATABASE_URL defined above
        "default": DATABASE_URL
    },
    "apps": {
        "models": { # 'models' is a standard Tortoise app name
            # Ensure this points to your actual models file
            # Add 'aerich.models' for database migrations using Aerich
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False, # Set to True if you store/require timezone-aware datetimes
    "timezone": "UTC" # Optional: specify timezone if use_tz=True
}

# Note: No SessionLocal or get_db dependency needed anymore.
# Tortoise manages connections internally after initialization.