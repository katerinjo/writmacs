from .util import strip_seq

INTERPOLATE = '%'
TERMINATE = ';'
BRACKETS = {
        '(': ')',
        '[': ']',
        '{': '}',
        '"': '"',
        '`': '`',
        "'": "'",
        '/': '/'
        }
AMBIBRACKETS = set('()[]{}<>"`\'/')
WHITESPACE = set(' \n\t')

def tree_print(chunks, depth=0):
    for chunk in chunks:
        if type(chunk) == dict:
            print('  ' * depth + '%' + chunk['name'])
            for i in range(len(chunk['vals'])):
                print('  ' * depth + ' ' + chunk['bracs'][i])
                tree_print(chunk['vals'][i], depth=depth+1)
        else:
            print('  ' * depth + chunk)


def parse(text):
    breadcrumbs = []
    frontier = 0

    def at_ladder():
        if len(breadcrumbs) == 0:
            return False

        ladder = breadcrumbs[-1]
        if frontier + len(ladder) > len(text):
            return False

        return text[frontier:frontier + len(ladder)] == ladder

    def parse_prose():
        nonlocal frontier
        start = frontier
        chunks = []

        while True:
            while (
                    frontier < len(text)
                    and not at_ladder()
                    and text[frontier] != INTERPOLATE
                    ):
                frontier += 1

            if frontier > start:
                chunks.append(text[start:frontier])
                start = frontier

            if frontier == len(text):
                return strip_seq(chunks)

            if at_ladder():
                frontier += len(breadcrumbs[-1])
                breadcrumbs.pop()
                return strip_seq(chunks)

            if text[frontier] == INTERPOLATE:
                chunks.append(parse_macro())
                start = frontier

    def parse_macro():
        nonlocal frontier
        name_start = frontier + 1 # skip INTERPOLATE character
        frontier = name_start

        while (
                frontier < len(text)
                and text[frontier] not in AMBIBRACKETS
                and text[frontier] not in WHITESPACE
                and text[frontier] != TERMINATE
                ):
            frontier += 1

        name = text[name_start:frontier]
        vals = []
        bracs = []

        while frontier < len(text) and text[frontier] in BRACKETS:
            bracket_start = frontier
            while text[frontier] == text[bracket_start]:
                frontier += 1
            bracket = text[bracket_start:frontier]
            bracs.append(bracket)

            # reverse bracket direction for close bracket string a.k.a. ladder
            breadcrumbs.append(BRACKETS[bracket[0]] * len(bracket))

            if bracket.startswith('`'): # literal quotation
                prose_start = frontier
                while frontier < len(text) and not at_ladder():
                    frontier += 1
                vals.append([text[prose_start:frontier]])
                frontier += len(bracket) # jump over closing bracket
            else:
                vals.append(parse_prose())

        # print('PARSED PROSE, NOW AT:', frontier)
        if frontier < len(text) and text[frontier] == ';':
            frontier += 1

        return {'name': name, 'bracs': bracs, 'vals': vals}

    return {'name': 'root', 'vals': [parse_prose()]}
