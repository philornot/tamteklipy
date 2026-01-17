"""
Router dla autoryzacji — logowanie, rejestracja, tokeny JWT
"""
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.exceptions import DatabaseError
from app.core.exceptions import DuplicateError
from app.core.security import hash_password
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user_from_token
)
from app.models.user import User
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm
)
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse, UserWithToken
from app.schemas.user import UserUpdate
from app.services.password_reset_utils import (
    create_password_reset_token,
    verify_reset_token
)
from fastapi import APIRouter, Depends
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


async def send_reset_email_task(email: str, token: str):
    """
    Background task to send password reset email.

    TODO: Implement actual email sending (TK-275)
    For now, just log the token (development only!)

    Args:
        email: User's email address
        token: Password reset token
    """
    reset_link = f"https://tamteklipy.pl/reset-password?token={token}"

    # TODO: Replace with actual email service
    logger.info(f"[DEV] Password reset link for {email}: {reset_link}")
    logger.info(f"[DEV] Token: {token}")

    # In production, use email service:
    # await email_service.send_password_reset_email(email, reset_link)


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Endpoint logowania - zwraca JWT token.

    Fixed version:
    - Proper error messages (no DB details in response)
    - Explicit session handling
    - Early returns to prevent unnecessary queries

    POST /api/auth/login
    Body (form-data):
        - username: str
        - password: str

    Returns:
        Token: JWT access token i typ tokenu
    """
    try:
        # 1. Znajdź użytkownika (case-insensitive)
        username_lower = form_data.username.lower().strip()

        user = db.query(User).filter(
            User.username == username_lower
        ).first()

        # 2. Sprawdź czy użytkownik istnieje
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username_lower}")
            raise AuthenticationError(
                message="Nieprawidłowa nazwa użytkownika lub hasło"
            )

        # 3. Sprawdź czy konto jest aktywne
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username_lower}")
            raise AuthenticationError(
                message="Konto jest nieaktywne"
            )

        # 4. Weryfikacja hasła
        password_provided = (form_data.password or "").strip()

        if not user.hashed_password:
            # User ma puste hasło - dozwolone tylko jeśli podane hasło też puste
            if password_provided != "":
                logger.warning(f"Login failed for {username_lower}: empty password expected")
                raise AuthenticationError(
                    message="Nieprawidłowa nazwa użytkownika lub hasło"
                )
        else:
            # Weryfikuj hash
            if not verify_password(password_provided, user.hashed_password):
                logger.warning(f"Login failed for {username_lower}: wrong password")
                raise AuthenticationError(
                    message="Nieprawidłowa nazwa użytkownika lub hasło"
                )

        # 5. Utwórz JWT token
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            scopes=user.award_scopes or []
        )

        logger.info(f"User logged in successfully: {username_lower}")

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except AuthenticationError:
        # Re-raise auth errors as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Login error for {form_data.username}: {e}", exc_info=True)
        raise AuthenticationError(
            message="Wystąpił błąd podczas logowania"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    """
    Endpoint rejestracji nowego użytkownika.
    UWAGA: Ten endpoint powinien być chroniony (tylko admin) - TODO: dodać middleware

    POST /api/auth/register
    Body:
        - username: str
        - email: str (optional)
        - password: str
        - full_name: str (optional)
        - award_scopes: List[str] (optional)

    Returns:
        UserResponse: Dane utworzonego użytkownika
    """
    try:
        # 1. Walidacja username
        username_lower = user_data.username.lower().strip()

        if not username_lower:
            raise DuplicateError(
                resource="Użytkownik",
                field="username",
                value="Username nie może być pusty"
            )

        # 2. Sprawdź duplikat username
        existing_user = db.query(User).filter(
            User.username == username_lower
        ).first()

        if existing_user:
            raise DuplicateError(
                resource="Użytkownik",
                field="username",
                value=username_lower
            )

        # 3. Sprawdź duplikat email (jeśli podany)
        if user_data.email:
            email_lower = user_data.email.lower().strip()

            existing_email = db.query(User).filter(
                User.email == email_lower
            ).first()

            if existing_email:
                raise DuplicateError(
                    resource="Użytkownik",
                    field="email",
                    value=email_lower
                )
        else:
            email_lower = None

        # 4. Utwórz użytkownika
        new_user = User(
            username=username_lower,
            email=email_lower,
            hashed_password=hash_password(user_data.password or ""),
            full_name=user_data.full_name,
            is_active=user_data.is_active if hasattr(user_data, 'is_active') else True,
            is_admin=False,  # Zawsze False dla public registration
            award_scopes=user_data.award_scopes or []
        )

        db.add(new_user)
        db.flush()  # Get user.id before creating personal award

        # 5. Utwórz osobistą nagrodę
        from app.models.award_type import AwardType

        personal_award = AwardType(
            name=f"award:personal_{new_user.username}",
            display_name=f"Nagroda {new_user.full_name or new_user.username}",
            description=f"Osobista nagroda użytkownika {new_user.username}",
            lucide_icon="trophy",
            color="#FFD700",
            is_personal=True,
            is_system_award=False,
            created_by_user_id=new_user.id
        )

        db.add(personal_award)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User registered: {new_user.username} with personal award")

        return new_user

    except (DuplicateError, AuthenticationError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}", exc_info=True)
        raise DatabaseError(message="Nie można utworzyć użytkownika")


@router.get("/me", response_model=UserResponse)
async def read_me(current_user: User = Depends(get_current_user)):
    """
    Zwraca dane aktualnie zalogowanego użytkownika.
    Wymaga nagłówka Authorization: Bearer <token>

    GET /api/auth/me
    """
    logger.debug(f"User {current_user.username}: is_admin={current_user.is_admin}")
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
        user_update: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Aktualizacja profilu użytkownika.

    PATCH /api/auth/me
    Body:
    {
      "full_name": "Nowa nazwa",
      "email": "nowy@email.pl",
      "password": "NoweHaslo123!" (opcjonalne)
    }
    """
    try:
        # 1. Sprawdź duplikat email
        if user_update.email and user_update.email != current_user.email:
            email_lower = user_update.email.lower().strip()

            existing_email = db.query(User).filter(
                User.email == email_lower,
                User.id != current_user.id
            ).first()

            if existing_email:
                raise DuplicateError(
                    resource="Email",
                    field="email",
                    value=email_lower
                )

        # 2. Update pól
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name.strip()

        if user_update.email is not None:
            current_user.email = user_update.email.lower().strip()

        if user_update.password is not None:
            password_stripped = user_update.password.strip()
            current_user.hashed_password = hash_password(password_stripped)

        # 3. Commit changes
        db.commit()
        db.refresh(current_user)

        logger.info(f"User {current_user.username} updated profile")

        return current_user

    except DuplicateError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update user {current_user.username}: {e}")
        raise DatabaseError(message="Nie można zaktualizować profilu")


