from django.contrib.auth.models import User

from django_datatable.views import DataTableListView
from django_datatable.presenter import BaseModelPresenter

class TestPresenter(BaseModelPresenter):

    def username(self, obj, context):
        return obj.username

    def date_joined(self, obj, context):
        return obj.date_joined

    def field_three(self, obj, context):
        return obj.last_name
    field_three.filter = lambda value: Q(**{'last_name__icontains' : value})
    field_three.order_by = 'last_name'

class TestViewOne(DataTableListView):
    template_name = 'datatable/dummy.html'
    datatable_presenter = TestPresenter(
        'username',
        'date_joined',
        'field_three',
    )
    filtering_enabled = True
    sorting_enabled = True
    per_page_default = 5

    def get_queryset(self):
        return User.objects.all()