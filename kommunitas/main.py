#!/usr/bin/env python3
"""
Main kommunitas bot script.
Read the documentation to know what cli arguments you need.
"""
import logging
import sys
from typing import Any, List


# check min. python version
if sys.version_info < (3, 7):
    sys.exit("kommunitas requires Python version >= 3.7")

from kommunitas.commands import Arguments
from kommunitas.exceptions import kommunitasException, OperationalException
from kommunitas.loggers import setup_logging_pre


logger = logging.getLogger('kommunitas')


def main(sysargv: List[str] = None) -> None:
    """
    This function will initiate the bot and start the trading loop.
    :return: None
    """

    return_code: Any = 1
    try:
        setup_logging_pre()
        arguments = Arguments(sysargv)
        args = arguments.get_parsed_arg()

        # Call subcommand.
        if 'func' in args:
            return_code = args['func'](args)
        else:
            # No subcommand was issued.
            raise OperationalException(
                "Usage of kommunitas requires a subcommand to be specified.\n"
                "To have the bot executing trades in live/dry-run modes, "
                "depending on the value of the `dry_run` setting in the config, run kommunitas "
                "as `kommunitas trade [options...]`.\n"
                "To see the full list of options available, please use "
                "`kommunitas --help` or `kommunitas <command> --help`."
            )

    except SystemExit as e:
        return_code = e
    except KeyboardInterrupt:
        logger.info('SIGINT received, aborting ...')
        return_code = 0
    except kommunitasException as e:
        logger.error(str(e))
        return_code = 2
    except Exception:
        logger.exception('Fatal exception!')
    finally:
        sys.exit(return_code)


if __name__ == '__main__':
    main()
