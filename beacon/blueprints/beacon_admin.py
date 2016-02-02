# -*- coding: utf-8 -*-

import datetime

from flask import (
    render_template, url_for, Response, stream_with_context,
    redirect, flash, abort, request, current_app, Blueprint
)
from flask_security import current_user, roles_accepted, utils as sec_utils

from beacon.database import db

from beacon.models.opportunities import Opportunity, Vendor, OpportunityDocument
from beacon.models.questions import Question
from beacon.forms.opportunities import OpportunityForm
from beacon.forms.questions import AnswerForm

from beacon.notifications import Notification

blueprint = Blueprint(
    'beacon_admin', __name__, url_prefix='/beacon/admin',
    static_folder='../static', template_folder='../templates'
)

@blueprint.route('/opportunities/new', methods=['GET', 'POST'])
@roles_accepted('staff', 'approver', 'admin')
def new():
    '''Create a new opportunity

    :status 200: Render the opportunity create/edit template
    :status 302: Post data for a new opportunity via the
        :py:class:`~purchasing.forms.front.OpportunityForm`
        and redirect to the edit view of the created opportunity
    '''
    form = OpportunityForm()

    if form.validate_on_submit():
        opportunity_data = form.data_cleanup()
        opportunity = Opportunity.create(
            opportunity_data, current_user,
            form.documents, request.form.get('save_type') == 'publish'
        )
        db.session.add(opportunity)
        db.session.commit()

        opportunity.send_publish_email()
        db.session.commit()
        flash('Opportunity post submitted to OMB!', 'alert-success')
        return redirect(url_for('beacon_admin.edit', opportunity_id=opportunity.id))

    form.display_cleanup()

    return render_template(
        'beacon/admin/opportunity.html', form=form, opportunity=None,
        subcategories=form.get_subcategories(),
        categories=form.get_categories()
    )

@blueprint.route('/opportunities/<int:opportunity_id>', methods=['GET', 'POST'])
@roles_accepted('staff', 'approver', 'admin')
def edit(opportunity_id):
    '''Edit an opportunity

    :status 200: Render the opportunity create/edit template
    :status 302: Post data for the relevant opportunity to edit via the
        :py:class:`~purchasing.forms.front.OpportunityForm`
        and redirect to the edit view of the opportunity
    '''
    opportunity = Opportunity.query.get(opportunity_id)

    if opportunity:

        if opportunity.can_edit(current_user):
            form = OpportunityForm(obj=opportunity)

            if form.validate_on_submit():
                opportunity_data = form.data_cleanup()
                opportunity.update(
                    opportunity_data, current_user,
                    form.documents, request.form.get('save_type') == 'publish'
                )
                opportunity.save()
                opportunity.send_publish_email()
                opportunity.save()
                flash('Opportunity successfully updated!', 'alert-success')

                return redirect(url_for('beacon_admin.edit', opportunity_id=opportunity.id))

            form.display_cleanup(opportunity)

            return render_template(
                'beacon/admin/opportunity.html', form=form,
                opportunity=opportunity,
                subcategories=form.get_subcategories(),
                categories=form.get_categories()
            )

        flash('This opportunity has been locked for editing by OMB.', 'alert-warning')
        return redirect(url_for('front.detail', opportunity_id=opportunity_id))
    abort(404)

@blueprint.route('/opportunities/<int:opportunity_id>/questions')
@roles_accepted('staff', 'approver', 'admin')
def questions(opportunity_id):
    opportunity = Opportunity.query.get(opportunity_id)
    if opportunity:
        if not opportunity.can_edit(current_user):
            sec_utils.do_flash(*sec_utils.get_message('UNAUTHORIZED'))
            return redirect('/')
        answered, unanswered = [], []
        for question in opportunity.questions:
            if question.answer_text:
                answered.append(question)
            else:
                unanswered.append(question)
        return render_template(
            'beacon/admin/questions.html', unanswered=unanswered,
            answered=answered, opportunity=opportunity,
        )
    abort(404)

