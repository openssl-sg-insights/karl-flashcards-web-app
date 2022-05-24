"""remove unnecessary index

Revision ID: 5226e60d1987
Revises: 957c6698b8e2
Create Date: 2022-05-24 18:46:10.123696

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5226e60d1987'
down_revision = '957c6698b8e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_deck_title', table_name='deck')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_deck_title', 'deck', ['title'], unique=False)
    # ### end Alembic commands ###
