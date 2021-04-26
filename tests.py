from writmacs import expand

### Given this input, expect this output

all_cases = {
    'html': {
        'Hello, %em{world}!': 'Hello, <em>world</em>!',
        '<p>Hello,</p>\n<p>%rot{upside-down text}!</p>': (
            '<p>Hello,</p>\n<p>ʇxǝʇ uʍop-ǝpᴉsdn!</p>'
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
        actual = expand(writ, target)[0]
        message = f"""Failed {target}.
    Given:
{writ}
    should become:
{correct}
    but instead we got:
{actual}
"""
        assert actual == correct, message


### Breaking the rules must fail successfully

try:
    expand('%map(9ece6796-b989-4137-b2d1-38d969f82c2a)')
    raise Exception("Undefined snippet attempted without error.")
except:
    pass



### Nothing broke, we succeeded

print('All tests passed.')
