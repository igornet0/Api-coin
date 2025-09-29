"""add_api_key_limiting_fields

Revision ID: 8c5ae74ea5b1
Revises: 61f923bea103
Create Date: 2025-09-29 17:45:45.018726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c5ae74ea5b1'
down_revision: Union[str, None] = '61f923bea103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new fields to kucoin_api_keys table
    op.add_column('kucoin_api_keys', sa.Column('limit_requests', sa.Integer(), nullable=False, server_default='1000'))
    op.add_column('kucoin_api_keys', sa.Column('requests_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('kucoin_api_keys', sa.Column('timedelta_refresh', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('kucoin_api_keys', sa.Column('next_refresh', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
    
    # Add name and created fields to users table
    op.add_column('users', sa.Column('name', sa.String(length=50), nullable=False, server_default=''))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove fields from kucoin_api_keys table
    op.drop_column('kucoin_api_keys', 'next_refresh')
    op.drop_column('kucoin_api_keys', 'timedelta_refresh')
    op.drop_column('kucoin_api_keys', 'requests_count')
    op.drop_column('kucoin_api_keys', 'limit_requests')
    
    # Remove name and created fields from users table
    op.drop_column('users', 'created')
    op.drop_column('users', 'name')
