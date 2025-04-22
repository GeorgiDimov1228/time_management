# time_management/app/admin_auth.py
import os
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from jose import JWTError
from app import security, crud, models
from app.database import SyncSessionLocal as SessionLocal

SESSION_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-sessions")

class AdminAuth(AuthenticationBackend):

    # Add the __init__ method and call super().__init__
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)
        # You could add other initializations here if needed

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
             print("Admin Login Failed: Missing username or password")
             return False

        db = SessionLocal()
        user = None
        try:
            # Call the SYNCHRONOUS version explicitly
            user = crud.get_employee_by_username_sync(db, username)
            if not user or not security.pwd_context.verify(password, user.hashed_password):
                print(f"Admin Login Failed: Invalid credentials for user '{username}'")
                return False

            if not user.is_admin:
                print(f"Admin Login Failed: User '{username}' is not an admin.")
                return False

            access_token = security.create_access_token(data={"sub": str(user.id)})
            request.session.update({"token": access_token})
            print(f"Admin Login Successful: User '{username}'")

        except Exception as e:
            print(f"Admin Login Error: An unexpected error occurred - {e}")
            return False
        finally:
            if db:
                db.close()

        return True

    async def logout(self, request: Request) -> bool:
        # This method should now correctly override the base class method
        print("Admin Logout Action Triggered") # Add log to confirm execution
        try:
            request.session.clear()
            print("Session cleared successfully.")
        except Exception as e:
            print(f"Error clearing session during logout: {e}")
            # Decide if you should still return True or False here
            return False # Indicate logout failed if session clearing fails
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        db = SessionLocal()
        try:
            user_id = security.verify_token(token, credentials_exception=JWTError("Invalid Token"))
            if user_id is None:
                 return False

            # Call the SYNCHRONOUS version explicitly
            user = crud.get_employee_sync(db, user_id=user_id)
            if user is None or not user.is_admin:
                request.session.clear()
                return False

            return True

        except JWTError:
            request.session.clear()
            return False
        except Exception as e:
            print(f"Admin Authenticate Error: An unexpected error occurred - {e}")
            return False
        finally:
            if db:
                db.close()

# --- Instantiate the backend ---
# This remains the same
authentication_backend = AdminAuth(secret_key=SESSION_SECRET_KEY)