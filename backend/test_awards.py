"""
Testy dla systemu nagród
"""
import pytest

from app.models.award_type import AwardType
from app.models.user import User


def test_user_can_give_system_award(db_session):
    """Test: każdy user może przyznać systemową nagrodę"""
    user = User(username="test", is_admin=False)
    award_type = AwardType(
        name="award:test",
        display_name="Test",
        is_system_award=True,
        is_personal=False
    )

    assert user.can_give_award(award_type) == True


def test_user_can_give_own_personal_award(db_session):
    """Test: user może przyznać swoją osobistą nagrodę"""
    user = User(id=1, username="test", is_admin=False)
    award_type = AwardType(
        name="award:personal_test",
        display_name="Personal",
        is_personal=True,
        created_by_user_id=1
    )

    assert user.can_give_award(award_type) == True


def test_user_cannot_give_others_personal_award(db_session):
    """Test: user NIE może przyznać cudzej osobistej nagrody"""
    user = User(id=1, username="test", is_admin=False)
    award_type = AwardType(
        name="award:personal_other",
        display_name="Other Personal",
        is_personal=True,
        created_by_user_id=2  # Inny user
    )

    assert user.can_give_award(award_type) == False


def test_admin_can_give_any_award(db_session):
    """Test: admin może przyznać każdą nagrodę"""
    admin = User(id=1, username="admin", is_admin=True)

    # Osobista nagroda innego usera
    personal_award = AwardType(
        name="award:personal_other",
        display_name="Other Personal",
        is_personal=True,
        created_by_user_id=999
    )

    assert admin.can_give_award(personal_award) == True


def test_user_can_give_custom_public_award(db_session):
    """Test: każdy może przyznać custom publiczną nagrodę"""
    user = User(id=1, username="test", is_admin=False)
    award_type = AwardType(
        name="award:custom_public",
        display_name="Custom Public",
        is_personal=False,
        is_system_award=False,
        created_by_user_id=999  # Inny user stworzył
    )

    assert user.can_give_award(award_type) == True
