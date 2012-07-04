from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import simplejson
from django.views.generic.list import BaseListView, ListView
from django.db.models import Q

from django_datatable import exceptions

class JSONResponseMixin(object):

    encoder = DjangoJSONEncoder

    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(simplejson.dumps(content, cls=self.encoder),
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        raise NotImplementedError


FILTERING_ATTRIBUTE_NAME = 'filter'
SORTING_ATTRIBUTE_NAME = 'order_by'

class DatatableJSONListView(JSONResponseMixin, BaseListView):
    """
    A view with datatable-format context serialization
    """
    filtering_enabled = False
    sorting_enabled = False
    per_page_default = 10
    
    def _get_param_or_default(self, param, default):
        return self.request.GET.get(param, default)

    def get_paginate_by(self, queryset):

        length = int(self._get_param_or_default('iDisplayLength',self.per_page_default))
        start = int(self._get_param_or_default('iDisplayStart',0))
        if start == 0:
            page = 1
        else:
            page = start / length + 1
        self.kwargs['page'] = page

        return length

    def get_search_Q(self, col, value):
        """

        """
        col_name = self.datatable_presenter.get_column_name(col)
        field = getattr(self.datatable_presenter,col_name, None)
        if field and getattr(field, FILTERING_ATTRIBUTE_NAME, None):
            return getattr(field, FILTERING_ATTRIBUTE_NAME)(value)
        return Q(**{'%s__icontains' % col_name : value})

    def get_sorting_arg(self, col):
        """

        """
        col_name = self.datatable_presenter.get_column_name(col)
        field = getattr(self.datatable_presenter,col_name, None)
        if field and getattr(field, SORTING_ATTRIBUTE_NAME, None):
            return getattr(field, SORTING_ATTRIBUTE_NAME)
        return col_name

    def apply_sorting(self, queryset, sorting_cols):
        """
        Applies sorting on a given queryset
        """
        return queryset.order_by(*sorting_cols)

    def apply_filter(self, queryset, outputQ):
        """
        Applies filtering on a given queryset
        """
        return queryset.filter(outputQ)

    def sort_queryset(self, queryset):
        """
        Applies sorting if it is actually enabled
        """
        
        iSortingCols =  int(self.request.GET.get('iSortingCols',0))
        asortingCols = []

        if iSortingCols:
            for sortedColIndex in range(0, iSortingCols):
                sortedColID = int(self.request.GET.get('iSortCol_%d' % sortedColIndex,0))
                #make sure the column is sortable
                if self.request.GET.get('bSortable_%d' % sortedColID , 'false')  == 'true':
#                    sortedColName = self.result_fields[sortedColID]
                    sortedColName = self.get_sorting_arg(sortedColID)
                    sortingDirection = self.request.GET.get('sSortDir_%d' % sortedColIndex, 'asc')
                    if sortingDirection == 'desc':
                            sortedColName = '-' + sortedColName
                    asortingCols.append(sortedColName)
        return self.apply_sorting(queryset, asortingCols)


    def filter_queryset(self, queryset):
        """
        Applies filtering if it is actually enabled
        """

        cols = int(self.request.GET.get('iColumns',0))

        #column search
        outputQ = None
        for col in range(0,cols):
            if (self.request.GET.get('sSearch_%d' % col, False) > ''
                    and self.request.GET.get('bSearchable_%d' % col, False) == 'true'):

                q = self.get_search_Q(col, self.request.GET['sSearch_%d' % col])
                
                if q:
                    outputQ = outputQ & q if outputQ else q

        if outputQ:
            queryset = self.apply_filter(queryset, outputQ)
        
        return queryset


    def prepare_queryset(self, queryset):
        """
        Wraps all actions on queryset for easier overriding
        """
        if self.sorting_enabled:
            queryset = self.sort_queryset(queryset)

        if self.filtering_enabled:
            queryset = self.filter_queryset(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = self.prepare_queryset(kwargs['object_list'])
        return super(DatatableJSONListView, self).get_context_data(**kwargs)

    def get_presenter_context(self, object_list):
        return {}

    def get_initial_json_context(self, object_list):
        return {}

    def add_to_json_context(self, object_list, ctx):
        """
        Provides a way to add context content from qset or other data
        """
        return {}

    def convert_context_to_json(self, context):

        data = []
        presenter_ctx = self.get_presenter_context(context['object_list'])

        if hasattr(self, 'datatable_presenter'):
            has = dir(self.datatable_presenter)
        else:
            has = []

        for r in context['object_list']:
            fields = []
            for f in self.datatable_presenter.get_cols():
                # local methods
                if f in has:
                    fields.append(getattr(self.datatable_presenter, f)(r,presenter_ctx))
                else:
                    field = f.split('.')
                    # follows FK
                    if len(field) > 1:
                        if callable(getattr(getattr(r, field[0]),field[1])):
                            fields.append(getattr(getattr(r, field[0]),field[1])())
                        else:
                            fields.append(getattr(getattr(r, field[0]),field[1]))
                    else:
                        try:
                            fields.append(getattr(r, field[0]))
                        except AttributeError:
                            raise exceptions.FieldNotDefined(field[0])

            data.append(fields)

        paginator = context['paginator']

        ctx = self.get_initial_json_context(context['object_list'])
        ctx.update({
            'sEcho':int(self.request.GET.get('sEcho', 0)),
            'iTotalRecords':paginator.count,
            'iTotalDisplayRecords':paginator.count, #not quite the same, but leave it for now
            'aaData':data
        })
        ctx.update(self.add_to_json_context(context['object_list'], ctx))
        return ctx


class DataTableListView(DatatableJSONListView, ListView):
    def render_to_response(self, context):
        if self.request.GET.has_key('json'):
            return DatatableJSONListView.render_to_response(self, context)
        else:
            return ListView.render_to_response(self, context)