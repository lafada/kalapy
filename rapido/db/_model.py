import threading
from types import FunctionType

from rapido.conf import settings
from rapido.utils.imp import import_module

from _errors import *
from _fields import *
from _query import *


__all__ = ['Model', 'get_model', 'get_models']


class ModelCache(object):
    """A class to manage cache of all models.
    """

    def __init__(self):
        self.cache = {}
        self.aliases = {}
        self.loaded = False
        self.lock = threading.RLock()

    def names(self, name):
        """For internal use only. Will return tuple of (package_name, name) from
        the given name. The name will be normalized.
        """
        name = name.lower()
        parts = name.split('.')
        if len(parts) > 1:
            return parts[0], name
        return "", name

    def _populate(self):
        if self.loaded:
            return
        self.lock.acquire()
        try:
            for package in settings.INSTALLED_PACKAGES:
                models = import_module('models', package)
            self.loaded = True
        finally:
            self.lock.release()

    def get_model(self, name):
        """Get the model from the cache of the given name.
        
        >>> db.get_model("base.user")
        
        Args:
            name: name of the model
        """
        self._populate()

        if isinstance(name, ModelType):
            name = name._model_name

        package, name = self.names(name)
        alias = self.aliases.get(name, name)
        return self.cache.setdefault(package, {}).get(alias)

    def get_models(self, package=None):
        """Get the list of all models from the cache. If package if provided
        then only those models belongs to the package.
        
        Args:
            package: name of the package
            
        Returns:
            list of models
        """
        self._populate()
        if package:
            return self.cache.setdefault(package, {}).values()
        result = []
        for models in self.cache.values():
            result.extend(models.values())
        return result

    def register_model(self, cls):
        """Register the provided model class to the cache.
        
        Args:
            cls: the model class
        """
        package, name = self.names(cls._model_name)
        models = self.cache.setdefault(package, {})
        alias = cls.__name__.lower()
        if package:
            alias = '%s.%s' % (package, alias)
        self.aliases[alias] = name
        models[name] = cls


cache = ModelCache()

get_model = cache.get_model
get_models = cache.get_models


class ModelType(type):

    def __new__(cls, name, bases, attrs):

        super_new = super(ModelType, cls).__new__

        parents = [b for b in bases if isinstance(b, ModelType)]
        if not parents:
            # This is not a subclass of Model so do nothing
            return super_new(cls, name, bases, attrs)

        if len(parents) > 1:
            raise DatabaseError("Multiple inheritance is not supported.")

        # always use the last defined base class in the inheritance chain 
        # to maintain linear hierarchy.

        try:
            package_name = '%s.' % attrs['__module__'].split('.')[-2]
        except Exception, e:
            package_name = ''

        model_name = getattr(parents[0], '_model_name', package_name + name).lower()
        parent = cache.get_model(model_name)

        if parent:
            bases = list(bases)
            for i, base in enumerate(bases):
                if isinstance(base, ModelType):
                    bases[i] = parent
            bases = tuple(bases)

        cls = super_new(cls, name, bases, attrs)

        cls._parent = parent
        cls._model_name = model_name
        cls._table_name = model_name.replace('.', '_')

        # overwrite model class in the cache
        cache.register_model(cls)

        cls._values = None
        cls._fields = getattr(parent, '_fields', {})

        for name, attr in attrs.items():

            # prepare fields
            if isinstance(attr, Field):
                if name in cls._fields:
                    raise DuplicateFieldError(
                        "Duplicate field, %s, already defined in parent class." % name)
                cls._fields[name] = attr
                attr.__configure__(cls, name)

            # prepare validators
            if isinstance(attr, FunctionType) and hasattr(attr, '_validates'):

                field = attr._validates
                if isinstance(field, basestring):
                    field = getattr(cls, field, None)

                if not isinstance(field, Field):
                    raise FieldError("Field '%s' is not defined." % attr._validates)

                field._validator = attr

        return cls
    
    def __repr__(cls):
        return "<Model %r: class %s>" % (cls._model_name, cls.__name__)


