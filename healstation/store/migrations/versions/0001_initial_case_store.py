"""initial case store

Revision ID: 0001
Revises: (none)
Create Date: 2026-10-10 16:31:13.043372
"""

import sqlalchemy as sa
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'case_keys',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('wrapped_key', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'cases',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('pseudonym', sa.String(length=16), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('language', sa.String(length=8), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('sex', sa.String(length=16), nullable=True),
        sa.Column('area_enc', sa.LargeBinary(), nullable=True),
        sa.Column('abha_enc', sa.LargeBinary(), nullable=True),
        sa.Column('created_by', sa.String(length=32), nullable=True),
        sa.Column('facility_id', sa.String(length=64), nullable=True),
        sa.Column('key_id', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('erased_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['key_id'], ['case_keys.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pseudonym'),
    )
    with op.batch_alter_table('cases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cases_expires_at'), ['expires_at'], unique=False)

    op.create_table(
        'assessments',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=False),
        sa.Column('job_id', sa.String(length=32), nullable=True),
        sa.Column('inputs_digest', sa.String(length=64), nullable=True),
        sa.Column('fast_path_enc', sa.LargeBinary(), nullable=True),
        sa.Column('result_enc', sa.LargeBinary(), nullable=True),
        sa.Column('urgency', sa.String(length=16), nullable=True),
        sa.Column('sources_json', sa.Text(), nullable=True),
        sa.Column('versions_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('assessments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessments_case_id'), ['case_id'], unique=False)

    op.create_table(
        'attachments',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('purpose', sa.String(length=16), nullable=False),
        sa.Column('stage', sa.String(length=16), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('reason_code', sa.String(length=40), nullable=True),
        sa.Column('detected_type', sa.String(length=64), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('content_digest', sa.String(length=64), nullable=True),
        sa.Column('original_name_enc', sa.LargeBinary(), nullable=True),
        sa.Column('summary_enc', sa.LargeBinary(), nullable=True),
        sa.Column('raw_blob_id', sa.String(length=32), nullable=True),
        sa.Column('job_id', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.create_index('ix_attachments_case_digest', ['case_id', 'content_digest'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_case_id'), ['case_id'], unique=False)

    op.create_table(
        'idempotency_keys',
        sa.Column('scope', sa.String(length=128), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_enc', sa.LargeBinary(), nullable=True),
        sa.Column('response_plain', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('scope', 'key'),
    )
    with op.batch_alter_table('idempotency_keys', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_idempotency_keys_created_at'), ['created_at'], unique=False)

    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('resource', sa.String(length=16), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=True),
        sa.Column('ref_id', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('stage', sa.String(length=32), nullable=True),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('timeout_s', sa.Float(), nullable=False),
        sa.Column('deadline_at', sa.DateTime(), nullable=True),
        sa.Column('error_code', sa.String(length=40), nullable=True),
        sa.Column('payload_enc', sa.LargeBinary(), nullable=True),
        sa.Column('result_enc', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_jobs_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_jobs_status'), ['status'], unique=False)

    op.create_table(
        'visits',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('visits', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_visits_case_id'), ['case_id'], unique=False)

    op.create_table(
        'derivatives',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('attachment_id', sa.String(length=32), nullable=False),
        sa.Column('case_id', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('content_enc', sa.LargeBinary(), nullable=True),
        sa.Column('blob_id', sa.String(length=32), nullable=True),
        sa.Column('model_version', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('derivatives', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_derivatives_attachment_id'), ['attachment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_derivatives_case_id'), ['case_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('derivatives', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_derivatives_case_id'))
        batch_op.drop_index(batch_op.f('ix_derivatives_attachment_id'))

    op.drop_table('derivatives')
    with op.batch_alter_table('visits', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_visits_case_id'))

    op.drop_table('visits')
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_jobs_status'))
        batch_op.drop_index(batch_op.f('ix_jobs_case_id'))

    op.drop_table('jobs')
    with op.batch_alter_table('idempotency_keys', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_idempotency_keys_created_at'))

    op.drop_table('idempotency_keys')
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_attachments_case_id'))
        batch_op.drop_index('ix_attachments_case_digest')

    op.drop_table('attachments')
    with op.batch_alter_table('assessments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessments_case_id'))

    op.drop_table('assessments')
    with op.batch_alter_table('cases', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_cases_expires_at'))

    op.drop_table('cases')
    op.drop_table('case_keys')
