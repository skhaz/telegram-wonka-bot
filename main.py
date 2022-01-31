import glob
import http
import os
import random
from typing import Set

import yaml
from flask import Flask, request
from google.cloud import vision
from telegram import Bot, Update
from telegram.ext import CallbackContext, Dispatcher, Filters, MessageHandler
from werkzeug.wrappers import Response

app = Flask(__name__)

vision_client = vision.ImageAnnotatorClient()

memes = list(glob.glob("memes/*"))


with open("keywords.yaml") as f:
    keywords = set(yaml.safe_load(f))


def words_matcher(phrase: str, words: Set[str], threshold: int = 3) -> bool:
    return len(set(phrase.lower().split()) & words) >= threshold


def photo(update: Update, context: CallbackContext) -> None:
    photo_file = update.message.photo[-1].get_file()
    buffer = photo_file.download_as_bytearray()
    image = vision.Image(content=bytes(buffer))

    response = vision_client.text_detection(image=image)
    text = " ".join([a.description for a in response.text_annotations])
    found = words_matcher(text, keywords)

    if found:
        meme = random.choice(memes)
        with open(meme, "rb") as f:
            update.message.reply_photo(photo=f)


bot = Bot(token=os.environ["TOKEN"])

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)
dispatcher.add_handler(MessageHandler(Filters.photo, photo))


@app.route("/", methods=["POST"])
def index() -> Response:
    dispatcher.process_update(Update.de_json(request.get_json(force=True), bot))

    return "", http.HTTPStatus.NO_CONTENT
