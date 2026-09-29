import os

import click


def _complete(ctx, args, incomplete):
    return ctx.obj['completions']


@click.group()
@click.pass_context
def entrypoint(ctx):
    pass


@entrypoint.command()
@click.argument('arg', type=click.STRING, autocompletion=_complete)
@click.pass_context
def subcommand(ctx, arg):
    print('arg={}'.format(arg))


os.environ['_TESTCLICK_COMPLETE'] = 'complete'
os.environ['COMP_WORDS'] = 'testclick subcommand '
os.environ['COMP_CWORD'] = '2'
try:
    entrypoint(obj={'completions': ['abc', 'def', 'ghi']}, prog_name='testclick')
except SystemExit:
    pass
