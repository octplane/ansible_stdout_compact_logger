# pylint: disable=E0401,C0103,C0111,W0212

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
from datetime import datetime
from ansible import constants as C
from ansible.utils.color import colorize, hostcolor

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'oneline'

    def _get_duration(self):
        end = datetime.now()
        total_duration = (end - self.tark_started)
        duration = total_duration.microseconds / 1000 + total_duration.total_seconds() * 1000
        return duration

    def _command_generic_msg(self, hostname, result, caption):
        duration = self._get_duration()

        stdout = result.get('stdout', '')
        if self._display.verbosity > 0:
            if 'stderr' in result and result['stderr']:
                stderr = result.get('stderr', '')
                return "%s | %s | %sms | rc=%s | stdout: \n%s\n\n\t\t\t\tstderr: %s" % \
                    (hostname, caption, duration, result.get('rc', 0), stdout, stderr)
            else:
                if len(stdout) > 0:
                    return "%s | %s | %sms | rc=%s | stdout: \n%s\n" % \
                        (hostname, caption, duration, result.get('rc', 0), stdout)
                else:
                    return "%s | %s | %sms | rc=%s | no stdout" % \
                        (hostname, caption, duration, result.get('rc', 0))
        else:
            return "%s | %s | %sms | rc=%s" % (hostname, caption, duration, result.get('rc', 0))

    def v2_playbook_on_task_start(self, task, is_conditional):
        # pylint: disable=W0613,W0201
        self.tark_started = datetime.now()

        sys.stdout.write("[%s] %s | " % (str(self.tark_started), task.get_name()))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        # pylint: disable=W0613,
        if 'exception' in result._result:
            exception_message = "An exception occurred during task execution."
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = exception_message + \
                    "To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = exception_message + \
                    "The full traceback is:\n" + result._result['exception'].replace('\n', '')

            if result._task.action in C.MODULE_NO_JSON:
                self._display.display(self._command_generic_msg( \
                    result._host.get_name(), result._result, 'FAILED'), color='red')
            else:
                self._display.display(msg, color='red')

        self._display.display("%s | FAILED!" % (result._host.get_name()), color='red')
        self._display.display(self._deep_serialize(result._result), color='cyan')

    def v2_runner_on_ok(self, result):
        duration = self._get_duration()

        if result._task.action in C.MODULE_NO_JSON:
            self._display.display(
                self._command_generic_msg(result._host.get_name(), result._result, 'SUCCESS'),
                color='green')
        else:

            self._display.display("%s | SUCCESS | %dms" %
                (result._host.get_name(), duration), color='green')
            if self._display.verbosity > 0:
                self._display.display(self._deep_serialize(result._result), color='green')
                # self._display.display(self._dump_results(result._result))


    def v2_runner_on_unreachable(self, result):
        self._display.display("%s | UNREACHABLE!: %s" % \
            (result._host.get_name(), result._result.get('msg', '')), color='yellow')

    def v2_runner_on_skipped(self, result):
        duration = self._get_duration()

        self._display.display("%s | SKIPPED | %dms" % \
            (result._host.get_name(), duration), color='cyan')

    def _deep_serialize(self, data, indent=0):
        output = " " * indent * 2
        if isinstance(data, list):
            for item in data:
                serialized_content = self._deep_serialize(item, indent + 1)
                output = output + "- " + serialized_content
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    output = output + "- %s:" % key
                    output = output + "\n" + " " * indent * 2 + \
                        self._deep_serialize(value, indent + 1)
                elif isinstance(value, list):
                    output = output + "- %s:" % key
                    output = output + "\n" + " " * indent * 2 + \
                        self._deep_serialize(value, indent + 1)
                elif isinstance(value, basestring):
                    if len(value) > 0:
                        output = output + "- %s:" % key
                        output = output + value + "\n" + " " * indent * 2
        return output

    def v2_playbook_on_include(self, included_file):
        msg = 'included: %s for %s' % \
            (included_file._filename, ", ".join([h.name for h in included_file._hosts]))
        self._display.display(msg, color='cyan')

    def v2_playbook_on_stats(self, stats):
        self._display.display("[%s] %s" % (str(datetime.now()), "play recap"))

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(u"[%s] %s : %s %s %s %s" % (
                str(datetime.now()),
                hostcolor(h, t),
                colorize(u'ok', t['ok'], 'green'),
                colorize(u'changed', t['changed'], 'yellow'),
                colorize(u'unreachable', t['unreachable'], 'yellow'),
                colorize(u'failed', t['failures'], 'red')),
                screen_only=True
            )

