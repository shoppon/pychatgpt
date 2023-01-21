import functools
import tenacity

from oslo_log import log as logging
from typing import Callable
from typing import Tuple
from typing import Type
from typing import Union

LOG = logging.getLogger(__name__)


def retry(retry_param: Union[None,
                             Type[Exception],
                             Tuple[Type[Exception], ...],
                             int,
                             Tuple[int, ...]],
          interval: float = 1,
          retries: int = 3,
          backoff_rate: float = 2,
          wait_random: bool = False,
          retry=tenacity.retry_if_exception_type) -> Callable:
    """Transplanted from cinder.utils.retry"""

    if retries < 1:
        raise ValueError('Retries must be greater than or '
                         'equal to 1 (received: %s). ' % retries)

    if wait_random:
        wait = tenacity.wait_random_exponential(multiplier=interval)
    else:
        wait = tenacity.wait_exponential(
            multiplier=interval, min=0, exp_base=backoff_rate)

    def _decorator(f: Callable) -> Callable:

        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            r = tenacity.Retrying(
                sleep=tenacity.nap.sleep,
                before_sleep=tenacity.before_sleep_log(LOG, logging.DEBUG),
                after=tenacity.after_log(LOG, logging.DEBUG),
                stop=tenacity.stop_after_attempt(retries),
                reraise=True,
                retry=retry(retry_param),
                wait=wait)
            return r(f, *args, **kwargs)

        return _wrapper

    return _decorator


def walk_class_hierarchy(clazz, encountered=None):
    """Walk class hierarchy, yielding most derived classes first."""
    if not encountered:
        encountered = []
    for subclass in clazz.__subclasses__():
        if subclass not in encountered:
            encountered.append(subclass)
            # drill down to leaves first
            for subsubclass in walk_class_hierarchy(subclass, encountered):
                yield subsubclass
            yield subclass
