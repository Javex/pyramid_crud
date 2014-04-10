from .forms import PollForm
from .models import DBSession
from pyramid_crud.views import CRUDView


class PollView(CRUDView):
    Form = PollForm
    list_display = ['question', 'pub_date', 'published']
    url_path = '/polls'
    dbsession = DBSession
