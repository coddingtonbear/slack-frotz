import logging
import traceback

from flask import Flask, jsonify, request

import config
import frotz


app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=config.LOG_OUTPUT,
    loglevel=logging.DEBUG,
)


@app.route("/")
def index():
    return "OK"


@app.route("/play/<data_id>/<session_id>", methods=['POST'])
def play(data_id, session_id):
    logger.info(
        'Incoming request for %s:%s',
        data_id,
        session_id,
    )
    command = request.form['text'].strip()
    if 'trigger_word' in request.form:
        command = command[len(request.form['trigger_word']) + 1:].strip()

    session = frotz.Session(data_id, session_id)

    try:
        state = session.input(command)
    except frotz.SessionReset:
        return jsonify({
            'title': 'Game Reset',
            'text': 'Your game has been reset.',
        })
    except frotz.FrotzError as e:
        return jsonify({
            'title': 'Frotz Error',
            'text': unicode(e)
        })
    except Exception as e:
        return jsonify({
            'title': 'Exception',
            'text': traceback.format_exc()
        })

    if not state['had_previous_save']:
        message = state['intro'] + '\n\n' + state['message']
    else:
        message = state['message']

    return jsonify({
        'title': state['title'],
        'text': message,
    })
