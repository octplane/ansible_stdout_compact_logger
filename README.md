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

## Test the logger

- clone this repository
```
ansible-playbook test-1.yml
```
- to run the tests, call `python2.6 callbacks/anstomlog.py`

## License

MIT, see LICENSE file.