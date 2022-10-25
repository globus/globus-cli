def _key_to_keyfunc(k):
    """
    We allow for 'keys' which are functions that map columns onto value
    types -- they may do formatting or inspect multiple values on the
    object. In order to support this, wrap string keys in a simple function
    that does the natural lookup operation, but return any functions we
    receive as they are.
    """
    # if the key is a string, then the "keyfunc" is just a basic lookup
    # operation -- return that
    if isinstance(k, str):
        subkeys = k.split(".")

        def lookup(x):
            current = x
            for sub in subkeys:
                current = x[sub]
            return current

        return lookup
    # otherwise, the key must be a function which is executed on the item
    # to produce a value -- return it verbatim
    return k


class Field:
    """A field which will be shown in record or table output.
    When fields are provided as tuples, they are converted into this.

    :param name: the displayed name for the record field or the column
        name for table output
    :param key: a str for indexing into print data or a callable which
        produces a string given the print data
    :param wrap_enabled: in record output, is this field allowed to wrap
    """

    def __init__(self, name, key, wrap_enabled=False):
        self.name = name
        self.keyfunc = _key_to_keyfunc(key)
        self.wrap_enabled = wrap_enabled

    @classmethod
    def coerce(cls, rawfield):
        """given a (Field|tuple), convert to a Field"""
        if isinstance(rawfield, cls):
            return rawfield
        elif isinstance(rawfield, tuple):
            if len(rawfield) == 2:
                return cls(rawfield[0], rawfield[1])
            raise ValueError("cannot coerce tuple of bad length")
        raise TypeError(
            "Field.coerce must be given a field or tuple, "
            "got {}".format(type(rawfield))
        )

    def __call__(self, data):
        """extract the field's value from the print data"""
        return self.keyfunc(data)
