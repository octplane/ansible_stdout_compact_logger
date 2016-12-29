# Ansible Stdout Compact Logger

## Installation

- put somewhere on your disk
- add `callback_plugins` settings in your `[defaults]` settings in your ansible configuration
- change stdout_callback to `anstomlog`

cf `ansible.cfg`.

## Features

- one-line display
- displays tasks content in a nice way:
  - ident structs, displays empty arrays, strings
  - put fields on top when available `['rc', 'stdout', 'stderr', 'start', 'end']`
- reverts to standard logger when more than `vv` verbosity

## Sample output

```
[2016-12-29 18:18:01.623233] setup | localhost | SUCCESS | 587ms
[2016-12-29 18:18:01.919534] command | localhost | SUCCESS | 1229.922ms | rc=0
[2016-12-29 18:18:03.036159] command | localhost | FAILED!
{
  - rc: 1
  - stdout: ""
  - stderr: ""
  - start: 2016-12-29 18:18:03.131670
  - end: 2016-12-29 18:18:03.136464
  - cmd: [ false ]
  - _ansible_no_log: False
  - changed: True
  - failed: True
  - delta: 0:00:00.004794
  - invocation: {
    - module_name: command
    - module_args: {
      - creates: None
      - executable: None
      - chdir: None
      - _raw_params: false
      - removes: None
      - warn: True
      - _uses_shell: False
    }
  }
  - stdout_lines: []
  - warnings: []
}
	to retry, use: --limit @test-1.retry
[2016-12-29 18:18:03.150010] -- Play recap --
[2016-12-29 18:18:03.150079] localhost                  : ok=2    changed=1    unreachable=0    failed=1
```

## Test the logger

- clone this repository
```
ansible-playbook test-1.yml
```
- to run the tests, call `python2.6 callbacks/anstomlog.py`

## License

MIT, see LICENSE file.