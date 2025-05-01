# time_management/app/admin_auth_starlette.py
from typing import Any, Optional, Dict, TYPE_CHECKING
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.templating import Jinja2Templates # Import for type hint
from jose import JWTError

from starlette_admin.auth import BaseAuthProvider

from app import security, crud, models
from app.database import SyncSessionLocal as SessionLocal

if TYPE_CHECKING:
    from starlette_admin.base import Admin

class AdminAuthProvider(BaseAuthProvider):
    login_path = "/admin/login" # Still useful for reference
    logout_path = "/admin/logout"

    # Remove __init__ again
    # def __init__(self, admin_instance: "Admin" = None):
    #     self.admin = admin_instance

    # --- Core Logic Methods ---
    async def _login_logic(self, request: Request, form_data: Dict) -> bool:
        # Keep as is
        username = form_data.get("username")
        password = form_data.get("password")
        if not username or not password: return False
        db = SessionLocal()
        try:
            user = crud.get_employee_by_username_sync(db, username)
            if not user or not user.is_admin or not security.pwd_context.verify(password, user.hashed_password):
                return False
            access_token = security.create_access_token(data={"sub": str(user.id)})
            request.session.update({"token": access_token})
            print(f"Admin Login Successful: User '{username}'")
            return True
        except Exception: return False
        finally:
            if db: db.close()

    async def _logout_logic(self, request: Request) -> None:
         # Keep as is
        print("Admin Logout Action Triggered")
        try:
            request.session.clear()
            print("Session cleared successfully.")
        except Exception as e: print(f"Error clearing session: {e}")

    # --- Authentication Methods for Starlette Admin Internal Checks ---
    async def is_authenticated(self, request: Request) -> bool:
        # Keep the version with print statements for now
        print("\n--- is_authenticated Check ---")
        token = request.session.get("token")
        print(f"Token from session: {token}")
        if not token:
            print("Result: No token found, returning False.")
            return False
        db = SessionLocal()
        try:
            print("Verifying token...")
            user_id = security.verify_token(token, credentials_exception=JWTError("Invalid Token"))
            print(f"User ID from token: {user_id}")
            if user_id is None:
                 print("Result: User ID from token is None, returning False.")
                 return False
            print(f"Fetching user with ID {user_id} from DB...")
            user = crud.get_employee_sync(db, user_id=user_id)
            print(f"User from DB: {user}")
            if user is None:
                 print(f"Result: User with ID {user_id} not found, clearing session and returning False.")
                 request.session.clear(); return False
            is_admin_check = user.is_admin
            print(f"Is user admin? {is_admin_check}")
            if not is_admin_check:
                 print(f"Result: User '{user.username}' (ID: {user_id}) is not an admin, clearing session and returning False.")
                 request.session.clear(); return False
            request.state.admin_user = user
            print(f"Result: Auth Check Successful for user '{user.username}', returning True.")
            return True
        except JWTError as e:
            print(f"Auth Check Failed: Invalid JWT token - {e}, clearing session and returning False.")
            request.session.clear(); return False
        except Exception as e:
            print(f"Auth Check Error: An unexpected error occurred - {e}, returning False.")
            return False
        finally:
            if db: db.close()
            print("--- End is_authenticated Check ---\n")

    async def get_admin_user(self, request: Request) -> Optional[Any]:
        # Keep this method as is
        return getattr(request.state, "admin_user", None)

    # --- Route Handlers (will be called by FastAPI/Starlette routes) ---
    async def login_get_handler(self, request: Request, templates: Jinja2Templates) -> Response:
        """ Handler for GET /login. Requires templates object. """
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": request.query_params.get("error")}
        )

    async def login_post_handler(self, request: Request) -> Response:
        """ Handler for POST /login """
        form_data = await request.form()
        if await self._login_logic(request, dict(form_data)): # Call the core logic
            # Use standard Starlette URL reversing for the admin index
            return RedirectResponse(request.app.url_path_for("admin:index"), status_code=303)
        # Use standard Starlette URL reversing for the login route itself
        return RedirectResponse(request.app.url_path_for("admin_login") + "?error=1", status_code=303)

    async def logout_handler(self, request: Request) -> Response:
        """ Handler for GET /logout """
        await self._logout_logic(request) # Call the core logic
         # Use standard Starlette URL reversing for the login route
        return RedirectResponse(request.app.url_path_for("admin_login"), status_code=303)

    # --- Simplified setup_admin ---
    def setup_admin(self, admin: "Admin") -> None: # type: ignore
        """ Keep this minimal """
        pass


# Instantiate the provider globally - it doesn't need admin instance at init anymore
auth_provider = AdminAuthProvider()