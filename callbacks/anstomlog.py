# coding=utf-8

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
from datetime import datetime

try:
    from ansible.utils.color import colorize, hostcolor
    from ansible.plugins.callback import CallbackBase
    from ansible import constants as C
except ImportError:
    class CallbackBase:
        # pylint: disable=I0011,R0903
        pass
    class C:
        COLOR_OK = 'green'

import unittest

# Fields we would like to see before the others, in this order, please...
PREFERED_FIELDS = ['stdout', 'rc', 'stderr', 'start', 'end', 'msg']
# Fields we will delete from the result
DELETABLE_FIELDS = [
    'stdout', 'stdout_lines', 'rc', 'stderr', 'start', 'end', 'msg',
    '_ansible_verbose_always', '_ansible_no_log', 'invocation', '_ansible_parsed',
    '_ansible_item_result', '_ansible_ignore_errors', '_ansible_item_label']

def deep_serialize(data, indent=0):
    # pylint: disable=I0011,E0602,R0912,W0631

    padding = " " * indent * 2
    if isinstance(data, list):
        if data == []:
            return "[]"
        output = "[ "
        if len(data) == 1:
            output = output + \
                ("\n" +
                 padding).join(deep_serialize(data[0], 0).splitlines()) + " ]"
        else:
            list_padding = " " * (indent + 1) * 2

            for item in data:
                output = output + "\n" + list_padding + "- " + \
                    deep_serialize(item, indent)
            output = output + "\n" + padding + " ]"
    elif isinstance(data, dict):
        if "_ansible_no_log" in data and data["_ansible_no_log"]:
            data = {"censored":
                    "the output has been hidden due to the fact that"
                    " 'no_log: true' was specified for this result"}
        list_padding = " " * (indent + 1) * 2
        output = "{\n"

        for key in PREFERED_FIELDS:
            if key in data.keys():
                value = data[key]
                prefix = list_padding + "- %s: " % key
                output = output + prefix + "%s\n" % \
                    "\n".join([" " * len(prefix) + line
                               for line in deep_serialize(value, indent)
                               .splitlines()]).strip()

        for key in DELETABLE_FIELDS:
            if key in data.keys():
                del data[key]

        for key, value in data.items():
            output = output + list_padding + \
                "- %s: %s\n" % (key, deep_serialize(value, indent + 1))

        output = output + padding + "}"
    else:
        string_form = str(data)
        if len(string_form) == 0:
            return "\"\""

        return string_form
    return output


class TestStringMethods(unittest.TestCase):

    test_structure = {
        u'cmd': [u'false'], u'end': u'2016-12-29 16:46:04.151591',
        '_ansible_no_log': False, u'stdout': u'', u'changed': True, 'failed': True,
        u'delta': u'0:00:00.005046', u'stderr': u'', u'rc': 1, 'invocation':
            {'module_name': u'command',
             u'module_args': {
                 u'creates': None, u'executable': None, u'chdir': None,
                 u'_raw_params': u'false', u'removes': None,
                 u'warn': True, u'_uses_shell': False}},
        'stdout_lines': [], u'start': u'2016-12-29 16:46:04.146545', u'warnings': []}

    def test_single_item_array(self):
        self.assertEqual(
            deep_serialize(self.test_structure['cmd']),
            "[ false ]")

    def test_single_empty_item_array(self):
        self.assertEqual(
            deep_serialize([""]),
            "[ \"\" ]")

    def test_issue_4(self):
        self.assertEqual(
            deep_serialize(["ÉLÉGANT"]),
            "[ ÉLÉGANT ]")

    def test_empty_array(self):
        self.assertEqual(
            deep_serialize(self.test_structure['stdout_lines']),
            "[]")

    def test_simple_hash(self):
        hs = {"cmd": "toto", "ret": 12}
        expected_result = "{\n  - cmd: toto\n  - ret: 12\n}"
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_hash_array(self):
        hs = {u'cmd': [u'false']}
        expected_result = "{\n  - cmd: [ false ]\n}"
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_hash_array2(self):
        hs = {u'cmd': ['one', 'two']}
        expected_result = """{
  - cmd: [ 
    - one
    - two
   ]
}"""
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_favorite_hash(self):
        hs = {"cmd": "toto", "rc": 12}
        expected_result = "{\n  - rc: 12\n  - cmd: toto\n}"
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_nested(self):
        hs = {u'cmd': {'bar': ['one', 'two']}}
        expected_result = """{
  - cmd: {
    - bar: [ 
      - one
      - two
     ]
  }
}"""
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_multiline_single(self):
        # pylint: disable=I0011,C0303
        hs = [["foo", "bar"]]
        expected_result = """[ [ 
  - foo
  - bar
 ] ]"""
        # print(deep_serialize(hs))
        # print(expected_result)
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_empty_array_no_padding(self):
        hs = [[{"foo": []}]]
        expected_result = """[ [ {
  - foo: []
} ] ]"""
        # print(deep_serialize(hs))
        # print(expected_result)
        self.assertEqual(deep_serialize(hs), expected_result)

    def test_hidden_fields(self):
        hs = {"_ansible_verbose_always": True}
        expected_result = """{
}"""
        # print(deep_serialize(hs))
        # print(expected_result)
        self.assertEqual(deep_serialize(hs), expected_result)


