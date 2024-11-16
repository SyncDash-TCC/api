"""replace username with email

Revision ID: f83c3588ce24
Revises: 123dd664252e
Create Date: 2024-11-16 22:04:12.996012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f83c3588ce24'
down_revision: Union[str, None] = '123dd664252e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('historic_dashboard', 'data_upload_planilha',
               existing_type=sa.DATE(),
               type_=sa.DateTime(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('historic_dashboard', 'data_upload_planilha',
               existing_type=sa.DateTime(),
               type_=sa.DATE(),
               existing_nullable=False)
    # ### end Alembic commands ###
