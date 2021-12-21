"""empty message

Revision ID: 6318b4edda2c
Revises: 650f87336b31
Create Date: 2021-08-30 18:22:06.131459

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6318b4edda2c"
down_revision = "650f87336b31"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("event_dates", sa.Column("size", sa.Integer(), nullable=True))
    op.add_column(
        "event_dates_version",
        sa.Column("size", sa.Integer(), autoincrement=False, nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("event_dates_version", "size")
    op.drop_column("event_dates", "size")
    op.create_table(
        "spatial_ref_sys",
        sa.Column("srid", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "auth_name", sa.VARCHAR(length=256), autoincrement=False, nullable=True
        ),
        sa.Column("auth_srid", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "srtext", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.Column(
            "proj4text", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.CheckConstraint(
            "(srid > 0) AND (srid <= 998999)", name="spatial_ref_sys_srid_check"
        ),
        sa.PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
    )
    # ### end Alembic commands ###