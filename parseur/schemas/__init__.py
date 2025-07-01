from marshmallow import EXCLUDE, post_load, Schema


class AttrDict(dict):
    """
    A dictionary subclass that allows attribute-style access.

    This class extends the built-in `dict` to support getting, setting, and
    deleting keys using attribute syntax. It is particularly useful for
    configuration objects or JSON-like structures where dot notation is preferred.

    Example:
        d = AttrDict()
        d.foo = 42 # sets d['foo'] = 42
        print(d.foo) # gets d['foo'], prints 42
        del d.foo # deletes d['foo']

        # Also works with standard dict access
        d['bar'] = 100
        print(d.bar) # prints 100
    """

    def __getattr__(self, name):
        """
        Retrieve a value via attribute access.

        Raises:
            AttributeError: If the key does not exist.
        """
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name, value):
        """
        Set a key via attribute access.
        """
        self[name] = value

    def __delattr__(self, name):
        """
        Delete a key via attribute access.

        Raises:
            AttributeError: If the key does not exist.
        """
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(name) from e


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def to_namespace(self, data, **kwargs):
        return AttrDict(data)