@router.post("/request-password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
        request_data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Request password reset token.

    POST /api/auth/request-password-reset
    Body: {"email": "user@example.com"}

    Security considerations:
    - Always returns success message (don't leak user existence)
    - Token sent via email only
    - 30-minute expiration
    - Invalidates previous unused tokens

    Returns:
        PasswordResetResponse: Generic success message
    """
    email = request_data.email.lower().strip()

    logger.info(f"Password reset requested for email: {email}")

    # Find user by email
    user = db.query(User).filter(User.email == email).first()

    # SECURITY: Always return success, even if email doesn't exist
    # This prevents email enumeration attacks
    if not user:
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return PasswordResetResponse()

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Password reset requested for inactive user: {email}")
        # Still return success for security
        return PasswordResetResponse()

    # Generate reset token
    try:
        token_obj = create_password_reset_token(
            user_id=user.id,
            db=db,
            expiration_minutes=30
        )

        # Queue email sending in background
        background_tasks.add_task(
            send_reset_email_task,
            email=user.email,
            token=token_obj.token
        )

        logger.info(
            f"Password reset token created for user {user.username} "
            f"(expires: {token_obj.expires_at})"
        )

    except Exception as e:
        logger.error(f"Failed to create reset token for {email}: {e}", exc_info=True)
        # Still return success for security
        pass

    return PasswordResetResponse()


@router.post("/reset-password")
async def reset_password(
        reset_data: PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    """
    Reset password using token.

    POST /api/auth/reset-password
    Body: {
        "token": "abc123...",
        "new_password": "NewSecurePassword123!"
    }

    Returns:
        dict: Success message

    Raises:
        AuthenticationError: Invalid or expired token
        ValidationError: Weak password
    """
    token = reset_data.token
    new_password = reset_data.new_password

    # Verify token
    token_obj = verify_reset_token(token, db)

    if not token_obj:
        logger.warning(f"Invalid or expired reset token used")
        raise AuthenticationError(
            message="Invalid or expired reset token",
            details={"hint": "Request a new password reset"}
        )

    # Get user
    user = token_obj.user

    if not user.is_active:
        logger.warning(f"Reset attempt for inactive user: {user.username}")
        raise AuthenticationError(
            message="Account is inactive"
        )

    # Validate new password
    if len(new_password) < 8:
        raise ValidationError(
            message="Password must be at least 8 characters",
            field="new_password"
        )

    # Update password
    try:
        user.hashed_password = hash_password(new_password)

        # Mark token as used
        token_obj.mark_as_used()

        db.commit()

        logger.info(f"Password reset successful for user: {user.username}")

        return {
            "message": "Password has been reset successfully",
            "username": user.username
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset password: {e}", exc_info=True)
        raise AuthenticationError(
            message="Failed to reset password"
        )
