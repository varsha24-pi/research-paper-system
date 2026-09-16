import os
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# -----------------------------------------------------------------------------
# JWT Configuration
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "academic_research_paper_intelligence_system_secret_key_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 Hours

# OAuth2 Scheme for Swagger UI Authorization Header Integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# -----------------------------------------------------------------------------
# Pydantic Schemas for Request / Response Models
# -----------------------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=100, description="Plain text password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of researcher")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or Email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    full_name: str


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    created_at: str


# -----------------------------------------------------------------------------
# Password & JWT Helper Utilities
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes a plain password using bcrypt with automated salt generation."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes user identity payload into a secure signed JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI Dependency: Extracts and verifies JWT from 'Authorization: Bearer <token>' header.
    Returns the authenticated User model or raises HTTP 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials or token has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            raise credentials_exception

    except (jwt.PyJWTError, Exception):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional Dependency: If valid token is present, returns User; otherwise returns None
    (allowing unauthenticated guest / demo workflows during early development).
    """
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None


# -----------------------------------------------------------------------------
# Authentication API Routes
# -----------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new researcher account"
)
def register_user(
    user_in: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    1. Validates username and email are unique.
    2. Hashes the password using bcrypt.
    3. Saves the new User record in MySQL.
    """
    # Check if username already exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already taken."
        )

    # Check if email already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_in.email}' is already registered."
        )

    # Create new user with hashed password
    new_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name.strip()
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "created_at": new_user.created_at.isoformat()
        }
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during user registration: {str(err)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login (returns JWT Access Token)"
)
def login_user(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user via JSON payload and returns a signed JWT access token.
    """
    identifier = credentials.username.strip()
    password = credentials.password

    # Lookup user by username OR email
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT Token
    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "email": user.email
    }
    access_token = create_access_token(token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }


@router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=False
)
def login_oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 Password Request Form endpoint for native Swagger UI Authorize integration.
    """
    identifier = form_data.username.strip()
    password = form_data.password

    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.username, "user_id": user.id, "email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in user profile"
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Protected Endpoint: Requires a valid JWT token in the Authorization header.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at.isoformat()
    }
