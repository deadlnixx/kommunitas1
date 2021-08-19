# flake8: noqa: F401
"""
Commands module.
Contains all start-commands, subcommands and CLI Interface creation.

Note: Be careful with file-scoped imports in these subfiles.
    as they are parsed on startup, nothing containing optional modules should be loaded.
"""
from kommunitas.commands.arguments import Arguments
from kommunitas.commands.build_config_commands import start_new_config
from kommunitas.commands.data_commands import (start_convert_data, start_download_data,
                                              start_list_data)
from kommunitas.commands.deploy_commands import (start_create_userdir, start_install_ui,
                                                start_new_hyperopt, start_new_strategy)
from kommunitas.commands.hyperopt_commands import start_hyperopt_list, start_hyperopt_show
from kommunitas.commands.list_commands import (start_list_exchanges, start_list_hyperopts,
                                              start_list_markets, start_list_strategies,
                                              start_list_timeframes, start_show_trades)
from kommunitas.commands.optimize_commands import start_backtesting, start_edge, start_hyperopt
from kommunitas.commands.pairlist_commands import start_test_pairlist
from kommunitas.commands.plot_commands import start_plot_dataframe, start_plot_profit
from kommunitas.commands.trade_commands import start_trading
from kommunitas.commands.webserver_commands import start_webserver
