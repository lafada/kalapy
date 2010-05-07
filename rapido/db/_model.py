import threading
from types import FunctionType

from rapido.conf import settings
from rapido.utils.implib import import_module
from rapido.utils.containers import OrderedDict

from _errors import *
from _fields import *
from _query import *


__all__ = ['Model', 'get_model', 'get_models']


class ModelCache(object):
    """A class to manage cache of all models.
    """

    # Use the Borg pattern to share state between all instances. Details at
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    __shared_state = dict(
            cache = OrderedDict(),
            aliases = {},
            loaded = False,
            resolved = False,
            handled = [],
            lock = threading.RLock(),
        )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def names(self, model_name, package_name=None):
        """For internal use only. Will return tuple of (package_name, name) from
        the given model_name. The name will be normalized.
        """
        name = model_name.lower()
        parts = name.split('.')
        if len(parts) > 1:
            return parts[0], name
        if package_name:
            return package_name, '%s.%s' % (package_name, name)
        return "", name

    def _populate(self):
        """Populate the cache with defined models in all INSTALLED_PACKAGES.
        """
        if self.loaded:
            return
        self.lock.acquire()
        try:
            for package in settings.INSTALLED_PACKAGES:
                if package in self.handled: # deal with recursive import
                    continue
                self.handled.append(package)
                models = import_module('models', package)
            self.loaded = True
            self._resolve_references()
        finally:
            self.lock.release()

    def _resolve_references(self):
        """Prepare all reference fields for the registered models.
        """

        if self.resolved:
            return

        from _reference import IRelation, ManyToOne

        for model in self.get_models():
            ref_models = model._meta.ref_models
            fields = model._meta.fields.items() + model._meta.virtual_fields.items()
            for name, field in fields:
                if not isinstance(field, IRelation):
                    continue
                field.prepare(model)
                if isinstance(field, ManyToOne) and \
                        field.reference not in ref_models:
                    if model in field.reference._meta.ref_models:
                        raise FieldError("Recursive dependency, field %r in '%s.%s'" % (
                            field.name, model.__module__, model.__name__))
                    ref_models.append(field.reference)
        self.resolved = True

    def get_model(self, model_name, package_name=None):
        """Get the model from the cache of the given name resolving with the
        provided package_name if the name is not fully qualified name.
        
        >>> db.get_model('base.user')
        >>> db.get_model('User', 'base')

        Args:
            model_name: name of the model
            package_name: package name
        """
        return self._get_model(model_name, package_name=package_name, seed=True)

    def _get_model(self, model_name, package_name=None, seed=False):
        if seed:
            self._populate()

        if isinstance(model_name, ModelType):
            model_name = model_name._meta.name

        package, name = self.names(model_name, package_name)
        alias = self.aliases.get(name, name)
        try:
            return self.cache.get(package, {})[alias]
        except KeyError:
            if not package: # try to resolve package_name
                import inspect
                frame = inspect.currentframe().f_back.f_back
                try:
                    package_name = frame.f_globals.get('__package__').split('.')[0]
                    return self._get_model(model_name, package_name)
                except:
                    pass
                finally:
                    del frame
            raise KeyError('No such model %r' % model_name)


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
            return self.cache.get(package, {}).values()
        result = []
        for models in self.cache.values():
            result.extend(models.values())
        return result

    def register_model(self, cls):
        """Register the provided model class to the cache.
        
        Args:
            cls: the model class
        """
        package, name = cls._meta.package, cls._meta.name
        models = self.cache.setdefault(package, OrderedDict())
        alias = cls.__name__.lower()
        if package:
            alias = '%s.%s' % (package, alias)
        self.aliases[alias] = name
        models[name] = cls


cache = ModelCache()

get_model = cache.get_model
get_models = cache.get_models


