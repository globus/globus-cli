import json
import six

from globus_sdk import GlobusResponse

from globus_cli.safeio import safeprint
from globus_cli.helpers import outformat_is_json, get_jmespath_expression

# make sure this is a tuple
# if it's a list, pylint will freak out
__all__ = (
    'formatted_print',

    'FORMAT_SILENT',
    'FORMAT_JSON',
    'FORMAT_TEXT_TABLE',
    'FORMAT_TEXT_RECORD',
    'FORMAT_TEXT_RAW'
    # NOTE: we don't export FORMAT_TEXT_CUSTOM as actually passing it is
    # incorrect usage -- it's used internally, but similarly to the other
    # format constants
)


FORMAT_SILENT = 'silent'
FORMAT_JSON = 'json'
FORMAT_TEXT_TABLE = 'text_table'
FORMAT_TEXT_RECORD = 'text_record'
FORMAT_TEXT_RAW = 'text_raw'
FORMAT_TEXT_CUSTOM = 'text_custom'


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
    jmespath_expr = get_jmespath_expression()

    def _print(data):
        if jmespath_expr is not None:
            data = jmespath_expr.search(data)
        safeprint(json.dumps(data, indent=2))

    if isinstance(res, GlobusResponse):
        _print(res.data)
    elif isinstance(res, dict):
        _print(res)
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


def formatted_print(response_data,

                    simple_text=None, text_preamble=None, text_epilog=None,
                    text_format=FORMAT_TEXT_TABLE,

                    json_converter=None,

                    fields=None, response_key=None):
    """
    A generic output formatter. Consumes the following pieces of data:

    ``response_data`` is a dict or GlobusResponse object. It contains either an
    API response or synthesized data for printing.

    ``simple_text`` is a text override -- normal printing is skipped and this
    string is printed instead (text output only)
    ``text_preamble`` is text which prints before normal printing (text output
    only)
    ``text_epilog`` is text which prints after normal printing (text output
    only)
    ``text_format`` is one of the FORMAT_TEXT_* constants OR a callable which
    takes ``response_data`` and prints output. Note that when a callable is
    given, it does the actual printing

    ``json_converter`` is a callable that does preprocessing of JSON output. It
    must take ``response_data`` and produce another dict or dict-like object
    (json output only)

    ``fields`` is an iterable of (fieldname, keyfunc) tuples. When keyfunc is
    a string, it is implicitly converted to `lambda x: x[keyfunc]` (text output
    only)

    ``response_key`` is a key into the data to print. When used with table
    printing, it must get an iterable out, and when used with raw printing, it
    gets a string. Necessary for certain formats like text table (text output
    only)
    """
    def _assert_fields():
        if fields is None:
            raise ValueError(
                'Internal Error! Output format requires fields; none given. '
                'You can workaround this error by using `--format JSON`')

    def _print_as_json():
        print_json_response(json_converter(response_data)
                            if json_converter else response_data)

    def _print_as_text():
        # if we're given simple text, print that and exit
        if simple_text is not None:
            safeprint(simple_text)
            return

        # if there's a preamble, print it beofre any other text
        if text_preamble is not None:
            safeprint(text_preamble)

        # if there's a response key, key into it
        data = (response_data
                if response_key is None else
                response_data[response_key])

        #  do the various kinds of printing
        if text_format == FORMAT_TEXT_TABLE:
            _assert_fields()
            print_table(data, fields)
        elif text_format == FORMAT_TEXT_RECORD:
            _assert_fields()
            colon_formatted_print(data, fields)
        elif text_format == FORMAT_TEXT_RAW:
            safeprint(data)
        elif text_format == FORMAT_TEXT_CUSTOM:
            _custom_text_formatter(data)

        # if there's an epilog, print it after any text
        if text_epilog is not None:
            safeprint(text_epilog)

    if isinstance(text_format, six.string_types):
        text_format = text_format
        _custom_text_formatter = None
    else:
        _custom_text_formatter = text_format
        text_format = FORMAT_TEXT_CUSTOM

    if outformat_is_json():
        _print_as_json()
    else:
        # silent does nothing
        if text_format == FORMAT_SILENT:
            return
        _print_as_text()
