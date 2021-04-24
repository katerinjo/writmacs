"""
Basic classes/types, constants, and helper functions.
"""


from pathlib import Path
import re
from typing import TypeVar, Sequence, Mapping, Callable, Any, Tuple


TARGETS = set(['html', 'md', 'txt']) # TODO: should this be an enum?
LETTERS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

keymap_cache = {}
    # currently not very cachey, TODO: lazier loading or something
snippet_cache = {}

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


# Types:

class Keymap:

    def __init__(self, mapping):
        self.mapping = mapping
        self.hints = set()
        for in_txt in mapping.keys():
            for depth in range(1, len(in_txt)):
                self.hints.add(in_txt[:depth])


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


Builder = Sequence[TypeVar('S', str, Token)]
Forest = Sequence[TypeVar('T', str, Node)]
Metadata = dict
# TODO: "TextMod" suggests analogous return type to BuilderMod
#       That's confusing, come up with better names.
TextMod = Callable[[str], str]
BuilderMod = Callable[[Builder], Tuple[Builder, Metadata]]
Macro = Callable[[Sequence[Builder], Metadata], Tuple[Builder, Metadata]]


#   Loading User-Configured Data:

def unescape(string: str) -> str:
    """
    Interpret and interpolate Python backslash characters in unicode
    string.
    """
    string = (string.replace(r'\t', '\t')
        .replace(r'\b', '\b')
        .replace(r'\n', '\n')
        .replace(r'\r', '\r')
        .replace(r'\f', '\f')
        .replace(r"\'", "'")
        .replace(r'\"', '"')
        .replace('\\\\', '\\'))
    def repl(match):
        return chr(int(match.group(1), 16))
    string = re.sub(r'\\u(.{4})', repl, string)
    string = re.sub(r'\\U(.{8})', repl, string)
    return string


def load_unicode_tsv(path: Path) -> list:
    """
    Load tab-separated value file given by path, escaping backslash
    characters.
    """
    raw = path.read_text()
    lines = [
        ln for ln in raw.split('\n')
        if not ln.startswith('#') and '\t' in ln
    ]
    rows = [ln.split('\t') for ln in lines]
    unicode_rows = []
    for row in rows:
        unicode_rows.append([unescape(field) for field in row])
    return unicode_rows


def load_unicode_mapping(path: Path, alias_sep: str = None) -> dict:
    """
    Load a mapping from str to str from a file, escaping backslash
    characters.
    """
    'path , str? -> {str -> str}'
    rows = load_unicode_tsv(path)
    mapping = {}
    for row in rows:
        before, after, *__ = row
        aliases = before.split(alias_sep)
        for alias in aliases:
            mapping[alias] = after
    return mapping


def load_keymap(name: str) -> Keymap:
    """
    Load a keymap from the user's configuration.
    """
    keymap_dict = {}
    rows = load_unicode_tsv(KEYMAPS_DIR / f'{name}.tsv')
    for fields in rows:
        if len(fields) < 2:
            continue
        keymap_dict[fields[0]] = fields[1]
    return Keymap(keymap_dict)


def load_all_mappings(parent_dir: Path, alias_sep: str = None) -> dict:
    """
    Load unicode mappings from all tab-separated value files in a given
    directory.
    """
    mapping = {}
    for tsv in parent_dir.iterdir():
        new_map = load_unicode_mapping(tsv, alias_sep)
        mapping.update(new_map)
    return mapping


def load_snippets() -> Mapping[str, str]:
    """Load all user snippets."""
    return load_all_mappings(SNIPPETS_DIR, alias_sep=',')


def load_keymap(name: str) -> Keymap:
    """Load up a particular Keymap by name."""
    '-> keymap'
    return Keymap(load_unicode_mapping(KEYMAPS_DIR / f'{name}.tsv'))


#   Macro Makers:

def simple_macro(
        trans_fun: Callable[[Builder], Tuple[Builder, Metadata]]) -> Macro:
    """Create a macro that uses one function in all cases."""
    def fun(fields, _):
        builder = []
        return trans_fun(fields[-1])
    return fun


def chop_mapping(aliases2val: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Convert a dict whose keys are comma-separated aliases into a dict
    in which each alias is now a key by itself.

    Example: {'asterisk,star': '*'} -> {'asterisk': '*', 'star': '*'}
    """
    key2val = {}
    for aliases, val in aliases2val.items():
        for alias in aliases:
            key2val[alias] = val
    return key2val


# TODO: Would it make more sense to concatenate extra arguments instead
#       of omitting them?
def multi_macro(format2fun: Mapping[str, BuilderMod]) -> Macro:
    """
    Create a Macro that uses different BuilderMod functions depending on
    target format. Produced Macros only use the last argument given,
    all others will be ignored.
    """
    format2fun = chop_mapping(format2fun)
    def fun(fields, metadata):
        # when in doubt do nothing
        if not metadata['target'] in format2fun:
            return fields[-1], {}
        return format2fun[metadata['target']](fields[-1])
    return fun


#   Builder Modifier Makers:

def keymapper(keymap_name: str) -> BuilderMod:
    """
    Given the name of a Keymap, produce a function that applies the
    Keymap to lists of strings.
    """
    if keymap_name not in keymap_cache:
        keymap_cache[keymap_name] = load_keymap(keymap_name)
    keymap = keymap_cache[keymap_name]
    def fun(chunks):
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


def taggifier(tag: str, **kwargs) -> BuilderMod:
    """
    Create a Builder Modifier that wraps the text in HTML tags.

    The tag name is mandatory. Attributes can be added as keyword
    arguments. All attributes are forced to be lowercase so you can
    avoid name collisions by capitalizing words like "class".
    """
    def out_fun(builder):
        prefix_builder = ['<' + tag]
        for k, v in kwargs.items():
            prefix_builder.append(f' {k.lower()}="{v}"')
        prefix_builder.append('>')
        prefix = Token(''.join(prefix_builder))
        suffix = Token(f'</{tag}>')
        return [prefix, *builder, suffix], {}
    return out_fun


def wrapper(prefix: str, suffix: str = None) -> BuilderMod:
    """
    Create a Builder Modifier that wraps text with a string prefix and
    suffix.

    If only one string is given, the suffix is made identical. To omit
    a prefix or suffix entirely, just use an empty string.
    """
    if suffix is None:
        suffix = prefix
    def fun(builder):
        return [Token(prefix), *builder, Token(suffix)], {}
    return fun

