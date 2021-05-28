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
from .util import TARGETS, Node

DEFAULT_CONTEXT = {'target': 'md'}

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


def eval_forest(forest, context=None):

    if context is None:
        context = {}

    data_out = {}
    builder = []

    for item in forest:
        if type(item) is Node:
            chunks, tree_data_out = eval_tree(item, context)
            builder.extend(chunks)
            data_out = {**data_out, **tree_data_out} # later > earlier
        else:
            # a str or something that can be cast to one e.g. a Token
            builder.append(item)

    return builder, data_out


def eval_tree(mac_tree, context=None):

    if context is None:
        context = {}

    # create context specifically for this sub-tree
    if mac_tree.name in contextualizers:
        # deeper > shallower
        local_context = {
            **context,
            **contextualizers[mac_tree.name](mac_tree.children)
        }
    else:
        local_context = context

    # evaluate the sub-tree below
    children = []
    data_out = {}
    for forest in mac_tree.children:
        builder, child_data_out = eval_forest(forest, local_context)
        children.append(builder)
        data_out.update(child_data_out)

    # perform the macro operation for this tree node
    if mac_tree.name in expanders:
        builder_out, *more_data = expanders[mac_tree.name](
                children, context
                )
        if len(more_data) == 1:
            data_out.update(more_data[0])
    else:
        # if no operation to do, default to flattening children together
        builder_out = [chunk for child in children for chunk in child]

    return builder_out, data_out


def expand(main_txt, context=None):
    if context is None:
        context = DEFAULT_CONTEXT
    main_tree = semantic_tree(main_txt)
    full_builder, full_meta = eval_tree(main_tree, context)
    return ''.join([str(chunk) for chunk in full_builder]), full_meta

if __name__ == '__main__':
    mac_txt = sys.stdin.read()
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target not in TARGETS:
        target = 'md'
    result, metadata = expand(mac_txt, {'target': target})

    print(result)