@blueprint.route('/opportunities/<int:opportunity_id>/questions/<int:question_id>', methods=['GET', 'POST'])
@roles_accepted('staff', 'approver', 'admin')
def answer_question(opportunity_id, question_id):
    question = Question.query.get(question_id)
    if question:
        if not question.opportunity.can_edit(current_user):
            sec_utils.do_flash(*sec_utils.get_message('UNAUTHORIZED'))
            return redirect('/')
        form = AnswerForm(obj=question)
        if form.validate_on_submit():
            answer = {'answer_text': form.answer_text.data}
            if question.answer_text:
                answer['edited'] = True
                answer['edited_at'] = datetime.datetime.utcnow()
                question.update(**answer)
                flash('Answer successfully edited.')
            else:
                answer['answered_at'] = datetime.datetime.utcnow()
                answer['answered_by'] = current_user
                question.update(**answer)
                flash('This question has been answered! The Vendor has been notified and the question and answer are now public.')

                to_email = set([
                    question.opportunity.created_by.email,
                    question.opportunity.contact.email,
                    question.asked_by.email
                ]).difference(set([current_user.email]))

                Notification(
                    to_email=list(to_email),
                    subject='New answer to a questio on Beacon',
                    html_template='beacon/emails/answered_question.html',
                    txt_template='beacon/emails/answered_question.txt',
                    question=question
                ).send(multi=True)

            return redirect(
                url_for('beacon_admin.questions', opportunity_id=opportunity_id)
            )

        return render_template(
            'beacon/admin/answer_question.html', form=form,
            question=question, opportunity_id=opportunity_id
        )
    abort(404)

@blueprint.route('/opportunities/<int:opportunity_id>/questions/<int:question_id>/delete')
@roles_accepted('staff', 'approver', 'admin')
def delete_question(opportunity_id, question_id):
    question = Question.query.get(question_id)
    if question:
        if not question.opportunity.can_edit(current_user):
            sec_utils.do_flash(*sec_utils.get_message('UNAUTHORIZED'))
            return redirect('/')
        question.delete()
        flash('Question successfully deleted', 'alert-info')
        return redirect(url_for('beacon_admin.questions', opportunity_id=opportunity_id))

@blueprint.route('/opportunities/<int:opportunity_id>/document/<int:document_id>/remove')
@roles_accepted('staff', 'approver', 'admin')
def remove_document(opportunity_id, document_id):
    '''Remove a particular opportunity document

    .. seealso::
        :py:class:`~purchasing.models.front.OpportunityForm`

    :status 302: Delete the relevant opportunity document and redirect to
        the edit view for the opportunity whose document was deleted
    '''
    try:
        document = OpportunityDocument.query.get(document_id)
        # TODO: delete the document from S3
        if document:
            current_app.logger.info(
'''BEACON DELETE DOCUMENT: | Opportunity ID: {} | Document: {} | Location: {}'''.format(
                    opportunity_id, document.name, document.href
                )
            )
            document.delete()
            flash('Document successfully deleted', 'alert-success')
        else:
            flash("That document doesn't exist!", 'alert-danger')
    except Exception, e:
        current_app.logger.error('Document delete error: {}'.format(str(e)))
        flash('Something went wrong: {}'.format(e.message), 'alert-danger')
    return redirect(url_for('beacon_admin.edit', opportunity_id=opportunity_id))

