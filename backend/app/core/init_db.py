"""
Updated init_db.py - includes PasswordResetToken model

Changes:
- Import PasswordResetToken model
- Model will be auto-created by Base.metadata.create_all()
"""
import logging

from app.core.database import engine, Base, SessionLocal, check_db_connection
from app.core.logging_config import setup_logging
from app.models import User, Clip, Award, Comment
from app.models.award_type import AwardType
from app.models.password_reset_token import PasswordResetToken

logger = logging.getLogger(__name__)


def init_db():
    """
    Creates all tables in the database.

    Now includes PasswordResetToken table.
    """
    logger.info("Checking database connection...")

    if not check_db_connection():
        logger.error("Cannot connect to database!")
        return False

    logger.info("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully!")

    # Note: PasswordResetToken table is now automatically created
    logger.info("PasswordResetToken table created")

    return True


def seed_system_awards():
    """Seed system award types if they don't exist."""
    db = SessionLocal()
    try:
        existing_count = db.query(AwardType).filter(AwardType.is_system_award == True).count()
        if existing_count > 0:
            logger.info(f"System AwardTypes already exist ({existing_count}), skipping seed")
            return

        system_awards = [
            AwardType(
                name="award:epic_clip",
                display_name="Epic Clip",
                description="For epic moment in game",
                lucide_icon="flame",
                color="#FF4500",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:funny",
                display_name="Funny Moment",
                description="For funny situation",
                lucide_icon="laugh",
                color="#FFD700",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:pro_play",
                display_name="Pro Play",
                description="For professional play",
                lucide_icon="star",
                color="#4169E1",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:clutch",
                display_name="Clutch",
                description="For clutch in difficult situation",
                lucide_icon="zap",
                color="#32CD32",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:wtf",
                display_name="WTF Moment",
                description="For totally unexpected situation",
                lucide_icon="eye",
                color="#9370DB",
                is_system_award=True,
                is_personal=False
            )
        ]

        for award_type in system_awards:
            db.add(award_type)
            logger.info(f"Created system AwardType: {award_type.name}")

        db.commit()
        logger.info(f"Seeded {len(system_awards)} system award types")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding AwardTypes: {e}")
    finally:
        db.close()


def create_personal_award_for_user(
        db,
        user_id: int,
        username: str,
        display_name: str = None
) -> AwardType:
    """
    Create personal award for new user.

    Args:
        db: SQLAlchemy session (passed from outside)
        user_id: User ID
        username: Username
        display_name: Display name for user

    Returns:
        AwardType: Created personal award
    """
    try:
        # Check if user already has personal award
        existing = db.query(AwardType).filter(
            AwardType.created_by_user_id == user_id,
            AwardType.is_personal == True
        ).first()

        if existing:
            logger.info(f"User {username} already has personal award: {existing.name}")
            return existing

        # Create personal award
        personal_award = AwardType(
            name=f"award:personal_{username}",
            display_name=f"Award {display_name or username}",
            description=f"Personal award for user {username}",
            lucide_icon="award",
            color="#FF6B9D",
            created_by_user_id=user_id,
            is_system_award=False,
            is_personal=True
        )

        db.add(personal_award)
        db.flush()

        logger.info(f"Created personal award for {username}: {personal_award.name}")

        return personal_award

    except Exception as e:
        logger.error(f"Error creating personal award: {e}")
        raise


def drop_db():
    """
    Drop all tables from database (CAREFUL!).

    Now also drops PasswordResetToken table.
    """
    logger.warning("WARNING: Dropping all tables from database!")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tables dropped")


if __name__ == "__main__":
    setup_logging(log_level="INFO")
    init_db()
