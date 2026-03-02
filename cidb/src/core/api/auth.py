import structlog
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError

logger = structlog.get_logger(__name__)

router = Router(tags=["auth"])


class LoginRequest(Schema):
    email: str
    password: str


class UserResponse(Schema):
    id: int
    email: str
    name: str
    is_staff: bool
    is_superuser: bool
    is_editor: bool


class LoginResponse(Schema):
    user: UserResponse
    message: str


class MessageResponse(Schema):
    message: str


class CSRFResponse(Schema):
    csrf_token: str


@router.get("/csrf", response=CSRFResponse)
def get_csrf_token(request: HttpRequest) -> CSRFResponse:
    return CSRFResponse(csrf_token=get_token(request))


@router.post("/login", response=LoginResponse)
def staff_login(request: HttpRequest, payload: LoginRequest) -> LoginResponse:
    user = authenticate(request, username=payload.email, password=payload.password)

    if user is None:
        logger.warning("staff_login_failed", email=payload.email)
        raise HttpError(401, "Invalid email or password")

    if not user.is_active:
        logger.warning("staff_login_inactive", email=payload.email)
        raise HttpError(401, "Account is disabled")

    if not user.is_staff:
        logger.warning("staff_login_not_staff", email=payload.email)
        raise HttpError(403, "Access denied. Staff account required.")

    login(request, user)
    logger.info("staff_login_success", user_id=user.pk, email=user.email)

    return LoginResponse(
        user=UserResponse(
            id=user.pk,
            email=user.email,
            name=user.name,
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
            is_editor=user.is_editor,
        ),
        message="Login successful",
    )


@router.post("/logout", response=MessageResponse)
def staff_logout(request: HttpRequest) -> MessageResponse:
    if request.user.is_authenticated:
        logger.info("staff_logout", user_id=request.user.pk)
    logout(request)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response=UserResponse)
def get_current_user(request: HttpRequest) -> UserResponse:
    if not request.user.is_authenticated:
        raise HttpError(401, "Not authenticated")

    user = request.user
    return UserResponse(
        id=user.pk,
        email=user.email,
        name=user.name,
        is_staff=user.is_staff,
        is_superuser=user.is_superuser,
        is_editor=user.is_editor,
    )
