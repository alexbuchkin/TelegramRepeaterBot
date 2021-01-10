import time

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from constants import MAX_MESSAGE_LENGTH

import logging
logging.basicConfig(level=logging.INFO)

Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'

    message = sa.Column(sa.String(MAX_MESSAGE_LENGTH))
    chat_id = sa.Column(sa.BigInteger, nullable=False)

    # Костыль! Добавить Sequence в качестве primary_key
    ts = sa.Column(sa.BigInteger, primary_key=True)

    def __repr__(self):
        # return f'<User(name='], fullname='%s', nickname='%s')>'
        return (
            '<Message('
            f'message="{self.message}"'
            ', '
            f'chat_id="{self.chat_id}"'
            ', '
            f'ts="{self.ts}"'
            ')>'
        )


class DatabaseHolder:
    def __init__(
        self,
        database_url,
    ):
        self.engine = sa.create_engine(database_url, echo=True)
        self.session = sa.orm.sessionmaker(bind=self.engine)()

    def get_last_update_ts(self):
        last_update_ts = self.session.query(
            sa.func.max(Message.ts)
        ).first()[0]

        return last_update_ts or 0

    def store_message(
        self,
        chat_id,
        text,
        ts,
    ):
        time_before_adding = time.time()

        new_message = Message(
            message=text,
            chat_id=chat_id,
            ts=ts,
        )

        self.session.add(new_message)
        self.session.commit()

        logging.info(
            'Message has been added to db, it took '
            f'{time.time() - time_before_adding} s'
        )

    def __del__(self):
        self.session.close()
        logging.info('Disconnected from database')
