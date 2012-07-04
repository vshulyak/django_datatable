
class BaseModelPresenter(object):

    def __init__(self, *args, **kwargs):
        self._cols = args
        self.kwargs = kwargs

    def get_cols(self):
        return self._cols

    def empty(self, obj, context):
        return ''

    def get_column_name(self, col):
        return self._cols[col]