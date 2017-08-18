# TDOD: Remove this file when endpoints natively support recursive ls

import logging
import time
from collections import deque

from globus_sdk.response import GlobusResponse
from globus_sdk.transfer.paging import PaginatedResource

logger = logging.getLogger(__name__)

# constants for controlling rate limiting
SLEEP_FREQUENCY = 25
SLEEP_LEN = 1


class RecursiveLsResponse(PaginatedResource):
    """
    Response class for recursive_operation_ls
    Uses PaginatedResource logic for iterating over potentially very
    large file systems without keeping the whole filesystem in memory,
    but rather than using Globus paging uses an internal queue
    for BFS of the filesystem.
    Rate limits calls to prevent getting back connection errors.
    """
    def __init__(self, client, endpoint_id,
                 max_depth, follow_symlinks, filter_after_first, ls_params):
        """
        **Parameters**
          ``client``
            A `TransferClient`` used for making the operation_ls calls.
          ``endpoint_id``
            The endpoint that will be recursively ls'ed.
          ``max_depth``
            The maximum depth the recursive ls will go into the file system.
          ``filter_after_first``
            If True, any filter in ``ls_params`` will be applied to all calls
            If False, any filter in ``ls_params`` will only be applied to the
            first ls.
          ``ls_params``
            Query params sent to operation_ls, see operation_ls for more
            details.
        """
        logger.info("Creating RecursiveLsResponse on path {} of endpoint {}"
                    .format(ls_params.get("path"), endpoint_id))

        self.client = client
        self.endpoint_id = endpoint_id
        self.ls_params = ls_params
        self.max_depth = max_depth
        self.filter_after_first = filter_after_first
        self.follow_symlinks = follow_symlinks
        self.filtering = True
        self.ls_count = 0

        # queue of (absolute_path, relative_path, depth) tuples.
        self.queue = deque()
        # initialized with the start path (if any) and a depth of 0
        self.queue.append((self.ls_params.get("path"), "", 0))

        # call the iterable_func method to convert it to a generator expression
        self.generator = self.iterable_func()

        # grab the first element out of the internal iteration function
        # because this could raise a StopIteration exception, we need to be
        # careful and make sure that such a condition is respected (and
        # replicated as an iterable of length 0)
        try:
            self.first_elem = next(self.generator)
        except StopIteration:
            # express this internally as "generator is null" -- just need some
            # way of making sure that it's clear
            self.generator = None

    def iterable_func(self):
        """
        An internal function which has generator semantics. Defined using the
        `yield` syntax.
        Used to grab the first element during class initialization, and
        subsequently on calls to `next()` to get the remaining elements.
        We rely on the implicit StopIteration built into this type of function
        to propagate through the final `next()` call.
        """
        # BFS is not done until the queue is empty
        while self.queue:
            logger.debug(("recursive_operation_ls BFS queue not empty, "
                          "getting next path now."))

            # rate limit based on number of ls calls we have made
            self.ls_count += 1
            if self.ls_count % SLEEP_FREQUENCY == 0:
                logger.debug(("recursive_operation_ls sleeping {} seconds to "
                              "rate limit itself.".format(SLEEP_LEN)))
                time.sleep(SLEEP_LEN)

            # get path and current depth from the queue
            abs_path, rel_path, depth = self.queue.pop()

            # set the target path to the popped absolute path if it exists
            if abs_path:
                self.ls_params["path"] = abs_path

            # if filter_after_first is False, stop filtering after the first
            # ls call has been made
            if not self.filter_after_first:
                if self.filtering:
                    self.filtering = False
                else:
                    try:
                        self.ls_params.pop("filter")
                    except KeyError:
                        pass

            # do the operation_ls with the updated params
            res = self.client.operation_ls(self.endpoint_id, **self.ls_params)
            res_data = res["DATA"]

            # if we aren't at the depth limit, add dir entries to the queue.
            # including the dir's name in the absolute and relative paths
            # and increasing the depth by one.
            # data is reversed to maintain any "orderby" ordering
            # syminks to dirs are ignored unless follow_symlinks is true
            if depth < self.max_depth:

                for item in reversed(res_data):

                    if item["type"] == "dir" and (
                            self.follow_symlinks or not item["link_target"]):

                        next_abs_path = res["path"] + item["name"]
                        next_rel_path = (
                            rel_path + "/" if rel_path else "") + item["name"]

                        self.queue.append((
                            next_abs_path, next_rel_path, depth + 1))

            # for each item in the response data update the item's name with
            # the relative path popped from the queue, and yield the item
            for item in res_data:
                item["name"] = (
                    rel_path + "/" if rel_path else "") + item["name"]
                yield GlobusResponse(item)
