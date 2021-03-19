'''
targets:
    html (accessible, for websites)
    markdown (hacky, mainly for instant messaging)
    text (very hacky, for terminals and other oppressive environments)
    (if you want non-hacky markdown, just use pandoc on the html)
'''

from pathlib import Path
import re

TARGETS = set(['html', 'md', 'txt'])
LETTERS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

keymap_cache = {}
snippet_cache = {} # currently not very cachey, TODO: lazier loading or something

config_dir = Path.home() / '.config'
if not config_dir.exists():
    config_dir.mkdir()
writmacs_dir = config_dir / 'writmacs'
if not writmacs_dir.exists():
    writmacs_dir.mkdir()
SNIPPETS_DIR = writmacs_dir / 'snippets'
if not SNIPPETS_DIR.exists():
    SNIPPETS_DIR.mkdir()
KEYMAPS_DIR = writmacs_dir / 'keymaps'
if not KEYMAPS_DIR.exists():
    KEYMAPS_DIR.mkdir()

# classes:

class Keymap:
    def __init__(self, mapping):
        self.mapping = mapping
        self.hints = set()
        for in_txt in mapping.keys():
            for depth in range(1, len(in_txt)):
                self.hints.add(in_txt[:depth])

class Token:
    def __init__(self, content):
        self.content = content

    def __str__(self):
        return str(self.content)

# loading configured data:

def unescape(string):
    'str with backslash escapes -> str with unicode interpolated'
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

def load_unicode_tsv(path):
    'path -> [[str]]'
    raw = path.read_text()
    lines = [ln for ln in raw.split('\n') if not ln.startswith('#') and '\t' in ln]
    rows = [ln.split('\t') for ln in lines]
    unicode_rows = []
    for row in rows:
        unicode_rows.append([unescape(field) for field in row])
    return unicode_rows

def load_unicode_mapping(path, alias_sep=None):
    'path , str? -> {str -> str}'
    rows = load_unicode_tsv(path)
    mapping = {}
    for row in rows:
        before, after, *__ = row
        aliases = before.split(alias_sep)
        for alias in aliases:
            mapping[alias] = after
    return mapping

def load_keymap(name):
    'str -> keymap'
    keymap_dict = {}
    rows = load_unicode_tsv(proj_dir / f'keymaps/{name}.tsv')
    for fields in rows:
        if len(fields) < 2:
            continue
        keymap_dict[fields[0]] = fields[1]
    return Keymap(keymap_dict)

def load_all_mappings(parent_dir, alias_sep=None):
    'path , str? -> {str -> str}'
    mapping = {}
    for tsv in parent_dir.iterdir():
        new_map = load_unicode_mapping(tsv, alias_sep)
        mapping.update(new_map)
    return mapping

def load_snippets():
    '-> {str -> str}'
    return load_all_mappings(SNIPPETS_DIR, alias_sep=',')

def load_keymap(name):
    '-> keymap'
    return Keymap(load_unicode_mapping(KEYMAPS_DIR / f'{name}.tsv'))

# macro makers:

def simple_macro(trans_fun):
    '(builder -> [builder, meta]) -> (fields , metadata -> builder)'
    def fun(fields, _):
        builder = []
        return trans_fun(fields[-1])
    return fun

def chop_mapping(aliases2val):
    key2val = {}
    for aliases, val in aliases2val.items():
        for alias in aliases:
            key2val[alias] = val
    return key2val

def multi_macro(format2fun):
    '{str -> (builder -> [builder, meta])} -> (fields , metadata -> [str])'
    format2fun = chop_mapping(format2fun)
    def fun(fields, metadata):
        # when in doubt do nothing
        if not metadata['target'] in format2fun:
            return fields[-1], {}
        return format2fun[metadata['target']](fields[-1])
    return fun

# macro helpers / text transformers

def keymapper(keymap_name):
    'keymap name str -> (builder -> [builder, meta])'
    if keymap_name not in keymap_cache:
        keymap_cache[keymap_name] = load_keymap(keymap_name)
    keymap = keymap_cache[keymap_name]
    def fun(chunks):
        builder = []
        for chunk in chunks:
            if not type(chunk) is str:
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
            return chunks, {}
    return fun

def taggifier(tag, **kwargs):
    'str -> (builder -> [builder, meta])'
    def out_fun(builder):
        prefix_builder = ['<' + tag]
        for k, v in kwargs.items():
            prefix_builder.append(f' {k.lower()}="{v}"')
        prefix_builder.append('>')
        prefix = Token(''.join(prefix_builder))
        suffix = Token(f'</{tag}>')
        return [prefix, *builder, suffix], {}
    return out_fun

def wrapper(prefix, suffix=None):
    'str , str? -> (builder -> [builder, meta])'
    if suffix is None:
        suffix = prefix
    def fun(builder):
        return [Token(prefix), *builder, Token(suffix)], {}
    return fun

