# -*- coding: utf-8 -*-

# import escape for custom opportunity widget
try:
    from html import escape
except ImportError:
    from cgi import escape

from wtforms import fields, widgets
from wtforms.compat import text_type
from wtforms.validators import ValidationError

from beacon.models.vendors import Category

class MultiCheckboxField(fields.SelectMultipleField):
    '''Custom multiple select field that displays a list of checkboxes

    We have a custom ``pre_validate`` to handle cases where a
    user has choices from multiple categories.
    the validation to pass.

    Attributes:
        widget: wtforms
            `ListWidget <http://wtforms.readthedocs.org/en/latest/widgets.html#wtforms.widgets.ListWidget>`_
        option_widget: wtforms
            `CheckboxInput <http://wtforms.readthedocs.org/en/latest/widgets.html#wtforms.widgets.CheckboxInput>`_
    '''
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

    def pre_validate(self, form):
        '''Automatically passes

        We override pre-validate to allow the form to use
        dynamically created CHOICES.

        See Also:
            :py:class:`~purchasing.models.front.Category`,
            :py:class:`~purchasing.forms.front.CategoryForm`
        '''
        pass

class DynamicSelectField(fields.SelectField):
    '''Custom dynamic select field
    '''
    def pre_validate(self, form):
        '''Ensure we have at least one Category and they all correctly typed

        See Also:
            * :py:class:`~purchasing.models.front.Category`
        '''
        if len(self.data) == 0:
            raise ValidationError('You must select at least one!')
            return False
        for category in self.data:
            if isinstance(category, Category):
                self.choices.append([category, category])
                continue
            else:
                raise ValidationError('Invalid category!')
                return False
        return True

class HelpTextSelectWidget(widgets.Select):
    '''Custom select field that appends help text
    '''
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        help_block_dict = kwargs.pop('data_help_block', {})
        html = ['<select %s>' % widgets.html_params(name=field.name, **kwargs)]
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(
                val, label, selected, help_block_dict=help_block_dict
            ))
        html.append('</select>')
        return widgets.HTMLString(''.join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = text_type(value)
        help_block = kwargs.pop('help_block_dict', {}).get(value, None)

        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        if help_block is not None:
            options['data-help-block'] = help_block
        return widgets.HTMLString('<option %s>%s</option>' % (widgets.html_params(**options), escape(text_type(label), quote=False)))
