from writmacs import expand

# Given this input, expect this output

all_cases = {
    'html': {
        'Hello, %em{world}!': 'Hello, <em>world</em>!',

        'monospaced': 'monospaced',

        '<p>Hello,</p>\n<p>%rot{upside-down text}!</p>': (
            '<p>Hello,</p>\n<p>ʇxǝʇ uʍop-ǝpᴉsdn!</p>'
        ),

        '%sparkly(sparkly)': '✧⭒͙°sparkly✧ﾟ☆',

        '%underlined{underlined}': (
            '<span class="underlined">underlined</span>'
        ),
    },
    'md': {
        'the %smallcaps{smallest of Caps}': 'the sᴍᴀʟʟᴇsᴛ ᴏғ Cᴀᴘs',
    },
    'txt': {
        'the %smallcaps{smallest of Caps}': 'the sᴍᴀʟʟᴇsᴛ ᴏғ Cᴀᴘs',

        '%rot(upside-down text!)': '¡ʇxǝʇ uʍop-ǝpᴉsdn',

        '%rot(¡ʇxǝʇ uʍop-ǝpᴉsdn)': 'upside-down text!',
    },
}

for target, cases in all_cases.items():
    for writ in cases.keys():
        correct = cases[writ]
        actual = expand(writ, {'target': target})[0]
        message = f"""Failed {target}.
    Given:
{writ}
    should become:
{correct}
    but instead we got:
{actual}
"""
        assert actual == correct, message

# Non-deterministic cases

### Studly

studly = expand('%studly(Ievan Polkka)')[0]

assert studly.lower() == 'ievan polkka', (
    f"Studly mutates underlying alphabet: {studly}"
)
assert studly[0] == 'i', (
    f"Studly case failed to render I as lowercase: {studly}"
)
assert studly[8] == 'L', (
    f"Studly case failed to render L as capital: {studly}"
)

# Breaking the rules must fail successfully

try:
    expand('%snippet(9ece6796-b989-4137-b2d1-38d969f82c2a)')
    raise Exception("Undefined snippet attempted without error.")
except:
    pass



# Nothing broke, we succeeded

print('All tests passed.')
