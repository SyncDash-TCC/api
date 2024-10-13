"""replace username with email

Revision ID: ed6cd87984f0
Revises: 9b73a0d3f688
Create Date: 2024-10-13 00:11:49.553750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed6cd87984f0'
down_revision: Union[str, None] = '9b73a0d3f688'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('panilhas', sa.Column('nome_produto', sa.String(), nullable=False))
    op.add_column('panilhas', sa.Column('categoria_produto', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('panilhas', 'categoria_produto')
    op.drop_column('panilhas', 'nome_produto')
    # ### end Alembic commands ###
