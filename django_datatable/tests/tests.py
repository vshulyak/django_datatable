import textwrap
from random import Random

from django.utils import simplejson

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from django_datatable.tests.views import TestViewOne

class DatatableViewCase(TestCase):

    dt_js_request = textwrap.dedent("""
        /datatable/?json
        &sEcho=1
        &iColumns=4
        &sColumns=
        &iDisplayStart=%(display_start)d
        &iDisplayLength=%(display_length)d
        &sSearch=
        &bRegex=false
        &sSearch_0=%(search_0)s
        &bRegex_0=false
        &bSearchable_0=true
        &sSearch_1=
        &bRegex_1=false
        &bSearchable_1=true
        &sSearch_2=
        &bRegex_2=false
        &bSearchable_2=true
        &sSearch_3=
        &bRegex_3=false
        &bSearchable_3=true
        &iSortingCols=1
        &iSortCol_0=%(sort_col)d
        &sSortDir_0=asc
        &bSortable_0=true
        &bSortable_1=true
        &bSortable_2=true
        &bSortable_3=true""").replace('\n','')

    def setUp(self):
        self.dt_list_view = TestViewOne.as_view()
        self.factory = RequestFactory()

        get_random_name = lambda: ''.join(Random().sample('qwertyuiopasdfghjklzxcvbnm', 10))

        for idx in xrange(0,5):
            User.objects.create(username='user_%d' % idx,
                first_name=get_random_name(), last_name=get_random_name())

    def test_non_json_template_response(self):
        request = self.factory.get('/datatable/')
        r = self.dt_list_view(request)

        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.template_name[0], TestViewOne.template_name)

    def test_json_response(self):
        request = self.factory.get('/datatable/?json')
        r = self.dt_list_view(request)

        self.assertEquals(r.status_code, 200)

    def test_dt_request(self):
        request = self.factory.get(self.__make_dt_request_line(
            display_start = 0,
            display_length = 10,
            sort_col = 0,
            search_0 = ''
        ))
        r = self.dt_list_view(request)
        self.assertEquals(r.status_code, 200)

        json = self.__parse_dt_response(r.content)
        self.assertEquals(len(json["aaData"]), User.objects.count())

    def test_pagination(self):
        #TODO: todo!
        pass

    def test_ordering(self):
        request = self.factory.get(self.__make_dt_request_line(
            display_start = 0,
            display_length = 10,
            sort_col = 2,
            search_0 = ''
        ))
        r = self.dt_list_view(request)
        self.assertEquals(r.status_code, 200)

        json = self.__parse_dt_response(r.content)

        for u, qset_user in zip(json["aaData"], User.objects.order_by('last_name')):
            self.assertEquals(u[0], qset_user.username)
    
    def test_filter(self):

        FILTER_EXP = 'user_3'

        request = self.factory.get(self.__make_dt_request_line(
            display_start = 0,
            display_length = 10,
            sort_col = 2,
            search_0 = '_3'
        ))
        r = self.dt_list_view(request)
        self.assertEquals(r.status_code, 200)

        json = self.__parse_dt_response(r.content)

        self.assertEquals(len(json["aaData"]), len(User.objects.filter(username=FILTER_EXP)))


    def __make_dt_request_line(self, **kwargs):
        return self.dt_js_request % kwargs

    def __parse_dt_response(self, response):
        return simplejson.loads(response)