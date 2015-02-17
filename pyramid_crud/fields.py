import wtforms.fields


class MultiCheckboxField(wtforms.fields.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.

    Example for displaying this field:

    .. code-block:: python

        class MyForm(Form):
            items = MultiCheckboxField(choices=[('1', 'Label')]
        form = MyForm()
        for item in form.items:
            str(item)  # the actual field to be displayed, likely in template

    If you don't iterate, it produces an unordered list be default (if ``str``
    is called on ``form.items``, not each item individually).

    And with formdata it might look like this:

    .. code-block:: python

        # Definition same as above
        formdata = MultiDict()
        formdata.add('items', '1')
        form = MyForm(formdata)
        assert form.items.data == ['1']

    As you can see, a list is produces instead of a scalar value which allows
    multiple fields with the same name.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()

    def pre_validate(self, form):
        if not self.data:
            return
        values = list(c[0] for c in self.choices)
        msg = ('One of the selected items does not exist anymore. It has '
               'probably been deleted.')
        for d in self.data:
            if d not in values:
                raise ValueError(self.gettext(msg))


class MultiHiddenField(wtforms.fields.SelectMultipleField):
    """
    A field that represents a list of hidden input fields the same way as
    :class:`.MultiCheckboxField` and
    :class:`wtforms.fields.SelectMultipleField`.
    """
    widget = wtforms.widgets.HiddenInput()
    option_widget = wtforms.widgets.HiddenInput()

    def pre_validate(self, form):
        if not self.data:
            return
        values = list(c[0] for c in self.choices)
        msg = ('One of the selected items does not exist anymore. It has '
               'probably been deleted.')
        for d in self.data:
            if d not in values:
                raise ValueError(self.gettext(msg))


class SelectField(wtforms.fields.SelectField):
    """
    Same as :class:`wtforms.fields.SelectField` with a custom validation
    message and the requirement that ``data`` evaluates to ``True`` (for the
    purpose of having an empty field that is not allowed).
    """

    def pre_validate(self, form):
        for v, _ in self.choices:
            if self.data == v and self.data:
                break
        else:
            raise ValueError(self.gettext('Please select an action to be '
                                          'executed.'))
