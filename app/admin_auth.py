# In app/main.py (or app/admin_auth.py)

import os
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from jose import JWTError
from app import security, crud, models # Import your security and crud functions
from app.database import SessionLocal # To create a DB session if needed outside requests

# Use the same secret key as the middleware
SESSION_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-sessions")

class AdminAuth(AuthenticationBackend): # Pass secret_key here

    def __init__(self, secret_key: str):
        # Pass the secret_key to the parent class's initializer
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form["username"]
        password = form["password"]

        # --- Use your existing auth logic ---
        db = SessionLocal() # Create a session for this operation
        user = None
        try:
            user = crud.get_employee_by_username(db, username) #
            if not user or not security.pwd_context.verify(password, user.hashed_password): #
                print("Admin Login Failed: Invalid credentials")
                return False # Failed login

            # --- Check if user is admin ---
            if not user.is_admin: #
                print(f"Admin Login Failed: User '{username}' is not an admin.")
                return False # Must be admin to login here

            # --- Create JWT token (like in /api/token) ---
            access_token = security.create_access_token(data={"sub": str(user.id)}) #

            # --- Store token in session ---
            request.session.update({"token": access_token})
            print(f"Admin Login Successful: User '{username}'")

        except Exception as e:
            print(f"Admin Login Error: {e}")
            return False # Handle potential errors
        finally:
            db.close() # Ensure session is closed

        return True # Successful login

    async def logout(self, request: Request) -> bool:
        print("Admin Logout")
        request.session.clear() # Clear the session
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            # print("Admin Authenticate: No token in session")
            return False # Not authenticated

        # --- Use your existing token verification and user check ---
        db = SessionLocal()
        try:
            user_id = security.verify_token(token, credentials_exception=None) # Pass None or a dummy exception
            if user_id is None:
                 # print("Admin Authenticate: Invalid token")
                 return False

            user = crud.get_employee(db, user_id=user_id) #
            if user is None or not user.is_admin: #
                # print(f"Admin Authenticate: User {user_id} not found or not admin.")
                return False # User not found or is not admin

            # print(f"Admin Authenticate: Success for user {user.username}")
            return True # User is authenticated and is an admin

        except JWTError:
            # print("Admin Authenticate: JWTError")
            return False # Token decode error
        except Exception as e:
            # print(f"Admin Authenticate Error: {e}")
            return False # Other errors
        finally:
            db.close()

# --- Instantiate the backend ---
authentication_backend = AdminAuth(secret_key=SESSION_SECRET_KEY)