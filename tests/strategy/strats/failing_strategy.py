# The strategy which fails to load due to non-existent dependency

import nonexiting_module  # noqa

from kommunitas.strategy.interface import IStrategy


class TestStrategyLegacy(IStrategy):
    pass
