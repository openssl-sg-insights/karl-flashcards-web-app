"""remove unnecessary columns is_test and studyset deck_id

Revision ID: 139df0683d97
Revises: 61dba6b62053
Create Date: 2022-05-16 01:35:10.802805

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '139df0683d97'
down_revision = '61dba6b62053'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_deck_is_test', table_name='deck')
    op.drop_column('deck', 'is_test')
    op.drop_column('fact', 'test_mode')
    op.drop_index('ix_studyset_deck_id', table_name='studyset')
    op.drop_constraint('studyset_deck_id_fkey', 'studyset', type_='foreignkey')
    op.drop_column('studyset', 'deck_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('studyset', sa.Column('deck_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('studyset_deck_id_fkey', 'studyset', 'deck', ['deck_id'], ['id'])
    op.create_index('ix_studyset_deck_id', 'studyset', ['deck_id'], unique=False)
    op.add_column('fact', sa.Column('test_mode', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False,
                                    nullable=False))
    op.add_column('deck', sa.Column('is_test', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False,
                                    nullable=False))
    op.create_index('ix_deck_is_test', 'deck', ['is_test'], unique=True)
    # ### end Alembic commands ###
