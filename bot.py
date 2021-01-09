import requests
import signal
import time

import constants
from database import DatabaseHolder

import logging
logging.basicConfig(level=logging.INFO)


class RepeaterBot:
    def __init__(
        self,
        token,
        database_url,
    ):
        self.update_request_url = constants.GET_UPDATES_URL.format(token=token)
        self.send_message_url = constants.SEND_MESSAGE_URL.format(token=token)

        self.database = DatabaseHolder(database_url)
        logging.info('Connected to database')

        self.last_update_ts = self.database.get_last_update_ts()
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
            return dict()

    def get_new_messages(
        self,
        response_json,
    ):
        if not response_json.get('ok') or \
           'result' not in response_json:
            logging.info('"result" or "ok" is not valid')
            return []

        received_messages = (
            item['message']
            for item in response_json['result']
            if item.get('message')
        )

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
        response = requests.get(
            url=self.send_message_url,
            params={
                'chat_id': chat_id,
                'text': text,
            },
        )
        response.raise_for_status()

    def loop(self):
        while self.is_working:

            new_messages = self.get_new_messages(self.send_update_request())
            logging.info(f'{len(new_messages)} new messages received')

            for message in new_messages:
                self.send_message(
                    chat_id=message['chat_id'],
                    text=message['text'],
                )

                self.database.store_message(
                    chat_id=message['chat_id'],
                    text=message['text'],
                    ts=message['ts'],
                )

            self.update_last_ts(new_messages)

            time.sleep(1)

    def on_sigterm(self, *args):
        self.is_working = False
