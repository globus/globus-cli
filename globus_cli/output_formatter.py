import json
import six

from globus_sdk import GlobusResponse

from globus_cli.safeio import safeprint
from globus_cli.helpers import outformat_is_json

# make sure this is a tuple
# if it's a list, pylint will freak out
__all__ = ('OutputFormatter', 'StreamingOutputFormatter')


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


def print_json_response(res):
    if isinstance(res, GlobusResponse):
        safeprint(json.dumps(res.data, indent=2))
    elif isinstance(res, dict):
        safeprint(json.dumps(res, indent=2))
    else:
        safeprint(res)


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


class OutputFormatter(object):
    """
    A generic output formatter. Consumes the following pieces of data:

    ``fields`` is an iterable of (fieldname, keyfunc) tuples. When keyfunc is
    a string, it is implicitly converted to `lambda x: x[keyfunc]`

    ``response_key`` is a key into the data to print. When used with table
    printing, it must get an iterable out, and when used with raw printing, it
    gets a string. Necessary for certain formats (e.g. text table)
    """
    def __init__(self, fields=(), response_key=None, text_format='text_table'):
        self.format = None

        if isinstance(text_format, six.string_types):
            self.text_format = text_format
            self._custom_text_formatter = None
        else:
            self.text_format = 'text_custom'
            self._custom_text_formatter = text_format

        self.fields = fields
        self.response_key = response_key

    def detect_format(self):
        if outformat_is_json():
            self.format = 'json'
        else:
            self.format = self.text_format
        return self.format

    def _print_response_text(
            self, response_data, simple_text, text_preamble, text_epilog):
        # if we're given simple text, print that and exit
        if simple_text is not None:
            safeprint(simple_text)
            return

        # if there's a preamble, print it beofre any other text
        if text_preamble is not None:
            safeprint(text_preamble)

        # if there's a response key, key into it
        if self.response_key is not None:
            response_data = response_data[self.response_key]

        #  do the various kinds of printing
        if self.format == 'text_table':
            print_table(response_data, self.fields)
        elif self.format == 'text_record':
            colon_formatted_print(response_data, self.fields)
        elif self.format == 'text_raw':
            safeprint(response_data)
        elif self.format == 'text_custom':
            self._custom_text_formatter(response_data)

        # if there's an epilog, print it after any text
        if text_epilog is not None:
            safeprint(text_epilog)

    def _print_response_json(self, response_data, json_converter):
        if json_converter:
            response_data = json_converter(response_data)
        print_json_response(response_data)

    def print_response(self, response_data, simple_text=None,
                       text_preamble=None, text_epilog=None,
                       json_converter=None):
        self.detect_format()

        # silent does nothing
        if self.format == 'silent':
            return

        # json prints json
        elif self.format == 'json':
            self._print_response_json(response_data, json_converter)

        # text formats are where the fun is at
        elif self.format.startswith('text_'):
            self._print_response_text(response_data, simple_text,
                                      text_preamble, text_epilog)
        else:
            raise ValueError("Can't output in format '{}'".format(self.format))
