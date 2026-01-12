import enum


class TagCategory(enum.Enum):
    CONSTRUCTED = "constructed"
    COMPUTED = "computed"
    VARIANT = "variant"
    ELEMENT = "element"
    COMPANION = "companion"


def tag_category_from_token(token_type: str) -> TagCategory:
    if token_type == "tag constructed":
        return TagCategory.CONSTRUCTED
    elif token_type == "tag computed":
        return TagCategory.COMPUTED
    elif token_type == "tag variant":
        return TagCategory.VARIANT
    elif token_type == "tag element":
        return TagCategory.ELEMENT
    elif token_type == "tag companion":
        return TagCategory.COMPANION
    else:
        raise ValueError(f"Unknown tag category token type: {token_type}")
