"""empty message

Revision ID: 79b0ee1dea0e
Revises: 93086455fc92
Create Date: 2021-06-21 18:35:18.785633

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "79b0ee1dea0e"
down_revision = "93086455fc92"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "album_items",
        sa.Column(
            "type", sa.Enum("image", "video", name="album_item_type"), nullable=True
        ),
    )
    op.drop_column("album_items", "album_item_type")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "album_items",
        sa.Column(
            "album_item_type",
            postgresql.ENUM("image", "video", name="album_item_type"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("album_items", "type")
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
