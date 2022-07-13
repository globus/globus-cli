# TDOD: Remove this file when endpoints natively support recursive ls

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any, Deque, Dict, Iterator, Optional, Tuple, cast

from globus_sdk import TransferClient

log = logging.getLogger(__name__)

ITEM_T = Dict[str, Any]
QUEUE_T = Deque[Tuple[Optional[str], str, int]]

# constants for controlling client-side rate limiting
SLEEP_FREQUENCY = 25
SLEEP_LEN = 1


def _client_side_limiter() -> Iterator[None]:
    counter = 0
    while True:
        counter += 1
        # rate limit based on number of ls calls we have made
        if counter % SLEEP_FREQUENCY == 0:
            log.debug(
                "recursive_operation_ls sleeping %s seconds to rate limit itself.",
                SLEEP_LEN,
            )
            time.sleep(SLEEP_LEN)

        yield


class RecursiveLsResponse:
    """
    Response class for recursive_operation_ls

    Used for iterating over potentially very large file systems without keeping the
    whole filesystem tree in memory.

    Uses an internal queue for BFS of the filesystem.

    Rate limits calls to reduce the changes of connection errors.

    :param client: `TransferClient`` used for making the operation_ls calls.
    :param endpoint_id: The endpoint that will be recursively ls'ed.
    :param ls_params: Query params sent to operation_ls
    :param max_depth: The maximum depth the recursive ls will go into the filesys
    :param filter_after_first: If True, any filter in ``ls_params`` will be applied
        to all calls. If False, any filter will be removed after the first ls.
    """

    def __init__(
        self,
        client: TransferClient,
        endpoint_id: str,
        ls_params: dict[str, Any],
        *,
        max_depth: int = 3,
        filter_after_first: bool = True,
    ) -> None:
        self._client = client
        self._endpoint_id = endpoint_id
        self._ls_params = ls_params
        self._max_depth = max_depth
        self._filter_after_first = filter_after_first

        start_path = cast(Optional[str], ls_params.get("path"))
        log.info(
            "Creating RecursiveLsResponse on path '%s' of endpoint '%s'",
            start_path,
            endpoint_id,
        )

        # call the iterable_func method to convert it to a generator expression
        self._generator = self._iterable_func(start_path)

        # grab the first element out of the internal iteration function
        # because this could raise a StopIteration exception, we need to be
        # careful and make sure that such a condition is respected (and
        # replicated as an iterable of length 0)
        try:
            self._first_elem: ITEM_T | None = next(self._generator)
        except StopIteration:
            # express this internally as "first_elem is null" -- just need some
            # way of making sure that it's clear
            self._first_elem = None

    def __iter__(self) -> Iterator[ITEM_T]:
        if self._first_elem is not None:
            yield self._first_elem
            yield from self._generator

    def _iterable_func(self, start_path: str | None) -> Iterator[ITEM_T]:
        """
        An internal function which has generator semantics. Defined using the
        `yield` syntax.
        Used to grab the first element during class initialization, and
        subsequently on calls to `next()` to get the remaining elements.
        We rely on the implicit StopIteration built into this type of function
        to propagate through the final `next()` call.
        """
        # iterator used for client-side limiting
        limiter = _client_side_limiter()

        # queue of (absolute_path, relative_path, depth) tuples.
        dir_queue: QUEUE_T = deque()
        # initialized with the start path (if any) and a depth of 0
        dir_queue.append((start_path, "", 0))

        # BFS is not done until the queue is empty
        while dir_queue:
            next(limiter)
            log.debug(
                "recursive_operation_ls BFS queue not empty, getting next path now."
            )

            # get path and current depth from the queue
            abs_path, rel_path, depth = dir_queue.pop()

            # set the target path to the popped absolute path if it exists
            if abs_path is not None:
                self._ls_params["path"] = abs_path

            # do the operation_ls with the updated params
            res = self._client.operation_ls(self._endpoint_id, **self._ls_params)
            res_data = res["DATA"]

            # add to the queue if there are additional listings to do
            # and we are not at the depth limit
            if depth < self._max_depth:
                # queue data includes the dir's name in the absolute and relative paths
                # and increases the depth by one.
                dir_queue.extend(
                    [
                        (
                            res["path"] + item["name"],
                            (rel_path + "/" if rel_path else "") + item["name"],
                            depth + 1,
                        )
                        # data is reversed to maintain any "orderby" ordering
                        for item in reversed(res_data)
                        if item["type"] == "dir"
                    ]
                )

            # if filter_after_first is False, stop filtering after the first
            # ls call has been made
            if not self._filter_after_first:
                self._ls_params.pop("filter", None)

            # for each item in the response data update the item's name with
            # the relative path popped from the queue, and yield the item
            for item in res_data:
                item["name"] = (rel_path + "/" if rel_path else "") + item["name"]
                yield cast(ITEM_T, item)
