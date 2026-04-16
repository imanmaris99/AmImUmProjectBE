from fastapi import HTTPException, status

from app.dtos.error_response_dtos import ErrorResponseDto


def normalize_optional_filter(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    return normalized or None


def validate_allowed_filter(
    value: str | None,
    allowed_values: set[str],
    field_name: str,
) -> str | None:
    normalized = normalize_optional_filter(value)
    if normalized is None:
        return None

    if normalized not in allowed_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=f"{field_name} filter '{value}' is not allowed."
            ).dict()
        )

    return normalized
