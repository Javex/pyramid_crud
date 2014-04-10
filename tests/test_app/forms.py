from .models import Poll, Choice, DBSession
from pyramid_crud.forms import TabularInLine, CSRFModelForm


class SessionMixin(object):

    @classmethod
    def get_session(cls):
        return DBSession


class ChoiceInline(TabularInLine):
    class Meta:
        model = Choice
    extra = 0

    @classmethod
    def get_session(cls):
        return DBSession


class PollForm(CSRFModelForm):
    class Meta:
        model = Poll
        include = ['pub_date']
    fieldsets = [
        {'title': None, 'fields': ['question']},
        {'title': 'Date information', 'fields': ['pub_date']},
    ]
    inlines = [ChoiceInline]
