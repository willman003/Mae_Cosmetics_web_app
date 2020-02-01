"""empty message

Revision ID: 12648d81b244
Revises: 
Create Date: 2020-01-31 11:29:58.069195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12648d81b244'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cars',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ten', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cars')
    # ### end Alembic commands ###