"""
Basic classes/types, constants, and helper functions.
"""


from pathlib import Path
import pkgutil
import re
from typing import *


### Constants

TARGETS = set(['html', 'md', 'txt']) # TODO: should this be an enum?
LETTERS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

CONFIG_DIR = Path.home() / '.config'
if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir()
WRITMACS_DIR = CONFIG_DIR / 'writmacs'
if not WRITMACS_DIR.exists():
    WRITMACS_DIR.mkdir()
SNIPPETS_DIR = WRITMACS_DIR / 'snippets'
if not SNIPPETS_DIR.exists():
    SNIPPETS_DIR.mkdir()
KEYMAPS_DIR = WRITMACS_DIR / 'keymaps'
if not KEYMAPS_DIR.exists():
    KEYMAPS_DIR.mkdir()

# (constants continued at end of file)

### Types:

class Keymap:

    def __init__(self, mapping):
        self.mapping = mapping
        self.hints = set()
        for in_txt in mapping.keys():
            for depth in range(1, len(in_txt)):
                self.hints.add(in_txt[:depth])


class DB:

    def __init__(self, fetch):
        self.fetch = fetch
        self.cache = {}

    def __getitem__(self, key):
        if key in self.cache:
            return self.cache[key]

        self.cache.update(self.fetch(key))
        if key in self.cache:
            return self.cache[key]

        return None

    def __contains__(self, key):
        return self[key] is not None


class Token:

    def __init__(self, content, fun=None):
        self.content = content
        self.fun = fun

    def __str__(self):
        if self.fun is None:
            return str(self.content)
        return str(fun(self.content))


class Node:
    def __init__(self, name, children, child_names={}):
        self.name = name
        self.children = children
        self.fields = child_names

    def __getitem__(self, key):
        if type(key) is int:
            return self.children[key]
        try:
            return self.children[self.fields[key]]
        except:
            raise KeyError

    def to_str(self, depth=0):
        builder = ['\n«' + '-' * depth + f':{self.name}:']
        for ix in range(len(self.children)):
            builder.extend(['\n' + '-' * depth + f'[{ix}]\n'])
            for chunk in self.children[ix]:
                if type(chunk) is str:
                    builder.append(chunk)
                else:
                    builder.append(chunk.to_str(depth+1))
        builder.append('»')
        return ''.join(builder)

    def __str__(self):
        return self.to_str()


Builder = Sequence[Union[str, Token]]
Forest = Sequence[Union[str, Node]]
Metadata = dict
# TODO: "TextMod" suggests analogous return type to BuilderMod
#       Come up with better names.
TextMod = Callable[[str], str]
# BuilderMod = Callable[[Builder], Tuple[Builder, Metadata]]
Macro = Callable[[Sequence[Builder], Metadata], Tuple[Builder, Metadata]]


### Loading User-Configured Data:

def unescape(string: str) -> str:
    """
    Interpret and interpolate Python backslash characters in unicode
    string.
    """
    string = (string
        .replace(r'\t', '\t')
        .replace(r'\b', '\b')
        .replace(r'\n', '\n')
        .replace(r'\r', '\r')
        .replace(r'\f', '\f')
    )
    string = re.sub(r'\\(.)', r'\1', string)

    def repl(match):
        return chr(int(match.group(1), 16))
    string = re.sub(r'\\u(.{4})', repl, string)
    string = re.sub(r'\\U(.{8})', repl, string)
    return string


def load_unicode_tsv(tsv: str) -> list:
    """
    Load tab-separated value file given by path, escaping backslash
    characters.
    """
    lines = [
        ln for ln in tsv.split('\n')
        if not ln.startswith('#') and '\t' in ln
    ]
    rows = [ln.split('\t') for ln in lines]
    unicode_rows = []
    for row in rows:
        unicode_rows.append([unescape(field) for field in row])
    return unicode_rows


def rows2mapping(rows, alias_sep: str = ',') -> dict:
    mapping = {}
    for row in rows:
        before, after, *__ = row
        aliases = before.split(alias_sep)
        for alias in aliases:
            mapping[alias] = after
    return mapping

def load_path_mapping(path: Path, alias_sep: str = None) -> dict:
    """
    Load a mapping from str to str from a file, escaping backslash
    characters.
    """
    rows = load_unicode_tsv(path.read_text())
    return rows2mapping(rows)


def load_all_path_mappings(parent_dir: Path, alias_sep: str = None) -> dict:
    """
    Load unicode mappings from all tab-separated value files in a given
    directory.
    """
    mapping = {}
    for tsv in parent_dir.iterdir():
        new_map = load_path_mapping(tsv, alias_sep)
        mapping.update(new_map)
    return mapping


