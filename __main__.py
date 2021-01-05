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
)
@click.option(
    '--database-name',
    envvar='DATABASE_NAME',
    type=str,
)
@click.option(
    '--database-user',
    envvar='DATABASE_USER',
    type=str,
)
@click.option(
    '--database-password',
    envvar='DATABASE_PASSWORD',
    type=str,
)
@click.option(
    '--database-host',
    envvar='DATABASE_HOST',
    type=str,
    default='localhost',
)
@click.option(
    '--database-port',
    envvar='DATABASE_PORT',
    type=str,
    default='5432',
)
def main(
    bot_token,
    database_url,
    database_name,
    database_user,
    database_password,
    database_host,
    database_port,
):
    database_settings = {
        'dbname': database_name,
        'user': database_user,
        'password': database_password,
        'host': database_host,
        'port': database_port,
    }

    logging.info('Creating bot')
    time_before_creating_bot = time.time()
    bot = RepeaterBot(
        token=bot_token,
        database_url=database_url,
        database_settings=database_settings,
    )
    logging.info(f'Bot has been created, it took {time.time() - time_before_creating_bot} s')

    bot.loop()


if __name__ == '__main__':
    main()
