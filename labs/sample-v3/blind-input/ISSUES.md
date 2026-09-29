# Bug reports

Six bug reports, each with the repository and the commit where the bug is present. Title and body are copied verbatim
from the report (comments are not included).

## n-23

- repository: https://github.com/alexmojaki/pure_eval
- commit with the bug: b5e1617805fbb1e77101de1ad372d2a0d58053ce
- title: TypeError for malformed metaclass example

### Report body (verbatim)

~~~~~~~~
In https://github.com/ipython/ipython/issues/13481, the following example used to show a fatal error in IPython:
```python
class X(type):
    def __prepare__(cls, *args, **kwargs):
        return []
class Y(metaclass=X):
    pass
```

If I try the same example with friendly-traceback, I also get a fatal error, with the following as part of a long traceback:
```
    During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "LOCAL:\pure_eval\core.py", line 445, in group_expressions
    for node, value in expressions:
  File "FRIENDLY:\info_variables.py", line 119, in <genexpr>
    for nodes, obj in group_expressions(
  File "LOCAL:\pure_eval\core.py", line 358, in find_expressions
    value = self[node]
  File "LOCAL:\pure_eval\core.py", line 68, in __getitem__
    self._cache[node] = result = self._handle(node)
  File "LOCAL:\pure_eval\core.py", line 89, in _handle
    return self.names[node.id]
TypeError: list indices must be integers or slices, not str
```

In https://github.com/friendly-traceback/friendly-traceback/commit/276ec1b85f7c5949b0e5d1fb325b30b59b57d9c5, I've guarded against this type of fatal error.

I didn't see any evidence that the IPython crash is caused by pure_eval or an other library of yours, but I thought you might want to know about it - and possibly include some safeguards in pure_eval.
~~~~~~~~

## n-25

- repository: https://github.com/pydantic/pydantic-settings
- commit with the bug: 9b73e924cab136d876907af0c6836dcca09ac35c
- title: Order of alias given in AliasChoices yield different results

### Report body (verbatim)

~~~~~~~~
Versions:

```
pydantic                       2.9.2
pydantic_core                  2.23.4
pydantic-settings              [current main branch so that this fix is present: https://github.com/pydantic/pydantic-settings/pull/400]
```

In the continuation of https://github.com/pydantic/pydantic-settings/issues/406 I've found that  the order of the alias given in `AliasChoices` change the behaviour, which I believe, shouldn't be the case. 

Given the following example:

```python
# test_config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, BaseModel, AliasGenerator, ConfigDict
from typing import List

validation_alias_a = lambda x: AliasChoices(x, x.replace('_','-'))
validation_alias_b = lambda x: AliasChoices(x.replace('_','-'), x)

my_validation_alias = validation_alias_a

class SubModel(BaseModel):
    sub_list: List[str] = Field(
        default_factory=list, description="A list argument",
    )
    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=my_validation_alias)
    )

class MySettings(BaseSettings):
    sub_model: SubModel = Field(
        SubModel(),
    )

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        env_nested_delimiter="__",
        alias_generator=AliasGenerator(validation_alias=my_validation_alias)
    )

settings = MySettings()

print(settings)
```

The following works as expected:

```bash
# python test_config.py --sub-model.sub-list=a,b,c
sub_model=SubModel(sub_list=['a', 'b', 'c'])
```

But if I change the validation_alias:

```python
(...)
my_validation_alias = validation_alias_b
(...)
```

Then the following fails

```bash
# python test_config.py --sub-model.sub-list=a,b,c
Traceback (most recent call last):
  File "./test_config.py", line 30, in <module>
    settings = MySettings()
  File "/usr/local/lib/python3.10/site-packages/pydantic_settings/main.py", line 155, in __init__
    super().__init__(
  File "/usr/local/lib/python3.10/site-packages/pydantic/main.py", line 212, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 1 validation error for MySettings
sub_model.sub-list
  Input should be a valid list [type=list_type, input_value='["a","b","c"]', input_type=str]
    For further information visit https://errors.pydantic.dev/2.9/v/list_type
```

---

In fact, if both of the alias do not include the field name itself (the `x`), for example:

```python
(...)
validation_alias_a = lambda x: AliasChoices(x.replace('_','__'), x.replace('_','-'))
validation_alias_b = lambda x: AliasChoices(x.replace('_','-'), x.replace('_','__'))
(...)
```

then the error is always thrown.

---

Not sure if it's in pydantic or pydantic-settings. But I guess this is a bug?

Note this is not a deal breaker since with the workaround of including `x` as the first alias choice mitigates it.
~~~~~~~~

## n-43

- repository: https://github.com/pytest-dev/iniconfig
- commit with the bug: 6bc5528789498c360577770cbb4bb779134ffce1
- title: Decode error in pytest.ini with chinese characters

### Report body (verbatim)

~~~~~~~~
Reported originally in https://github.com/pytest-dev/pytest/issues/3799 by @edsion1107

@edsion1107 a PR here (with accompanying test) would be welcome!

---

- pytest           3.7.1

