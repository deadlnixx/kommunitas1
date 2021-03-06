from unittest.mock import MagicMock

import pytest

from kommunitas.enums import SellType
from kommunitas.persistence import Trade
from kommunitas.rpc.rpc import RPC
from kommunitas.strategy.interface import SellCheckTuple
from tests.conftest import get_patched_kommunitasbot, patch_get_signal


def test_may_execute_sell_stoploss_on_exchange_multi(default_conf, ticker, fee,
                                                     limit_buy_order, mocker) -> None:
    """
    Tests workflow of selling stoploss_on_exchange.
    Sells
    * first trade as stoploss
    * 2nd trade is kept
    * 3rd trade is sold via sell-signal
    """
    default_conf['max_open_trades'] = 3
    default_conf['exchange']['name'] = 'bitmart'

    stoploss = {
        'id': 123,
        'info': {}
    }
    stoploss_order_open = {
        "id": "123",
        "timestamp": 1542707426845,
        "datetime": "2018-11-20T09:50:26.845Z",
        "lastTradeTimestamp": None,
        "symbol": "BTC/USDT",
        "type": "stop_loss_limit",
        "side": "sell",
        "price": 1.08801,
        "amount": 90.99181074,
        "cost": 0.0,
        "average": 0.0,
        "filled": 0.0,
        "remaining": 0.0,
        "status": "open",
        "fee": None,
        "trades": None
    }
    stoploss_order_closed = stoploss_order_open.copy()
    stoploss_order_closed['status'] = 'closed'
    stoploss_order_closed['filled'] = stoploss_order_closed['amount']

    # Sell first trade based on stoploss, keep 2nd and 3rd trade open
    stoploss_order_mock = MagicMock(
        side_effect=[stoploss_order_closed, stoploss_order_open, stoploss_order_open])
    # Sell 3rd trade (not called for the first trade)
    should_sell_mock = MagicMock(side_effect=[
        SellCheckTuple(sell_type=SellType.NONE),
        SellCheckTuple(sell_type=SellType.SELL_SIGNAL)]
    )
    cancel_order_mock = MagicMock()
    mocker.patch('kommunitas.exchange.bitmart.stoploss', stoploss)
    mocker.patch.multiple(
        'kommunitas.exchange.Exchange',
        fetch_ticker=ticker,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
        fetch_stoploss_order=stoploss_order_mock,
        cancel_stoploss_order_with_result=cancel_order_mock,
    )

    mocker.patch.multiple(
        'kommunitas.kommunitasbot.kommunitasBot',
        create_stoploss_order=MagicMock(return_value=True),
        _notify_sell=MagicMock(),
    )
    mocker.patch("kommunitas.strategy.interface.IStrategy.should_sell", should_sell_mock)
    wallets_mock = mocker.patch("kommunitas.wallets.Wallets.update", MagicMock())
    mocker.patch("kommunitas.wallets.Wallets.get_free", MagicMock(return_value=1000))

    kommunitas = get_patched_kommunitasbot(mocker, default_conf)
    kommunitas.strategy.order_types['stoploss_on_exchange'] = True
    # Switch ordertype to market to close trade immediately
    kommunitas.strategy.order_types['sell'] = 'market'
    kommunitas.strategy.confirm_trade_entry = MagicMock(return_value=True)
    kommunitas.strategy.confirm_trade_exit = MagicMock(return_value=True)
    patch_get_signal(kommunitas)

    # Create some test data
    kommunitas.enter_positions()
    assert kommunitas.strategy.confirm_trade_entry.call_count == 3
    kommunitas.strategy.confirm_trade_entry.reset_mock()
    assert kommunitas.strategy.confirm_trade_exit.call_count == 0
    wallets_mock.reset_mock()

    trades = Trade.query.all()
    # Make sure stoploss-order is open and trade is bought (since we mock update_trade_state)
    for trade in trades:
        trade.stoploss_order_id = 3
        trade.open_order_id = None

    n = kommunitas.exit_positions(trades)
    assert n == 2
    assert should_sell_mock.call_count == 2
    assert kommunitas.strategy.confirm_trade_entry.call_count == 0
    assert kommunitas.strategy.confirm_trade_exit.call_count == 1
    kommunitas.strategy.confirm_trade_exit.reset_mock()

    # Only order for 3rd trade needs to be cancelled
    assert cancel_order_mock.call_count == 1
    # Wallets must be updated between stoploss cancellation and selling, and will be updated again
    # during update_trade_state
    assert wallets_mock.call_count == 4

    trade = trades[0]
    assert trade.sell_reason == SellType.STOPLOSS_ON_EXCHANGE.value
    assert not trade.is_open

    trade = trades[1]
    assert not trade.sell_reason
    assert trade.is_open

    trade = trades[2]
    assert trade.sell_reason == SellType.SELL_SIGNAL.value
    assert not trade.is_open


