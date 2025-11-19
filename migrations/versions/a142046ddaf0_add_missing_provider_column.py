"""Add missing provider column

Revision ID: a142046ddaf0
Revises: 
Create Date: 2025-11-19 13:34:32.719349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a142046ddaf0'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add provider column
    op.add_column('users', sa.Column('provider', sa.String(length=20), nullable=True, server_default='local'))
    
    # Add provider_id column
    op.add_column('users', sa.Column('provider_id', sa.String(length=200), nullable=True))


def downgrade():
    # Remove the columns in reverse order
    op.drop_column('users', 'provider_id')
    op.drop_column('users', 'provider')
