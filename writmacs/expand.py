'''
"node":
    a promise of a future text builder with a name that specifies what it
    intends to do with its 1 or more child forests to produce it
"forest":
    a list of strings, nodes (i.e. trees), or tokens
"builder":
    a list of strings and tokens (not nodes) meant to be joined into a string
"AST":
    abstract syntax tree, tracking what text has been placed in which parens
    but not what parameter order or paren choice mean down the line
"semantic tree":
    a node containing forests containing nodes etc. with node children assigned
    and organized in a meaningful way
'''

import sys

from .parse import parse
from .macros import expanders, organizers, contextualizers
from .util import TARGETS

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

def AST2tree(syntax_node):
    name = syntax_node['name']

    if name in organizers:
        protochildren, children_names = organizers[name](syntax_node)
    else:
        protochildren = syntax_node['vals']
        children_names = {}

    children = []
    for section in protochildren:
        forest = []
        for chunk in section:
            if type(chunk) is str:
                forest.append(chunk)
            else:
                forest.append(AST2tree(chunk))
        children.append(forest)

    return Node(name, children, children_names)


def semantic_tree(macs_txt):

    AST = parse(macs_txt)
    return AST2tree(AST)


def eval_forest(forest, metadata=None):

    metadata = metadata if metadata is not None else {'target': 'md'}
    builder = []

    for item in forest:
        if type(item) is Node:
            chunks, inner_data = eval_tree(item, metadata, collapse=False)
            builder.extend(chunks)
            metadata = {**metadata, **inner_data} # later > earlier
        else:
            builder.append(item)

    return builder, metadata


def eval_tree(mac_tree, metadata=None, collapse=True):

    metadata = metadata if metadata is not None else {'target': 'md'}
    children = []

    for nth, forest in enumerate(mac_tree.children):
        if mac_tree.name in contextualizers:
            # deeper > shallower
            local_metadata = {**metadata, **contextualizers[mac_tree.name][nth]}
        else:
            local_metadata = metadata
        chunks, inner_data = eval_forest(forest, local_metadata)
        children.append(chunks)
        metadata = {**inner_data, **metadata} # shallower > deeper

    if mac_tree.name in expanders:
        builder, *more_data = expanders[mac_tree.name](
                children, metadata
                )
        if len(more_data) == 1:
            metadata = {**more_data[0], **metadata}
    else:
        builder = [chunk for child in children for chunk in child]
    if collapse:
        return ''.join([str(chunk) for chunk in builder]), metadata
    else:
        return builder, metadata

def expand(main_txt, target='md'):
    main_tree = semantic_tree(main_txt)
    return eval_tree(main_tree, {'target': target})

if __name__ == '__main__':
    mac_txt = sys.stdin.read()
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target not in TARGETS:
        target = 'md'
    result, metadata = expand(mac_txt)

    print(result)