class Options(object):

    def __init__(self):
        self.package = None
        self.name = None
        self.table = None
        self.fields = OrderedDict()
        self.virtual_fields = OrderedDict()
        self.ref_models = []
        self.unique = []

    @property
    def model(self):
        return get_model(self.name)

    def prepare(self):

        self.fields._keys.sort(
                lambda x, y: cmp(
                    self.fields[x]._serial,
                    self.fields[y]._serial))

        self.virtual_fields._keys.sort(
                lambda x, y: cmp(
                    self.virtual_fields[x]._serial,
                    self.virtual_fields[y]._serial))


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

        if '_meta' in attrs:
            raise AttributeError("'_meta' is reserved for internal use.")

        meta = getattr(parents[0], '_meta', None) or Options()

        if meta.name is None:
            try:
                meta.package = attrs['__module__'].split('.')[-2]
                meta.name = meta.package + '.' + name.lower()
            except:
                meta.package = ''
                meta.name = name.lower()
            meta.table = meta.name.replace('.', '_')

        try:
            parent = cache._get_model(meta.name)
        except KeyError:
            parent = None

        if parent:
            bases = list(bases)
            for i, base in enumerate(bases):
                if isinstance(base, ModelType):
                    bases[i] = parent
            bases = tuple(bases)

        cls = super_new(cls, name, bases, {
            '_meta': meta,
            '__module__': attrs.pop('__module__')})

        # create primary key field if it is root model
        if not parent:
            cls.add_field(AutoKey())

        # overwrite model class in the cache
        cache.register_model(cls)

        cls._values = None

        for name, attr in attrs.items():
            if isinstance(attr, Field):
                cls.add_field(attr, name)
            else:
                setattr(cls, name, attr)

        # loop again so that every attributes are set
        for name, attr in attrs.items():

            # prepare unique constraints
            if isinstance(attr, Field) and hasattr(attr, '_unique_with'):
                meta.unique.append(attr._unique_with[:])
                del attr._unique_with

            # prepare validators
            if isinstance(attr, FunctionType) and hasattr(attr, '_validates'):

                field = attr._validates
                if isinstance(field, basestring):
                    field = getattr(cls, field, None)

                if not isinstance(field, Field):
                    raise FieldError("Field '%s' is not defined." % attr._validates)

                # use bound method
                field._validator = getattr(cls, name)

        meta.prepare()

        return cls

    def add_field(cls, field, name=None):
        
        name = name or field.name

        if not name:
            raise ValueError('Field has no name')

        if hasattr(cls, name):
            raise DuplicateFieldError('Field %r already defined in model %r' % (name, cls.__name__))

        setattr(cls, name, field)

        if getattr(field, 'is_virtual', None):
            cls._meta.virtual_fields[name] = field
        else:
            cls._meta.fields[name] = field

        field.__configure__(cls, name)
    
    def __repr__(cls):
        return "<Model %r: class %s>" % (cls._meta.name, cls.__name__)


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


    def __new__(cls, **kw):
        if cls is Model:
            raise DatabaseError("You can't create instance of Model class")

        klass = cache.get_model(cls)
        return super(Model, cls).__new__(klass)

    def __init__(self, **kw):
        """Create a new instance of this model.

        Instanciate a model, initialize it's properties and call save() to save
        the instance in database.

        >>> u = User()
        >>> u.name = "Some"
        >>> u.save()

        Properties can also be initialized by providing keyword arguments to the
        model constructor.

        >>> u = User(name="some")
        >>> u.save()
        
        Args:
            **kw: keyword arguments mapping to instance properties.
        """
        self._key = None
        self._values = {}
        self._dirty = True

        for field in self.fields().values():
            if field.name in kw:
                value = kw[field.name]
            elif field.default is not None:
                value = field.default
            else:
                continue
            field.__set__(self, value)

    @property
    def saved(self):
        """Whether the model is saved in database or not.
        """
        return  self._key is not None

    @property
    def is_dirty(self):
        """Check if the instance is dirty. An instance is dirty if it's 
        properties are changed since it is saved last time.

        Returns:
            True if dirty, else False
        """
        return self._dirty
    
    def _values_for_db(self):
        """Return values to be stored in database table. For internal use only.
        """
        values = {}
        fields = self.fields()
        for name, field in fields.items():
            #if k in self._values:
            #    values[k] = fields[k].python_to_database(self._values[k])
            if field.is_dirty:
                values[name] = field.python_to_database(self._values[name])

        return values
    
    @classmethod
    def _from_db_values(cls, values):
        """Create an instance of this model which properties initialized with
        the given values. For internal use only.

        Args:
            values: mapping of name, value to instance properties

        Returns:
            an instance of this Model
        """
        values = dict(values)

        obj = cls()
        obj._key = values.pop('key', None)

        fields = obj.fields()
        for k, v in values.items():
            values[k] = fields[k].database_to_python(v)

        obj._values.update(values)
        obj._dirty = False
        return obj

    def _get_related(self):
        """Get the list of all related model instances associated with this
        model instance. Used to get all dirty instances of related model
        instances referenced by ManyToOne and OneToOne properties.
        
        For internal use only.

        Returns:
            list of related model instances
        """
        from _reference import IRelation

        related = []
        for name, field in self._meta.fields.items():
            if isinstance(field, IRelation) and field.name in self._values:
                value = self._values[field.name]
                if isinstance(value, Model) and value.is_dirty:
                    related.append(val)
        return related
        
    def save(self):
        """Writes the instance to the database.

        If the instance is created, a new record will be added to the database
        else if it is loaded from database, the record will be updated.

        It also saves all dirty instances of related model instances referenced
        by many-to-one and one-to-many properties.

        Returns:
            The unique key id

        Raises:
            DatabaseError if instance could not be commited.
        """
        if self.saved and not self.is_dirty:
            return self.key

        from rapido.db.engines import database

        [o.save() for o in self._get_related()]

        if self.saved:
            key = database.update_table(self)
        key = database.insert_into(self)
        self._dirty = False

        #TODO: use signal to inform all fields
        for field in self.fields().values():
            field._dirty = False

        return key

    def delete(self):
        """Deletes the instance from the database.
        
        Raises:
            DatabaseError if instance could not be deleted.
        """
        if not self.saved:
            raise DatabaseError("Can't delete, instance doesn't exists.")
        from rapido.db.engines import database
        database.delete_from(self)
        self._key = None
        self._dirty = True
        
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
        result = cls.all().filter('key in :keys', keys=keys).fetch(len(keys))

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
    def select(cls, *fields):
        """Mimics SELECT column query. If fields are not given it is
        equivalent to `all()`.

        >>> names = User.select('name').fetch(-1)
        >>> print names
        ... ['a', 'b', 'c', ...]
        >>> name_dob = User.select('name', 'dob').fetch(-1)
        >>> print name_dob
        ... [('a', '01-11-2001'), ...]
        >>> users = User.select().fetch(-1)
        >>> print users
        ... [<Object ...> ...]
        """
        def mapper(obj):
            if not fields:
                return obj
            if len(fields) > 1:
                return tuple([getattr(obj, name) for name in fields])
            return getattr(obj, fields[0])

        return Query(cls, mapper)

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
        return OrderedDict(cls._meta.fields)
    
    def __repr__(self):
        return "<Model %r: %s object at %s>" % (self._meta.name,
                                          self.__class__.__name__, hex(id(self)))