@blueprint.route('/opportunities/<int:opportunity_id>/publish')
@roles_accepted('approver', 'admin')
def publish(opportunity_id):
    '''Publish an opportunity

    If an :py:class:`~purchasing.models.front.Opportunity` has
    been created by a non-admin, it will be stuck in a "pending" state
    until it has been approved by an beacon_admin. This view function handles
    the publication event for a specific
    :py:class:`~purchasing.models.front.Opportunity`

    :status 200: Publish the relevant opportunity and send the relevant
        publication emails
    :status 404: :py:class:`~purchasing.models.front.Opportunity`
        not found
    '''
    opportunity = db.session.query(Opportunity).filter(
        Opportunity.id == opportunity_id
    ).first()

    if opportunity:
        to_email = opportunity.created_by.email

        opportunity.is_public = True
        db.session.commit()

        opportunity.send_publish_email()

        Notification(
            to_email=[to_email],
            subject='OMB approved your opportunity post!',
            html_template='beacon/emails/staff_postapproved.html',
            txt_template='beacon/emails/staff_postapproved.txt',
            opportunity=opportunity
        ).send(multi=True)

        opportunity.save()

        current_app.logger.info(
            '''BEACON APPROVED: ID: {} | Title: {} | Publish Date: {} | Submission Start Date: {} | Submission End Date: {} '''.format(
                opportunity.id, opportunity.title.encode('ascii', 'ignore'), str(opportunity.planned_publish),
                str(opportunity.planned_submission_start), str(opportunity.planned_submission_end)
            )
        )

        flash('Opportunity successfully published!', 'alert-success')
        return redirect(url_for('beacon_admin.pending'))
    abort(404)

@blueprint.route('/opportunities/pending')
@roles_accepted('staff', 'approver', 'admin')
def pending():
    '''View which contracts are currently pending approval

    :status 200: Render the pending template
    '''
    pending = Opportunity.query.filter(
        Opportunity.is_public == False,
        Opportunity.planned_submission_end >= datetime.date.today(),
        Opportunity.is_archived == False
    ).all()

    approved = Opportunity.query.filter(
        Opportunity.planned_publish > datetime.date.today(),
        Opportunity.is_public == True,
        Opportunity.planned_submission_end >= datetime.date.today(),
        Opportunity.is_archived == False
    ).all()

    current_app.logger.info('BEACON PENDING VIEW')

    return render_template(
        'beacon/admin/pending.html', pending=pending,
        approved=approved, current_user=current_user
    )

@blueprint.route('/opportunities/<int:opportunity_id>/archive')
@roles_accepted('approver', 'admin')
def archive(opportunity_id):
    '''Archives opportunities in pending view

    :status 302: Archive the :py:class:`~purchasing.models.front.Opportunity`
        and redirect to the pending view
    :status 404: :py:class:`~purchasing.models.front.Opportunity`
        not found
    '''
    opportunity = Opportunity.query.get(opportunity_id)
    if opportunity:
        opportunity.is_archived = True
        db.session.commit()

        current_app.logger.info(
'''BEACON ARCHIVED: ID: {} | Title: {} | Publish Date: {} | Submission Start Date: {} | Submission End Date: {} '''.format(
                opportunity.id, opportunity.title.encode('ascii', 'ignore'), str(opportunity.planned_publish),
                str(opportunity.planned_submission_start), str(opportunity.planned_submission_end)
            )
        )

        flash('Opportunity successfully archived!', 'alert-success')

        return redirect(url_for('beacon_admin.pending'))

    abort(404)

@blueprint.route('/signups')
@roles_accepted('staff', 'approver', 'admin')
def signups():
    '''Basic dashboard view for category-level signups

    :status 200: Download a tab-separated file of all vendor signups
    '''
    def stream():
        # yield the title columns
        yield 'first_name\tlast_name\tbusiness_name\temail\tphone_number\t' +\
            'minority_owned\twoman_owned\tveteran_owned\t' +\
            'disadvantaged_owned\tcategories\topportunities\n'

        vendors = Vendor.query.all()
        for vendor in vendors:
            row = vendor.build_downloadable_row()
            yield '\t'.join([str(i) for i in row]) + '\n'

    current_app.logger.info('BEACON VENDOR CSV DOWNLOAD')

    resp = Response(
        stream_with_context(stream()),
        headers={
            "Content-Disposition": "attachment; filename=vendors-{}.tsv".format(datetime.date.today())
        },
        mimetype='text/tsv'
    )

    return resp
