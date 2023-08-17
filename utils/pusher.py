from pusher import Pusher
from dotenv import load_dotenv
from os import getenv


def init_pusher() -> Pusher:
    load_dotenv()


    return Pusher(
        app_id=getenv('PUSHER_APP_ID'),
        key=getenv('PUSHER_KEY'),
        secret=getenv('PUSHER_SECRET'),
        cluster='eu',
        ssl=True
    )
