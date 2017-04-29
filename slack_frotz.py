import traceback

from flask import Flask, jsonify, request

import frotz


app = Flask(__name__)


@app.route("/")
def index():
    return "OK"


@app.route("/play/<data_id>/<session_id>", methods=['POST'])
def play(data_id, session_id):
    command = request.form['text'].strip()
    if 'trigger_word' in request.form:
        command = command[len(request.form['trigger_word']) + 1:].strip()

    session = frotz.Session(data_id, session_id)

    try:
        state = session.input(command)

        message = {
            'text': state['message'],
        }
        if state['title']:
            message['text'] = u'*{title}*\n{message}'.format(
                title=state['title'],
                message=state['message']
            )

        if not state['had_previous_save']:
            message['text'] = '\n\n'.join([
                '*' + state['intro'] + '*',
                message['text']
            ])

        return jsonify(message)
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


    return jsonify({
        'text': 'A...surprise...has occurred; try again.'
    })
