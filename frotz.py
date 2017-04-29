import os
import re
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
            os.unlink(self.get_save_path())
            raise SessionReset()

        return self._execute(command)

    def _build_command(self, command):
        save_path = self.get_save_path()

        cmd_parts = [
            'restore',
            save_path,
            '\\lt',
            '\\cm\\w',
            command.encode('utf8'),
            'save',
            save_path,
        ]
        if os.path.exists(save_path):
            cmd_parts.append('y')

        return '\n'.join(cmd_parts) + '\n'

    def _execute(self, command):
        info = self.get_data_info()

        had_previous_save = False
        if os.path.exists(self.get_save_path()):
            had_previous_save = True

        proc = subprocess.Popen(
            [
                config.FROTZ_EXE_PATH,
                '-i',
                '-Z',
                '0',
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
            had_previous_save=had_previous_save
        )

    def _get_state_data(self, output, err, had_previous_save=False):
        info = self.get_data_info()

        lines = output.split('\n')

        intro_lines = []
        output_lines = []

        with open('/tmp/ztest.log', 'w') as out:
            import json
            out.write(json.dumps(info) + '\n')

            for idx, line in enumerate(lines):
                line = line.replace('> > ', '')
                if line.startswith('@'):
                    continue

                if idx < info['header'] - 1:
                    out.write('header: %s\n' % line)
                    intro_lines.append(line)
                elif idx < info['header'] + info['load'] - 1:
                    out.write('load: %s\n' % line)
                    pass
                elif idx + info['save'] >= len(lines) + 1:
                    out.write('save: %s\n' % line)
                    pass
                else:
                    out.write('output: %s\n' % line)
                    output_lines.append(line)

        state = {
            'raw': output,
            'had_previous_save': had_previous_save,
        }

        raise Exception(lines)

        if 'Score:' in output_lines[0] and 'Moves:' in output_lines[0]:
            parts = re.split(r'\s+', output_lines[0])
            state['moves'] = int(parts[-1])
            state['score'] = int(parts[-3])
            state['location'] = ' '.join(parts[1:4])
            state['title'] = output_lines[1].strip()
            state['message'] = '\n'.join(output_lines[2:])
        else:
            state['error'] = True

        state['output'] = '\n'.join(output_lines)
        state['intro'] = '\n'.join(intro_lines)

        return state
