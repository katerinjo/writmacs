from expand import expand

simple_html = {
    'Hello, %em{world}!': 'Hello, <em>world</em>!',
}

for writ in simple_html.keys():
    correct = simple_html[writ]
    actual = expand(writ, 'html')[0]
    message = f"""Failed simple HTML.
    Given:
{writ}
    should become:
{correct}
    but instead we got:
{actual}
"""
    assert actual == correct, message

print('All tests passed.')