class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'anstomlog'

    def _get_duration(self):
        end = datetime.now()
        total_duration = (end - self.task_started)
        seconds = total_duration.total_seconds()
        if seconds >= 60:
            seconds_remaining = seconds % 60
            minutes = (seconds - seconds_remaining) / 60
            duration = "{0:.0f}m{1:.0f}s".format(minutes, seconds_remaining)
        elif seconds >= 1:
            duration = "{0:.2f}s".format(seconds)
        else:
            duration = "{0:.0f}ms".format(seconds * 1000)
        return duration

    def _command_generic_msg(self, hostname, result, caption):
        duration = self._get_duration()

        stdout = result.get('stdout', '')
        if self._display.verbosity > 0:
            if 'stderr' in result and result['stderr']:
                stderr = result.get('stderr', '')
                return "%s | %s | %s | rc=%s | stdout: \n%s\n\n\t\t\t\tstderr: %s" % \
                    (hostname, caption, duration,
                     result.get('rc', 0), stdout, stderr)

            if len(stdout) > 0:
                return "%s | %s | %s | rc=%s | stdout: \n%s\n" % \
                    (hostname, caption, duration, result.get('rc', 0), stdout)

            return "%s | %s | %s | rc=%s | no stdout" % \
                (hostname, caption, duration, result.get('rc', 0))

        return "%s | %s | %s | rc=%s" % (hostname, caption, duration, result.get('rc', 0))

    def v2_playbook_on_task_start(self, task, is_conditional):
        parentTask = task.get_first_parent_include()
        if parentTask is not None:
            sectionName = task._role.get_name()
            if parentTask.action.endswith('tasks'):
                sectionName = os.path.splitext(os.path.basename(task.get_path()))[0]
            self._open_section("  ↳ {} : {}".format(sectionName, task.name))
        else:
            self._open_section(task.get_name(), task.get_path())

    def _open_section(self, section_name, path=None):
        self.task_started = datetime.now()

        prefix = ''
        ts = self.task_started.strftime("%H:%M:%S")

        if self._display.verbosity > 1:
            if path:
                self._emit_line("[{}]: {}".format(ts, path))
        self.task_start_preamble = "[{}]{} {} ...".format(ts, prefix, section_name)
        sys.stdout.write(self.task_start_preamble)

    def v2_playbook_on_handler_task_start(self, task):
        self._emit_line("triggering handler | %s " % task.get_name().strip())

    def v2_runner_on_failed(self, result, ignore_errors=False):
        duration = self._get_duration()
        host_string = self._host_string(result)

        if 'exception' in result._result:
            exception_message = "An exception occurred during task execution."
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = exception_message + \
                    "To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = exception_message + \
                    "The full traceback is:\n" + \
                    result._result['exception'].replace('\n', '')

                self._emit_line(msg, color=C.COLOR_ERROR)

        self._emit_line("%s | FAILED | %s" %
                        (host_string,
                         duration), color=C.COLOR_ERROR)
        self._emit_line(deep_serialize(result._result), color=C.COLOR_ERROR)

    def v2_on_file_diff(self, result):

        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        self._emit_line(diff)

        elif 'diff' in result._result and \
                result._result['diff'] and \
                result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self._emit_line(diff)

    @staticmethod
    def _host_string(result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        if delegated_vars:
            host_string = "%s -> %s" % (
                result._host.get_name(), delegated_vars['ansible_host'])
        else:
            host_string = result._host.get_name()

        return host_string

    def v2_runner_on_ok(self, result):
        duration = self._get_duration()

        self._clean_results(result._result, result._task.action)

        host_string = self._host_string(result)

        self._clean_results(result._result, result._task.action)

        if result._task.action in ('include', 'include_role', 'include_tasks'):
            sys.stdout.write("\b\b\b\b ")
            if result._task.action in ('include', 'include_role'):
                sys.stdout.write("    \n")
            return

        msg, color = self._changed_or_not(result._result, host_string)

        if result._task.loop and self._display.verbosity > 0 and 'results' in result._result:
            for item in result._result['results']:
                msg, color = self._changed_or_not(item, host_string)
                item_msg = "%s - item=%s" % (msg, self._get_item(item))
                self._emit_line("%s | %s" %
                                (item_msg, duration), color=color)
        else:
            self._emit_line("%s | %s" %
                            (msg, duration), color=color)
        self._handle_warnings(result._result)

        if ((self._display.verbosity > 0 or '_ansible_verbose_always' in result._result)
                and not '_ansible_verbose_override' in result._result):
            self._emit_line(deep_serialize(result._result), color=color)

        result._preamble = self.task_start_preamble

    @staticmethod
    def _changed_or_not(result, host_string):
        if result.get('changed', False):
            msg = "%s | CHANGED" % host_string
            color = C.COLOR_CHANGED
        else:
            msg = "%s | SUCCESS" % host_string
            color = C.COLOR_OK

        return [msg, color]

    def _emit_line(self, lines, color=C.COLOR_OK):

        if self.task_start_preamble is None:
            self._open_section("system")

        if self.task_start_preamble.endswith(" ..."):
            sys.stdout.write("\b\b\b\b | ")
            self.task_start_preamble = " "

        for line in lines.splitlines():
            self._display.display(line, color=color)

    def v2_runner_on_unreachable(self, result):
        self._emit_line('{} | UNREACHABLE!: {}'.format(
            self._host_string(result), result._result.get('msg', '')), color=C.COLOR_CHANGED)

    def v2_runner_on_skipped(self, result):
        duration = self._get_duration()

        self._emit_line("%s | SKIPPED | %s" %
                        (self._host_string(result), duration), color=C.COLOR_SKIP)

    def v2_playbook_on_include(self, included_file):
        if self.task_start_preamble.endswith(" ..."):
            self.task_start_preamble = " "
            msg = '| {} | {} | {}'.format(
                ", ".join([h.name for h in included_file._hosts]),
                'INCLUDED',
                os.path.basename(included_file._filename))
            self._display.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_stats(self, stats):
        self._open_section("system")
        self._emit_line("-- Play recap --")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._emit_line(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)))

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.task_started = datetime.now()
        self.task_start_preamble = None
        # python2 only
        try:
            reload(sys).setdefaultencoding('utf8')
        # pylint: disable=W0702
        except:
            pass


if __name__ == '__main__':
    unittest.main()
