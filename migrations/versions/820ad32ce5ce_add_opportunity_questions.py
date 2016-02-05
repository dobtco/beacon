"""add_opportunity_questions

Revision ID: 820ad32ce5ce
Revises: d43a4431956e
Create Date: 2016-01-28 16:10:07.875893

"""

# revision identifiers, used by Alembic.
revision = '820ad32ce5ce'
down_revision = 'd43a4431956e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('question',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('asked_by_id', sa.Integer(), nullable=True),
    sa.Column('asked_at', sa.DateTime(), nullable=True),
    sa.Column('answer_text', sa.Text(), nullable=True),
    sa.Column('answered_by_id', sa.Integer(), nullable=True),
    sa.Column('answered_at', sa.DateTime(), nullable=True),
    sa.Column('edited', sa.Boolean(), nullable=True),
    sa.Column('edited_at', sa.DateTime(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['answered_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['asked_by_id'], ['vendor.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='created_by_id_fkey', use_alter=True),
    sa.ForeignKeyConstraint(['opportunity_id'], ['opportunity.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name='updated_by_id_fkey', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_id'), 'question', ['id'], unique=False)
    op.add_column(u'opportunity', sa.Column(
        'enable_qa', sa.Boolean(), nullable=False,
        server_default=sa.schema.DefaultClause('true'))
    )
    op.add_column(u'opportunity', sa.Column('qa_end', sa.DateTime(), nullable=True))
    op.add_column(u'opportunity', sa.Column('qa_start', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'opportunity', 'qa_start')
    op.drop_column(u'opportunity', 'qa_end')
    op.drop_column(u'opportunity', 'enable_qa')
    op.drop_index(op.f('ix_question_id'), table_name='question')
    op.drop_table('question')
    ### end Alembic commands ###