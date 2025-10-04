"""
Helper script to run database migrations
Usage:
    python run_migration.py        # Run migration
    python run_migration.py --down # Rollback migration
"""
import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.award_type import AwardType
from sqlalchemy import text, inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_if_migrated():
    """Check if the new columns exist in award_types table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('award_types')]

    has_lucide = 'lucide_icon' in columns
    has_personal = 'is_personal' in columns

    return has_lucide and has_personal


def manual_migration():
    """
    Manually run the migration if Alembic is not set up
    This is a simplified version that works without Alembic
    """
    logger.info("Starting manual migration...")

    db = SessionLocal()

    try:
        # Check if already migrated
        if check_if_migrated():
            logger.info("Database already migrated!")
            return

        logger.info("Running migration queries...")

        # 1. Add new columns to award_types
        logger.info("Adding new columns to award_types...")
        db.execute(text("ALTER TABLE award_types ADD COLUMN lucide_icon VARCHAR(100)"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN custom_icon_path VARCHAR(500)"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN created_by_user_id INTEGER"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN is_system_award BOOLEAN DEFAULT 0 NOT NULL"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN is_personal BOOLEAN DEFAULT 0 NOT NULL"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"))
        db.execute(text("ALTER TABLE award_types ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"))

        # 2. Add is_admin to users
        logger.info("Adding is_admin column to users...")
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))

        db.commit()

        # 3. Update existing awards with lucide icons
        logger.info("Migrating emoji icons to lucide icons...")

        icon_mapping = {
            '🔥': 'flame',
            '😂': 'laugh',
            '⭐': 'star',
            '💪': 'zap',
            '🤯': 'eye',
            '🏆': 'trophy'
        }

        award_types = db.query(AwardType).all()
        for award_type in award_types:
            # Map old icon to lucide
            old_icon = getattr(award_type, 'icon', '🏆')
            lucide_icon = icon_mapping.get(old_icon, 'trophy')

            award_type.lucide_icon = lucide_icon
            award_type.is_system_award = True

        db.commit()
        logger.info(f"Updated {len(award_types)} system awards")

        # 4. Create personal awards for existing users
        logger.info("Creating personal awards for existing users...")

        users = db.query(User).all()
        personal_awards_created = 0

        for user in users:
            # Check if already has personal award
            existing = db.query(AwardType).filter(
                AwardType.created_by_user_id == user.id,
                AwardType.is_personal == True
            ).first()

            if existing:
                continue

            display_name = user.full_name if user.full_name else user.username

            personal_award = AwardType(
                name=f"award:personal_{user.username}",
                display_name=f"Nagroda {display_name}",
                description=f"Osobista nagroda użytkownika {display_name}",
                lucide_icon="award",
                color="#FF6B9D",
                created_by_user_id=user.id,
                is_system_award=False,
                is_personal=True
            )

            db.add(personal_award)
            personal_awards_created += 1
            logger.info(f"  ✓ Created personal award for {user.username}")

        db.commit()
        logger.info(f"Created {personal_awards_created} personal awards")

        # 5. Drop old icon column (SQLite limitation - need to recreate table)
        logger.info("Note: Old 'icon' column still exists (SQLite limitation)")
        logger.info("It can be safely ignored or manually removed if needed")

        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def rollback_migration():
    """Rollback the migration (removes personal awards and new columns)"""
    logger.warning("⚠️  Rolling back migration...")

    db = SessionLocal()

    try:
        # Check if migrated
        if not check_if_migrated():
            logger.info("Database not migrated, nothing to rollback")
            return

        # 1. Remove personal awards
        logger.info("Removing personal awards...")
        personal_awards = db.query(AwardType).filter(AwardType.is_personal == True).all()
        for award in personal_awards:
            db.delete(award)
        db.commit()
        logger.info(f"Removed {len(personal_awards)} personal awards")

        # 2. Note about columns
        logger.warning("Note: Due to SQLite limitations, columns cannot be easily dropped")
        logger.warning("The new columns will remain but will not be used")
        logger.warning("For clean rollback, restore database from backup")

        logger.info("✅ Rollback completed")

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Run database migration")
    parser.add_argument(
        "--down",
        action="store_true",
        help="Rollback the migration"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check migration status"
    )

    args = parser.parse_args()

    if args.check:
        migrated = check_if_migrated()
        if migrated:
            logger.info("✅ Database is migrated to new schema")
        else:
            logger.info("❌ Database needs migration")
        return

    if args.down:
        rollback_migration()
    else:
        manual_migration()


if __name__ == "__main__":
    main()
