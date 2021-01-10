import time

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from constants import (
    MAX_MESSAGE_LENGTH,
    MESSAGE_SEQ_NAME,
)

import logging
logging.basicConfig(level=logging.INFO)

Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'

    pk_id = sa.Column(
        sa.Integer,
        sa.Sequence(MESSAGE_SEQ_NAME),
        primary_key=True,
    )
    text = sa.Column(sa.String(MAX_MESSAGE_LENGTH))
    chat_id = sa.Column(sa.BigInteger, nullable=False)
    ts = sa.Column(sa.BigInteger, nullable=False)

    def __repr__(self):
        return (
            '<Message('
            f'pk_id="{self.pk_id}"'
            ', '
            f'text="{self.text}"'
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
            text=text,
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
