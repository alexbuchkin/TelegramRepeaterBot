import psycopg2
import requests
import signal
import time

import constants

import logging
logging.basicConfig(level=logging.INFO)


class RepeaterBot:
    def __init__(
        self,
        token,
        database_url,
        database_settings,
    ):
        self.update_request_url = constants.GET_UPDATES_URL.format(token=token)
        self.send_message_url = constants.SEND_MESSAGE_URL.format(token=token)

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

        self.is_working = True
        signal.signal(signal.SIGTERM, self.on_sigterm)
        signal.signal(signal.SIGINT, self.on_sigterm)


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
            time_before_adding = time.time()
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
            logging.info(f'Message has been added to db, it took {time.time() - time_before_adding} s')

    def loop(self):
        while self.is_working:
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

        self.conn.close()
        logging.info('Disconnected from database')


    def on_sigterm(self, *args):
        self.is_working = False
