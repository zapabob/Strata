"""Read-only packaged shell/Host identity and Control-owner/Prism process checks."""
from __future__ import annotations

import argparse
from common import *


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell', type=int)
    parser.add_argument('--child', type=int)
    parser.add_argument('--app', type=Path)
    parser.add_argument('--home', type=Path)
    parser.add_argument('--port', type=int)
    parser.add_argument('--model', type=Path)
    args = parser.parse_args()
    if args.shell is None:
        print(json.dumps(dict(processCounts=process_counts(), resourceBlockers=blockers(resources()))))
        return
    require(args.app is not None and args.home is not None, 'Explicit app and isolated home required')
    expected = load(OUT / 'qualified-payload.json')
    shell = psutil.Process(args.shell)
    require(Path(shell.exe()).resolve() == (args.app / 'strata-desktop.exe').resolve(), 'Wrong shell path')
    require(sha(Path(shell.exe())) == expected['strata-desktop.exe'], 'Wrong shell hash')
    hosts = [p for p in shell.children() if Path(p.exe()).name.lower() == 'node.exe']
    require(len(hosts) == 1, 'Expected one packaged Host')
    host = hosts[0]
    require(Path(host.exe()).resolve() == (args.app / 'node/node.exe').resolve(), 'Wrong Host executable')
    require(sha(Path(host.exe())) == expected['node/node.exe'], 'Wrong Host digest')
    command = host.cmdline()
    require(any(Path(arg).resolve() == (args.app / 'host/server/index.mjs').resolve() for arg in command if arg.endswith('index.mjs')), 'Host source is not packaged')
    env = host.environ()
    require(Path(env.get('STRATA_HOME', '')).resolve() == args.home.resolve(), 'Host home is not isolated')
    require('isolate-host-home.mjs' in env.get('NODE_OPTIONS', ''), 'Homedir preload absent')
    require(host.create_time() >= shell.create_time(), 'Host lifetime differs')
    if args.child is None:
        print(json.dumps(dict(owned=True, packagedShellAndHost=True, homeIsolated=True)))
        return
    child = psutil.Process(args.child)
    if args.model:
        require(shell in child.parents(), 'Prism is not shell-owned')
        require(sha(Path(child.exe())) == PRISM_EXE_SHA, 'Prism digest differs')
        command = child.cmdline()
        def value(flag: str) -> str | None:
            return command[command.index(flag) + 1] if flag in command and command.index(flag) + 1 < len(command) else None
        require(Path(value('-m') or '').resolve() == args.model.resolve(), 'Prism model differs')
        require(all(value(k) == v for k, v in [('-c', '98304'), ('-ctk', 'q8_0'), ('-ctv', 'q8_0'), ('-fa', 'on'), ('-np', '1')]), 'Prism settings differ')
        require(value('--spec-type') in (None, 'none'), 'Unexpected speculation')
        require(any(c.status == psutil.CONN_LISTEN and c.laddr.ip == '127.0.0.1' and c.laddr.port == args.port for c in child.net_connections(kind='tcp')), 'Prism listener not owned')
    else:
        require(sha(Path(child.exe())) == staged()['engineSHA256'], 'Native digest differs')
        owners = []
        for parent in child.parents():
            command = parent.cmdline()
            if '--die-with-pid' in command:
                require(command[command.index('--die-with-pid') + 1] == str(host.pid), 'Control owner bound to different Host')
                require('--die-with-token' in command, 'Creation token absent')
                owners.append(parent)
        require(len(owners) == 1, 'Unique lifetime-bound Control owner required')
        command = child.cmdline()
        require(all(flag in command and command.index(flag) + 1 < len(command) and command[command.index(flag) + 1] == value for flag, value in [('--max-context', '4096'), ('--prefill', '512'), ('--expert-slots', '5'), ('--mtp', '2'), ('--cache-type-k', 'f32'), ('--cache-type-v', 'f32'), ('--q36-memory', 'bounded-experts-v1')]), 'Native argv differs')
        require('--private-conversation-cache' in command, 'Private owner cache absent')
    require(child.create_time() >= host.create_time(), 'Runtime lifetime differs')
    print(json.dumps(dict(owned=True, packagedShellAndHost=True, actualSettingsMatched=True, homeIsolated=True)))


if __name__ == '__main__':
    main()
