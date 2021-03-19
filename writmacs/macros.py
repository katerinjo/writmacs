# import os
# from pathlib import Path
from random import random, randint
from util import *

# home = Path.home()
# this_file = Path(os.path.realpath(__file__))
# file_dir = this_file.parent
# trans_dir = file_dir / 'transforms'

# [content], {target} -> builder
emphasis = multi_macro({
            ('md', 'txt'): wrapper('*'),
            ('html',): taggifier('em')
        })

def apply_keymap(fields, _):
    '[keymap name str, content builder] -> builder'
    keymap, builder = fields
    return keymapper(keymap)(builder)

def monospace(fields, metadata):
    '[content], {target} -> builder'
    target = metadata['target']
    if target == 'md':
        return wrapper('`')(fields[0])
    if target == 'html':
        multiline = False
        for chunk in fields[0]:
            if type(chunk) is str and '\n' in chunk:
                multiline = True
                break
        if multiline:
            tag = 'pre'
        else:
            tag = 'code'
        return taggifier(tag)(fields[0])
    if target == 'txt':
        return keymapper('monospace')(fields[0])

def rotate(fields, _):
    '[content] -> builder'
    content = fields[0]
    flipped_letters = keymapper('rotated')(content)
    rev_content = reversed(flipped_letters)
    return rev_content, {}

def section(fields, metadata):
    '[title, body] -> builder'
    target = metadata['target']
    title, body = fields
    if target in ['md', 'txt']:
        return ['## ', *title, '\n\n', *body], {}
    else:
        return taggifier('section')([*taggifier('h3')(title), *body]), {}

# [content], {target} -> builder
smallcaps = multi_macro(
    {
        ('md', 'txt'): keymapper('smallcaps'),
        ('html',): taggifier('span', Class='smallcaps')
    })

def snippet(fields, metadata):
    snip_name = fields[0]
    if snip_name not in snippet_cache:
        snippet_cache.update(load_snippets())
    if snip_name not in snippet_cache:
        return snip_name
    elif metadata['target'] == 'md': # working with markdown, need escapes
        snippet = (snippet_cache[snip_name]
                .replace('\\', r'\\')
                .replace('_', r'\_')
                .replace('*', r'\*'))
        return snippet, {}
    else:
        return snippet_cache[snip_name], {}

def title(fields, metadata):
    return [], {'title': fields[0]}

def studly(fields, _):
    def studly_str(text):
        if not type(text) is str:
            return text
        builder = []
        for character in text:
            if character in 'Ii':
                builder.append('i')
            elif character in 'Ll':
                builder.append('L')
            elif character in LETTERS:
                if random() < 0.4:
                    builder.append(character.upper())
                else:
                    builder.append(character.lower())
            else:
                builder.append(character)
        return ''.join(builder)
    return [studly_str(chunk) for chunk in fields[0]], {}

def underline(fields, metadata):
    content = fields[0]
    target = metadata['target']
    if target == 'html':
        return taggifier('span', Class='underlined')(content)
    UNDERLINABLE = set(
            '0123456789ABCDEFGHIJKLMNOPRSTUVWXYZabcdefhiklmnorstuvwxz'
            + 'ĉĈĥĤŭŬêÊĴĜ().?!:-\'"+=*&^%$#@`~'
            )
    UNDERLINE = chr(818)
    def underline_str(text):
        if not type(text) is str:
            return text
        builder = []
        for character in text:
            if character == ' ':
                builder.append('_')
            else:
                builder.append(character)
                if character in UNDERLINABLE:
                    builder.append(UNDERLINE)
        return ''.join(builder)

    builder = []
    for chunk in content:
        builder.append(underline_str(chunk))
    return builder, {}


sparkle = wrapper('✧⭒͙°', '✧ﾟ☆')

def zalgo(fields, _):
    builder = []
    for chunk in fields[0]:
        if type(chunk) is str:
            for character in chunk:
                builder.append(character)
                builder.extend([chr(randint(768, 866)) for n in range(8)])
        else:
            builder.append(chunk)
    return builder, {}

keymaps = [path.stem for path in KEYMAPS_DIR.iterdir()]

expanders = {
        **{name:keymapper(name) for name in keymaps},
        'em': emphasis,
        'map': apply_keymap,
        'mono': monospace,
        'monospace': monospace,
        'rot': rotate,
        'rotate': rotate,
        'section': section,
        'smallcap': smallcaps,
        'smallcaps': smallcaps,
        'snip': snippet,
        'snippet': snippet,
        'sparkle': sparkle,
        'studly': studly,
        'title': title,
        'under': underline,
        'underline': underline,
        'void': zalgo,
        'zalgo': zalgo,
        }
organizers = {}
contextualizers = {}