pytest.ini:
```python
[pytest]
log_file = pytest.log
log_file_level = INFO
log_file_format = %(asctime)s %(module)s.%(funcName)s %(levelname)s %(message)s
log_cli=true
log_cli_level = WARNING
log_cli_format = %(msecs)d %(filename)s(%(lineno)d) %(levelname)s %(message)s
# 中文
;--basetemp=../results
;--tap-files
;--html=report.html --self-contained-html
```

I have tried  to add Chinese comment ,then this error occurs:
```
Traceback (most recent call last):
  File "C:\Program Files\JetBrains\PyCharm Community Edition 2018.2.1\helpers\pycharm\_jb_pytest_runner.py", line 31, in <module>
    pytest.main(args, plugins_to_load)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 55, in main
    config = _prepareconfig(args, plugins)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 180, in _prepareconfig
    pluginmanager=pluginmanager, args=args
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\hooks.py", line 258, in __call__
    return self._hookexec(self, self._nonwrappers + self._wrappers, kwargs)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\manager.py", line 67, in _hookexec
    return self._inner_hookexec(hook, methods, kwargs)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\manager.py", line 61, in <lambda>
    firstresult=hook.spec_opts.get('firstresult'),
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\callers.py", line 196, in _multicall
    gen.send(outcome)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\helpconfig.py", line 89, in pytest_cmdline_parse
    config = outcome.get_result()
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\callers.py", line 76, in get_result
    raise ex[1].with_traceback(ex[2])
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\pluggy\callers.py", line 180, in _multicall
    res = hook_impl.function(*args)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 612, in pytest_cmdline_parse
    self.parse(args)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 777, in parse
    self._preparse(args, addopts=addopts)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 723, in _preparse
    self._initini(args)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\__init__.py", line 666, in _initini
    rootdir_cmd_arg=ns.rootdir or None,
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\findpaths.py", line 118, in determine_setup
    rootdir, inifile, inicfg = getcfg([ancestor], warnfunc=warnfunc)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\_pytest\config\findpaths.py", line 35, in getcfg
    iniconfig = py.iniconfig.IniConfig(p)
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\py\_vendored_packages\iniconfig.py", line 55, in __init__
    tokens = self._parse(iter(f))
  File "C:\Users\p_jbzhang\.virtualenvs\wecar-tMZRsXDh\lib\site-packages\py\_vendored_packages\iniconfig.py", line 83, in _parse
    for lineno, line in enumerate(line_iter):
UnicodeDecodeError: 'gbk' codec can't decode byte 0xad in position 259: illegal multibyte sequence
```


I tried to fix this error:

```python
# filename: iniconfig.py
# line: 49
class IniConfig(object):
    def __init__(self, path, data=None):
        self.path = str(path)  # convenience
        if data is None:
            # f = open(self.path)     
            # add encoding params 
            f = open(self.path, encoding='utf-8')
            try:
                tokens = self._parse(iter(f))
            finally:
                f.close()
        else:
            tokens = self._parse(data.splitlines(True))
```
~~~~~~~~

## n-46

- repository: https://github.com/rspeer/ordered-set
- commit with the bug: 10ebd5008e60c0c8c3e59be265572f79a6a0f4aa
- title: Pickling then unpickling fails for the empty OrderedSet().

### Report body (verbatim)

~~~~~~~~
The following fails:

``` python
>>> import pickle
>>> from ordered_set import OrderedSet
>>> pickle.loads(pickle.dumps(OrderedSet()))
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/mj/Development/venvs/stackoverflow-2.7/lib/python2.7/site-packages/ordered_set.py", line 126, in __repr__
    if not self:
  File "/Users/mj/Development/venvs/stackoverflow-2.7/lib/python2.7/site-packages/ordered_set.py", line 49, in __len__
    return len(self.items)
AttributeError: 'OrderedSet' object has no attribute 'items'
```

because `OrderedSet.__getstate__` returns an empty list, causing `pickle` to assume you don't want `__setstate__` to be called when loading again.

This can be fixed by using a `__getstate__` that wraps the list in a 1-element tuple:

``` python
def __getstate__(self):
    return (list(self),)

def __setstate__(self, state):
    if isinstance(state, tuple):
        state = state[0]   # new pickle format
    self.__init__(state)    
```

By explicitly testing for a tuple in `__setstate__` previously pickled data can still be loaded.

Also see http://stackoverflow.com/questions/24846605/cannot-pickle-empty-ordered-set
~~~~~~~~

## n-49

- repository: https://github.com/python-trio/trio-websocket
- commit with the bug: ac1c976c2a89c5efc49f9fb02e6d6fabd17f60a8
- title: connection fails on URL without a path component

### Report body (verbatim)

