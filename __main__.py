import click
import json
import requests
import sys
import time

MAIN_URL = 'https://api.telegram.org/bot{token}/'
GET_UPDATES_URL = MAIN_URL + 'getUpdates'
SEND_MESSAGE_URL = MAIN_URL + 'sendMessage'


class RepeaterBot:
    def __init__(
        self,
        token,
        last_update_ts=None,
    ):
        self.last_update_ts = last_update_ts or 0
        self.update_request_url = GET_UPDATES_URL.format(token=token)
        self.send_message_url = SEND_MESSAGE_URL.format(token=token)

    def send_update_request(
        self,
    ):
        response = requests.get(
            url=self.update_request_url,
        )
        if not response or not response.ok:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def get_new_messages(
        self,
        response_json,
    ):
        if not response_json.get('ok') or \
           not response_json.get('result'):
            return []
        message_list = [item['message'] for item in response_json['result'] if item.get('message')]
        return [
            {
                'text': message.get('text', 'This message has no text'),
                'chat_id': message['chat']['id'],
                'ts': message['date'],
            }
            for message in message_list
            if message['date'] > self.last_update_ts
        ]

    def update_last_ts(
        self,
        messages,
    ):
        new_ts = max((
            self.last_update_ts,
            *(item['ts'] for item in messages)
        ))
        if new_ts > self.last_update_ts:
            self.last_update_ts = new_ts

    def send_message(
        self,
        chat_id,
        text,
    ):
        requests.get(
            url=self.send_message_url,
            params={
                'chat_id': chat_id,
                'text': text,
            },
        )

    def loop(self):
        while True:
            new_messages = self.get_new_messages(self.send_update_request())
            for message in new_messages:
                self.send_message(
                    chat_id=message['chat_id'],
                    text=message['text'],
                )

            self.update_last_ts(new_messages)

            time.sleep(1)


@click.command()
@click.option(
    '--bot-token',
    envvar='BOT_TOKEN',
    required=True,
    type=str,
)
@click.option(
    '--last-update-ts',
    envvar='LAST_UPDATE_TS',
    type=int,
)
def main(bot_token, last_update_ts):
    bot = RepeaterBot(token=bot_token, last_update_ts=last_update_ts)
    bot.loop()


if __name__ == '__main__':
    main()
