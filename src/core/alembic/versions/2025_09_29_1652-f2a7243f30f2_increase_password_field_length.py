"""increase_password_field_length

Revision ID: f2a7243f30f2
Revises: 5bff05224ac3
Create Date: 2025-09-29 16:52:13.946305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a7243f30f2'
down_revision: Union[str, None] = '5bff05224ac3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase password field length to accommodate bcrypt hashes (60 chars)
    op.alter_column('users', 'password',
                   existing_type=sa.VARCHAR(length=50),
                   type_=sa.VARCHAR(length=100),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert password field length
    op.alter_column('users', 'password',
                   existing_type=sa.VARCHAR(length=100),
                   type_=sa.VARCHAR(length=50),
                   existing_nullable=False)
