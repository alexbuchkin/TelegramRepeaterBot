import click
import time

from bot import RepeaterBot

import logging
logging.basicConfig(level=logging.INFO)


@click.command()
@click.option(
    '--bot-token',
    envvar='BOT_TOKEN',
    required=True,
    type=str,
)
@click.option(
    '--database-url',
    envvar='DATABASE_URL',
    type=str,
    required=True,
)
def main(
    bot_token,
    database_url,
):
    logging.info('Creating bot')
    time_before_creating_bot = time.time()
    bot = RepeaterBot(
        token=bot_token,
        database_url=database_url,
    )
    logging.info(
        'Bot has been created, it took '
        f'{time.time() - time_before_creating_bot} s'
    )

    bot.loop()


if __name__ == '__main__':
    main()
