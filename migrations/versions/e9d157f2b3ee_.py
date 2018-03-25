"""empty message

Revision ID: e9d157f2b3ee
Revises: a8a95b895776
Create Date: 2018-03-22 21:56:31.134377

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9d157f2b3ee'
down_revision = 'a8a95b895776'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orderitems', 'shipped_count')
    op.add_column('shipments', sa.Column('buyer_id', sa.Integer(), nullable=True))
    op.drop_constraint('shipments_customer_id_fkey', 'shipments', type_='foreignkey')
    op.create_foreign_key(None, 'shipments', 'customers', ['buyer_id'], ['id'])
    op.drop_column('shipments', 'customer_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shipments', sa.Column('customer_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'shipments', type_='foreignkey')
    op.create_foreign_key('shipments_customer_id_fkey', 'shipments', 'customers', ['customer_id'], ['id'])
    op.drop_column('shipments', 'buyer_id')
    op.add_column('orderitems', sa.Column('shipped_count', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