~~~~~~~~
Not sure who's guilty here (kraken's impl or this client) but downgrading to `0.8.1` resolves the problem.
Their [api has been in production for a while](https://docs.kraken.com/websockets/#exampleapi).

Test code:

```python
import trio
import trio_websocket

async def open_ws():
    async with trio_websocket.open_websocket_url(
        'wss://ws.kraken.com',
    ) as ws:
        ...

trio.run(open_ws)
```

On `0.8.1` this yields no output but on `0.9.0` this errors with:

```python
Traceback (most recent call last):
  File "tws_kraken_fail.py", line 10, in <module>
    trio.run(open_ws)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/trio/_core/_run.py", line 1928, in run
    raise runner.main_task_outcome.error
  File "tws_kraken_fail.py", line 5, in open_ws
    async with trio_websocket.open_websocket_url(
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/async_generator/_util.py", line 34, in __aenter__
    return await self._agen.asend(None)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/async_generator/_impl.py", line 366, in step
    return await ANextIter(self._it, start_fn, *args)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/async_generator/_impl.py", line 202, in send
    return self._invoke(self._it.send, value)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/async_generator/_impl.py", line 209, in _invoke
    result = fn(*args)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/trio_websocket/_impl.py", line 124, in open_websocket
    raise DisconnectionTimeout from None
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/trio/_core/_run.py", line 815, in __aexit__
    raise combined_error_from_nursery
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/trio_websocket/_impl.py", line 1182, in _reader_task
    await self._send(self._initial_request)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/trio_websocket/_impl.py", line 1238, in _send
    data = self._wsproto.send(event)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/wsproto/__init__.py", line 35, in send
    data += self.handshake.send(event)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/wsproto/handshake.py", line 88, in send
    data += self._initiate_connection(event)
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/wsproto/handshake.py", line 338, in _initiate_connection
    upgrade = h11.Request(
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/h11/_events.py", line 71, in __init__
    self._validate()
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/h11/_events.py", line 147, in _validate
    validate(request_target_re, self.target, "Illegal target characters")
  File "/home/goodboy/repos/piker/3.8/lib/python3.8/site-packages/h11/_util.py", line 108, in validate
    raise LocalProtocolError(msg)
h11._util.LocalProtocolError: Illegal target characters
```

Please feel free to adjust the issue title, I haven't dug into this at all other then quick looks through the debugger stack.

Underlying issue seems to be the `h11._events.Request.target` is `b''` and it dies inside `.validate()`?
~~~~~~~~

## n-59

- repository: https://github.com/lincolnloop/python-qrcode
- commit with the bug: dd30060df682f38f644be95a316fa5c775fd3464
- title: Generation of image file fails with Python 3

### Report body (verbatim)

~~~~~~~~
Generation of image file with Python 3 triggers `TypeError: must be str, not bytes` exception:

```
$ PYTHONPATH="." python3.4 qrcode/console_scripts.py --help
Usage: qr - Convert stdin (or the first argument) to a QR Code.

When stdout is a tty the QR Code is printed to the terminal and when stdout is
a pipe to a file an image is written. The default image format is PNG.
...
$ PYTHONPATH="." python3.4 qrcode/console_scripts.py text
█████████████████████████████
█████████████████████████████
████ ▄▄▄▄▄ ███▄▄██ ▄▄▄▄▄ ████
████ █   █ █ ▀▄  █ █   █ ████
████ █▄▄▄█ █ ▄█▄ █ █▄▄▄█ ████
████▄▄▄▄▄▄▄█ █▄▀ █▄▄▄▄▄▄▄████
████ ▀▄ ▄ ▄██▄▀█ █▄ ▄  █▀████
████▄▀▄█ ▄▄▄▄█ ▄█▄█▀   ▄█████
█████▄██▄█▄▄ ▀▄ ▀ ▀█▄▄█ ▀████
████ ▄▄▄▄▄ █▀▀ ▀ ▀ ▄█▀ ▄█████
████ █   █ █  ▄█ ██ █ ▀▄█████
████ █▄▄▄█ █▄ ▄▄█▄█▀ █ ██████
████▄▄▄▄▄▄▄█▄▄█▄█▄██▄█▄▄█████
█████████████████████████████
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
$ PYTHONPATH="." python3.4 qrcode/console_scripts.py text > /tmp/image.png
Traceback (most recent call last):
  File "qrcode/console_scripts.py", line 65, in <module>
    main()
  File "qrcode/console_scripts.py", line 61, in main
    img.save(sys.stdout)
  File "/tmp/python-qrcode/qrcode/image/pil.py", line 32, in save
    self._img.save(stream, kind)
  File "/usr/lib64/python3.4/site-packages/PIL/Image.py", line 1685, in save
    save_handler(self, fp, filename)
  File "/usr/lib64/python3.4/site-packages/PIL/PngImagePlugin.py", line 631, in _save
    fp.write(_MAGIC)
TypeError: must be str, not bytes
```

Fix:

```
--- qrcode/console_scripts.py
+++ qrcode/console_scripts.py
@@ -58,7 +58,7 @@
         return

     img = qr.make_image(image_factory=image_factory)
-    img.save(sys.stdout)
+    img.save(sys.stdout.buffer if sys.version_info[0] >= 3 else sys.stdout)


 if __name__ == "__main__":
```
~~~~~~~~
