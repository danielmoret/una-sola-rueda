"""empty message

Revision ID: c74b15745d7b
Revises: 0dc554ed9ea2
Create Date: 2023-03-08 19:27:11.593243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c74b15745d7b'
down_revision = '0dc554ed9ea2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('number_of_tickets', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('total', sa.Float(precision=10), nullable=False))
        batch_op.drop_column('amount')

    with op.batch_alter_table('talonario', schema=None) as batch_op:
        batch_op.alter_column('price',
               existing_type=sa.REAL(),
               type_=sa.Float(precision=10),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('talonario', schema=None) as batch_op:
        batch_op.alter_column('price',
               existing_type=sa.Float(precision=10),
               type_=sa.REAL(),
               existing_nullable=False)

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount', sa.REAL(), autoincrement=False, nullable=False))
        batch_op.drop_column('total')
        batch_op.drop_column('number_of_tickets')

    # ### end Alembic commands ###