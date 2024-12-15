from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    # Retrieve credentials from environment variables
    correct_username = os.getenv("BASIC_AUTH_USERNAME", "prometheus")  # Default fallback value if not set
    correct_password = os.getenv("BASIC_AUTH_PASSWORD", "prometheus")  # Default fallback value if not set
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
