""" Kucoin exchange subclass """
import logging
from typing import Dict

from kommunitas.exchange import Exchange


logger = logging.getLogger(__name__)


class Kucoin(Exchange):
    """
    Kucoin exchange class. Contains adjustments needed for kommunitas to work
    with this exchange.

    Please note that this exchange is not included in the list of exchanges
    officially supported by the kommunitas development team. So some features
    may still not work as expected.
    """

    _ft_has: Dict = {
        "l2_limit_range": [20, 100],
        "l2_limit_range_required": False,
    }