class Model(object):
    """Model is the super class of all the objects of data entities in
    the database.

    Database tables declared as subclasses of `Model` defines table properties
    as class members of type `Field`. So if you want to publish a story with 
    title, body and date, you would do it like:

    >>> class Story(Model):
    >>>     title = String(size=100, required=True)
    >>>     body = Text()
    >>>     date = DateTime()

    You can extend a model by creating subclasses of that model but you
    can't inherit from more then one models.

    >>> class A(Model):
    >>>     a = String()
    >>> 
    >>> class B(Model):
    >>>     b = String()

    you can extend A like this:

    >>> class C(A):
    >>>     c = String()

    but not like this:

    >>> class C(A, B):
    >>>     c = String()


    Another interesting behavior is that no matter which class it inherits
    from, it always inherits from the last class defined of that base model 
    class. Let's see what it means:

    >>> class D(C):
    >>>     d = String()
    >>>
    >>> class E(C):
    >>>     e = String()

    Here even though `E` is extending `C` it is actually extending `D`, the
    last defined class of `A`. So E will have access to all the methods/members
    of `D` not just from `C`. In other words the inheritance hierarchy will be
    forcefully maintained in linear fashion.

    Also whatever class you use of the hierarchy to instantiate you will
    always get an instance of the last defined class. For example:

    >>> obj = D()

    The `obj` will be a direct instance of `E` other then `D`.

    This way you can easily change the behavior of existing data models
    by simply creating subclasses without modifying existing code.

    Let's see an use case:

    >>> class User(Model):
    >>>     name = String(size=100, required=True)
    >>>     lang = String(size=6, selection=[('en_EN', 'English'), ('fr_FR', 'French')])]
    >>>
    >>>     def do_something(self):
    >>>         ...
    >>>         ...

    Your package is using this class like this:

    >>>
    >>> user = User(**kwargs)
    >>> user.do_something()
    >>> user.put()
    >>> 

    Where `kwargs` are `dict` of form variables coming from an http post request.

    Now if you think that `User` should have one more property `age` but you
    don't want to change your running system by modifying the source code,
    you simply create a subclass of `User` and all the methods/members defined
    in that subclass will be available to the package.

    >>> class UserEx(User):
    >>>     age = Integer(size=3)
    >>> 
    >>>     def do_something(self):
    >>>         super(UserEx, self).do_something()
    >>>         ...
    >>>         ...

    so now if the html form has `age` field, the above code will work without any change
    and still saving `age` value. You can also change the behavior of the base class
    by overriding methods.
    """

    __metaclass__ = ModelType

    _table = None

    def __new__(cls, **kw):

        if cls is Model:
            raise DatabaseError("You can't create instance of Model class")

        klass = cache.get_model(cls)

        return super(Model, cls).__new__(klass)


    def __init__(self, **kw):

        self._key = None
        self._values = {}

        fields = self.fields()
        for field in self.fields().values():
            if field.name in kw:
                value = kw[field.name]
            elif field.default is not None:
                value = field.default
            else:
                continue
            field.__set__(self, value)

    @property
    def key(self):
        """The unique key id for this model instance.

        The property is only available if the instance is already stored in
        the database.
        """
        return self._key

    @property
    def saved(self):
        """Whether the model is saved in database or not.
        """
        return  self._key is not None
    
    def _values_for_db(self):
        """Return values to be stored in database table. For internal use only.
        """
        return dict(self._values)
    
    @classmethod
    def _from_db_values(cls, values):
        obj = cls()
        obj._key = values.pop('id', None)
        obj._values.update(values)
        return obj
        
    def save(self):
        """Writes the instance to the database.

        If the instance is created, a new record will be added to the database
        else if it is loaded from database, the record will be updated.

        Returns:
            The unique key id

        Raises:
            DatabaseError if instance could not be commited.
        """
        from rapido.db.engines import database
        return database.insert_into(self)

    def delete(self):
        """Deletes the instance from the database.
        
        Raises:
            DatabaseError if instance could not be deleted.
        """
        if not self.saved:
            raise DatabaseError("Can't delete, instance doesn't exists.")
        from rapido.db.engines import database
        database.delete_from(self)
        
    @classmethod
    def get(cls, keys):
        """Fetch the instance(s) from the database using the provided id(s).

        If `keys` is a single value it will return an instance else if `keys`
        is a list of `key` then returns list of instances.

        >>> user = User.get(123)
        >>> isinstance(user, User)
        ... True
        >>> users = User.get([123, 456, 789])
        >>> isinstance(users, list):
        ... True

        Args:
            keys: an key or list of keys

        Returns:
            if `keys` is single value it will return and instance of the Model else
            returns list of instances.

        Raises:
            DatabaseError if instances can't be retrieved from the given keys.
        """
        single = False
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
            single = True
        result = cls.all().filter('id in :keys', keys=keys).fetch(len(keys))

        if single:
            return result[0] if result else None
        return result

    @classmethod
    def all(cls):
        """Returns a query object over all instances of this model 
        from the database.

        Returns:
            Query instance that will retrive all instances of this model.
        """
        return Query(cls)

    @classmethod
    def filter(cls, query, **params):
        """Shortcut to `cls.all().filter`

        Args:
            query: the simple query (see `db.Query`)
            params: param values

        Returns:
            Query object
        """
        return cls.all().filter(query, **params)

    @classmethod
    def fields(cls):
        """Return the defined fields.
        """
        return dict(cls._fields)
    
    def __repr__(self):
        return "<Model %r: %s object at %s>" % (self._model_name,
                                          self.__class__.__name__, hex(id(self)))