@pytest.mark.parametrize("balance_ratio,result1", [
                        (1, 200),
                        (0.99, 198),
])
def test_forcebuy_last_unlimited(default_conf, ticker, fee, limit_buy_order, mocker, balance_ratio,
                                 result1) -> None:
    """
    Tests workflow unlimited stake-amount
    Buy 4 trades, forcebuy a 5th trade
    Sell one trade, calculated stake amount should now be lower than before since
    one trade was sold at a loss.
    """
    default_conf['max_open_trades'] = 5
    default_conf['forcebuy_enable'] = True
    default_conf['stake_amount'] = 'unlimited'
    default_conf['tradable_balance_ratio'] = balance_ratio
    default_conf['dry_run_wallet'] = 1000
    default_conf['exchange']['name'] = 'bitmart'
    default_conf['telegram']['enabled'] = True
    mocker.patch('kommunitas.rpc.telegram.Telegram', MagicMock())
    mocker.patch.multiple(
        'kommunitas.exchange.Exchange',
        fetch_ticker=ticker,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
    )

    mocker.patch.multiple(
        'kommunitas.kommunitasbot.kommunitasBot',
        create_stoploss_order=MagicMock(return_value=True),
        _notify_sell=MagicMock(),
    )
    should_sell_mock = MagicMock(side_effect=[
        SellCheckTuple(sell_type=SellType.NONE),
        SellCheckTuple(sell_type=SellType.SELL_SIGNAL),
        SellCheckTuple(sell_type=SellType.NONE),
        SellCheckTuple(sell_type=SellType.NONE),
        SellCheckTuple(sell_type=SellType.NONE)]
    )
    mocker.patch("kommunitas.strategy.interface.IStrategy.should_sell", should_sell_mock)

    kommunitas = get_patched_kommunitasbot(mocker, default_conf)
    rpc = RPC(kommunitas)
    kommunitas.strategy.order_types['stoploss_on_exchange'] = True
    # Switch ordertype to market to close trade immediately
    kommunitas.strategy.order_types['sell'] = 'market'
    patch_get_signal(kommunitas)

    # Create 4 trades
    n = kommunitas.enter_positions()
    assert n == 4

    trades = Trade.query.all()
    assert len(trades) == 4
    assert kommunitas.wallets.get_trade_stake_amount('XRP/BTC') == result1

    rpc._rpc_forcebuy('TKN/BTC', None)

    trades = Trade.query.all()
    assert len(trades) == 5

    for trade in trades:
        assert trade.stake_amount == result1
        # Reset trade open order id's
        trade.open_order_id = None
    trades = Trade.get_open_trades()
    assert len(trades) == 5
    bals = kommunitas.wallets.get_all_balances()

    n = kommunitas.exit_positions(trades)
    assert n == 1
    trades = Trade.get_open_trades()
    # One trade sold
    assert len(trades) == 4
    # stake-amount should now be reduced, since one trade was sold at a loss.
    assert kommunitas.wallets.get_trade_stake_amount('XRP/BTC') < result1
    # Validate that balance of sold trade is not in dry-run balances anymore.
    bals2 = kommunitas.wallets.get_all_balances()
    assert bals != bals2
    assert len(bals) == 6
    assert len(bals2) == 5
    assert 'LTC' in bals
    assert 'LTC' not in bals2
