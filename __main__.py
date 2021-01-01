import click
import json
import requests
import sys
import time

import logging
import psycopg2

logging.basicConfig(level=logging.INFO)

MAIN_URL = 'https://api.telegram.org/bot{token}/'
GET_UPDATES_URL = MAIN_URL + 'getUpdates'
SEND_MESSAGE_URL = MAIN_URL + 'sendMessage'


class RepeaterBot:
    def __init__(
        self,
        token,
        database_url,
        database_settings,
    ):
        self.update_request_url = GET_UPDATES_URL.format(token=token)
        self.send_message_url = SEND_MESSAGE_URL.format(token=token)

        if database_url:
            self.conn = psycopg2.connect(database_url)
        else:
            if any((not value for value in database_settings.values())):
                raise KeyError('Some fields from database settings are missing')
            self.conn = psycopg2.connect(**database_settings)

        logging.info('Connected to database')

        with self.conn.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS messages
                (
                    message VARCHAR(4096),
                    chat_id BIGINT NOT NULL,
                    ts BIGINT NOT NULL
                );
                '''
            )
            self.conn.commit()
            logging.info('Table has been created')

        with self.conn.cursor() as cursor:
            cursor.execute(
                '''
                SELECT MAX(ts)
                FROM messages;
                '''
            )
            result = cursor.fetchone()
            self.last_update_ts = result[0] or 0
        logging.info(f'last_update_ts is set to {self.last_update_ts}')

    def send_update_request(
        self,
    ):
        logging.info(f'Sending request to: {self.update_request_url}')
        response = requests.get(
            url=self.update_request_url,
        )
        if not response or not response.ok:
            logging.info('not response or not response.ok')
            return {}
        try:
            return response.json()
        except ValueError:
            logging.info('responsing json is not valid')
            return {}

    def get_new_messages(
        self,
        response_json,
    ):
        if not response_json.get('ok') or \
           'result' not in response_json:
            logging.info('"result" or "ok" is not valid')
            return []

        received_messages = (item['message'] for item in response_json['result'] if item.get('message'))

        return [
            {
                'text': message.get('text'),
                'chat_id': message['chat']['id'],
                'ts': message['date'],
            }
            for message in received_messages
            if message['date'] > self.last_update_ts
        ]

    def update_last_ts(
        self,
        messages,
    ):
        self.last_update_ts = max((
            self.last_update_ts,
            *(item['ts'] for item in messages)
        ))

    def send_message(
        self,
        chat_id,
        text,
    ):
        text = text or 'This message has no text'
        logging.info(f'Sending message "{text}" to chat_id "{chat_id}"')
        requests.get(
            url=self.send_message_url,
            params={
                'chat_id': chat_id,
                'text': text,
            },
        )

    def store_message(
        self,
        chat_id,
        text,
        ts,
    ):
        with self.conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO messages
                VALUES (%(message)s, %(chat_id)s, %(ts)s);
                ''',
                {
                    'message': text,
                    'chat_id': chat_id,
                    'ts': ts,
                }
            )
            self.conn.commit()

    def loop(self):
        while True:
            new_messages = self.get_new_messages(self.send_update_request())
            logging.info(f'{len(new_messages)} new messages received')

            for message in new_messages:
                self.send_message(
                    chat_id=message['chat_id'],
                    text=message['text'],
                )

                self.store_message(
                    chat_id=message['chat_id'],
                    text=message['text'],
                    ts=message['ts'],
                )

            self.update_last_ts(new_messages)

            time.sleep(1)

    def __exit__(self):
        self.cursor.close()
        self.conn.close()

        logging.info('Disconnected from database')


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
    bot = RepeaterBot(
        token=bot_token,
        database_url=database_url,
        database_settings=database_settings,
    )
    logging.info('Bot has been created')

    bot.loop()


if __name__ == '__main__':
    main()
