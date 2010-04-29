
from _fields import Field
from _model import get_model, get_models


__all__ = ('ManyToOne', 'OneToMany', 'ManyToMany')


class ManyToOne(Field):

    _data_type = "integer"

    def __init__(self, reference, cascade=None, **kw):
        super(ManyToOne, self).__init__(**kw)
        self._reference = reference
        self.cascade = cascade

    @property
    def reference(self):
        return get_model(self._reference)


class OneToMany(Field):
    pass


class ManyToMany(Field):
    pass

