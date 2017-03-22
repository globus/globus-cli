import json
import six

from globus_sdk import GlobusHTTPResponse

from globus_cli.safeio import safeprint


def print_json_response(res):
    if isinstance(res, GlobusHTTPResponse):
        safeprint(json.dumps(res.data, indent=2))
    elif isinstance(res, dict):
        safeprint(json.dumps(res, indent=2))
    else:
        safeprint(res)


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
    if isinstance(k, six.string_types):
        def lookup(x):
            return x[k]
        return lookup
    # otherwise, the key must be a function which is executed on the item
    # to produce a value -- return it verbatim
    return k


def colon_formatted_print(data, named_fields):
    maxlen = max(len(n) for n, f in named_fields) + 1
    for name, field in named_fields:
        field_keyfunc = _key_to_keyfunc(field)
        safeprint('{} {}'.format((name + ':').ljust(maxlen),
                                 field_keyfunc(data)))


def print_table(iterable, headers_and_keys, print_headers=True):
    # the iterable may not be safe to walk multiple times, so we must walk it
    # only once -- however, to let us write things naturally, convert it to a
    # list and we can assume it is safe to walk repeatedly
    iterable = list(iterable)

    # extract headers and keys as separate lists
    headers = [h for (h, k) in headers_and_keys]
    keys = [k for (h, k) in headers_and_keys]

    # convert all keys to keyfuncs
    keyfuncs = [_key_to_keyfunc(key) for key in keys]

    # use the iterable to find the max width of an element for each column, in
    # the same order as the headers_and_keys array
    # use a special function to handle empty iterable
    def get_max_colwidth(kf):
        def _safelen(x):
            try:
                return len(x)
            except TypeError:
                return len(str(x))
        lengths = [_safelen(kf(i)) for i in iterable]
        if not lengths:
            return 0
        else:
            return max(lengths)

    widths = [get_max_colwidth(kf) for kf in keyfuncs]
    # handle the case in which the column header is the widest thing
    widths = [max(w, len(h)) for w, h in zip(widths, headers)]

    # create a format string based on column widths
    format_str = six.u(' | '.join('{:' + str(w) + '}' for w in widths))

    def none_to_null(val):
        if val is None:
            return 'NULL'
        return val

    # print headers
    if print_headers:
        safeprint(format_str.format(*[h for h in headers]))
        safeprint(format_str.format(*['-'*w for w in widths]))
    # print the rows of data
    for i in iterable:
        safeprint(format_str.format(*[none_to_null(kf(i)) for kf in keyfuncs]))
