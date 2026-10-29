from app.models.about import Education, Experience, LanguageSkill
from app.models.beyond import BeyondItem
from app.models.bio import Bio, SocialLink
from app.models.media import MediaAsset
from app.models.project import Project
from app.models.user import AdminUser, TokenBlocklist

# Every table whose rows are language variants of the same item.
LANGUAGE_ROW_MODELS = (Bio, Education, Experience, LanguageSkill, Project, BeyondItem)

__all__ = [
    "LANGUAGE_ROW_MODELS",
    "AdminUser",
    "BeyondItem",
    "Bio",
    "Education",
    "Experience",
    "LanguageSkill",
    "MediaAsset",
    "Project",
    "SocialLink",
    "TokenBlocklist",
]
