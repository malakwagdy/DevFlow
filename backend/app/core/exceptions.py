LOGIN_FAILURE_MESSAGE = "Invalid email or password"


class AppError(Exception):
    """Base error; main.py turns it into a JSON response with `status_code`."""

    status_code: int = 400
    headers: dict[str, str] | None = None

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class EmailAlreadyRegisteredError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("Email already registered")


class InvalidCredentialsError(AppError):
    status_code = 401

    def __init__(self) -> None:
        super().__init__(LOGIN_FAILURE_MESSAGE)


class InactiveUserError(AppError):
    status_code = 403

    def __init__(self) -> None:
        super().__init__("User account is inactive")


class InvalidTokenError(AppError):
    status_code = 401

    def __init__(self) -> None:
        super().__init__("Invalid or expired token")


class NotAuthenticatedError(AppError):
    status_code = 401

    def __init__(self) -> None:
        super().__init__("Not authenticated")


class PermissionDeniedError(AppError):
    status_code = 403

    def __init__(self) -> None:
        super().__init__("You do not have permission to perform this action")


class GitHubNotConfiguredError(AppError):
    status_code = 503

    def __init__(self) -> None:
        super().__init__("GitHub integration is not configured on this server")


class GitHubNotConnectedError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("GitHub account is not connected")


class GitHubReauthorizationRequiredError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__(
            "GitHub access was revoked or has expired. Please reconnect your GitHub account."
        )


class GitHubUnavailableError(AppError):
    status_code = 502

    def __init__(self) -> None:
        super().__init__("GitHub could not be reached. Please try again.")


class RepositoryNotAccessibleError(AppError):
    status_code = 422

    def __init__(self) -> None:
        super().__init__("Repository not found, or DevFlow does not have access to it")


class BranchNotFoundError(AppError):
    status_code = 422

    def __init__(self) -> None:
        super().__init__("Branch not found in this repository")


class ProjectNotFoundError(AppError):
    status_code = 404

    def __init__(self) -> None:
        super().__init__("Project not found")


class ProjectAlreadyExistsError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("You already have a project for this repository")


class EmailVerificationTokenInvalidError(AppError):
    status_code = 400

    def __init__(self) -> None:
        super().__init__("This verification link is invalid or has expired")


class PasswordResetTokenInvalidError(AppError):
    status_code = 400

    def __init__(self) -> None:
        super().__init__("This password reset link is invalid, expired or already used")


class EmailAlreadyVerifiedError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("Email is already verified")


class IncorrectPasswordError(AppError):
    status_code = 403

    def __init__(self) -> None:
        super().__init__("Current password is incorrect")


class CompanyHasOtherMembersError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__(
            "You own a company that has other members. Transfer ownership before "
            "deleting your account."
        )


class TooManyRequestsError(AppError):
    status_code = 429

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Too many attempts. Please try again later.")
        self.headers = {"Retry-After": str(retry_after_seconds)}