def load_snippets() -> Mapping[str, str]:
    """Load all user snippets."""
    return load_all_path_mappings(SNIPPETS_DIR, alias_sep=',')


def load_keymap(name: str) -> Keymap:
    """Load up a particular Keymap by name."""
    '-> keymap'

    users_version = KEYMAPS_DIR / f'{name}.tsv'
    if users_version.exists():
        return Keymap(load_path_mapping(users_version))

    default_res = pkgutil.get_data(__name__, f'keymaps/{name}.tsv')
    if default_res is not None:
        return Keymap(rows2mapping(load_unicode_tsv(default_res.decode())))

    raise KeyError('Keymap file not found: ' + name)


### Macro Makers:

def simple_macro(
        trans_fun: Callable[[Builder], Tuple[Builder, Metadata]]) -> Macro:
    """Create a macro that uses one function in all cases."""
    def fun(fields, _):
        builder = []
        return trans_fun(fields[-1])
    return fun


def chop_mapping(aliases2val: Mapping[Sequence[str], Any]) -> Mapping[str, Any]:
    """
    Convert a dict whose keys are sequences of aliases into a dict
    in which each alias is now a key by itself.

    Example: {('asterisk', 'star'): '*'} -> {'asterisk': '*', 'star': '*'}
    """
    key2val = {}
    for aliases, val in aliases2val.items():
        for alias in aliases:
            key2val[alias] = val
    return key2val


# TODO: Would it make more sense to concatenate extra arguments instead
#       of omitting them?
def multi_macro(formats2fun: Mapping[Sequence[str], Macro]) -> Macro:
    """
    Create a Macro that uses different Macro functions depending on
    target format. Produced Macros only use the last argument given,
    all others will be ignored.
    """
    format2fun = chop_mapping(formats2fun)
    def fun(fields, metadata):
        # when in doubt do nothing
        if not metadata['target'] in format2fun:
            return fields[-1], {}
        return format2fun[metadata['target']](fields, {})
    return fun


def keymapper(keymap_name: str) -> Macro:
    """
    Given the name of a Keymap, produce a function that applies the
    Keymap to lists of strings.
    """
    # if keymap_name not in KEYMAP_CACHE:
    #     KEYMAP_CACHE[keymap_name] = load_keymap(keymap_name)
    keymap = KEYMAP_CACHE[keymap_name]
    def fun(fields, __):
        chunks = fields[0]
        builder = []
        for txt in chunks:
            if not type(txt) is str:
                builder.append(chunk)
                continue
            left = 0
            right = 1
            while left < len(txt):
                valid_answer = right
                while right <= len(txt):
                    candidate = txt[left:right]
                    if candidate in keymap.mapping:
                        valid_answer = right
                    if candidate in keymap.hints:
                        right += 1
                    else:
                        break
                builder.append(
                        keymap.mapping.get(
                            txt[left:valid_answer],
                            txt[left:valid_answer]
                            ))
                left = valid_answer
                right = left + 1
        return builder, {}
    return fun


def taggifier(tag: str, **kwargs) -> Macro:
    """
    Create a Builder Modifier that wraps the text in HTML tags.

    The tag name is mandatory. Attributes can be added as keyword
    arguments. All attributes are forced to be lowercase so you can
    avoid name collisions by capitalizing words like "class".
    """
    def out_fun(fields, __):
        builder = fields[0]
        prefix_builder = ['<' + tag]
        for k, v in kwargs.items():
            prefix_builder.append(f' {k.lower()}="{v}"')
        prefix_builder.append('>')
        prefix = Token(''.join(prefix_builder))
        suffix = Token(f'</{tag}>')
        return [prefix, *builder, suffix], {}
    return out_fun


def wrapper(prefix: str, suffix: str = None) -> Macro:
    """
    Create a Builder Modifier that wraps text with a string prefix and
    suffix.

    If only one string is given, the suffix is made identical. To omit
    a prefix or suffix entirely, just use an empty string.
    """
    if suffix is None:
        suffix = prefix
    def fun(fields, __):
        builder = fields[0]
        assert type(builder[0]) is str, f'DEBUG!! got: {builder}'
        return [Token(prefix), *builder, Token(suffix)], {}
    return fun


### Constants Again Because Python's Limited Hoisting Can't Handle This

KEYMAP_CACHE = DB(lambda k: {k: load_keymap(k)})

# load all snippets regardless of request
# because discrimination unimplemented
SNIPPET_CACHE = DB(lambda _: load_snippets)


