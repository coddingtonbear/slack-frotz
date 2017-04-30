import datetime
import os
import re
import shutil
import subprocess32 as subprocess

import config


class FrotzError(Exception):
    pass


class RestrictedCommandError(FrotzError):
    pass


class CommandTimeout(FrotzError):
    pass


class SessionReset(Exception):
    pass


class Response(object):
    def __init__(
        self,
        message,
        title=None,
    ):
        self._message = message
        self._title = title


class Session(object):
    def __init__(self, data_id, session_id):
        self._data_id = data_id
        self._session_id = session_id

    def get_save_path(self):
        return os.path.join(
            config.FROTZ_SAVE_PATH,
            self._data_id + '__' + self._session_id + '.zsav',
        )

    def get_data_info(self):
        return config.FROTZ_DATA_MAP[self._data_id]

    def input(self, command):
        if command in ['save', 'restore', 'quit', 'exit']:
            raise RestrictedCommandError(
                "The %s command is restricted." % command
            )

        if command in ['reset', 'restart']:
            filename, ext = os.path.splitext(self.get_save_path())
            shutil.copyfile(
                self.get_save_path(),
                '%s.%s.%s' % (
                    filename,
                    datetime.datetime.now().strftime('%Y%m%d%H%M%SZ'),
                    ext,
                )
            )
            os.unlink(self.get_save_path())
            raise SessionReset()

        return self._execute(command)

    def _build_command(self, command):
        cmd_parts = [
            command.encode('utf8'),
            'save',
        ]

        return '\n'.join(cmd_parts) + '\n'

    def _execute(self, command):
        info = self.get_data_info()

        proc = subprocess.Popen(
            [
                config.FROTZ_EXE_PATH,
                '-J',
                '-r', 'lt',
                '-r', 'cm',
                '-r', 'w',
                '-i',
                '-Z', '0',
                '-R', self.get_save_path(),
                info['path'],
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        try:
            output, err = proc.communicate(
                self._build_command(command),
                timeout=5
            )
            if proc.returncode != 0:
                raise FrotzError(err)
        except subprocess.TimeoutExpired:
            proc.kill()
            output, err = proc.communicate()
            raise CommandTimeout(
                "Stdout: %s; Stderr: %s" % (
                    output,
                    err,
                )
            )

        return self._get_state_data(
            output,
            err,

        )

    def _get_state_data(self, raw_output, err):
        output = raw_output[
            raw_output.find('>')+1:
            raw_output.rfind('>', 0, len(raw_output) - 1)
        ]
        output_lines = output.split('\n')

        state = {
            'raw': output,
            'message': '',
            'title': '',
            'location': '',
        }

        if 'Score:' in output_lines[0] and 'Moves:' in output_lines[0]:
            parts = re.split(r'\s+', output_lines[0])
            state['moves'] = int(parts[-1])
            state['score'] = int(parts[-3])
            state['location'] = ' '.join(parts[1:-4]).strip()
            state['title'] = output_lines[1].strip().strip()
            state['message'] = '\n'.join(output_lines[2:]).strip()
            if not state['message']:
                state['message'] = state['title']
                state['title'] = None
        else:
            state['message'] = output
            state['error'] = True

        return state
