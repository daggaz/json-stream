from collections import deque

from json_stream.base import StreamingJSONList, StreamingJSONObject


class Context:
    LIST = 1
    DICT = 2


def to_standard_types(x):
    in_stack, out_stack = deque(), deque()
    if isinstance(x, StreamingJSONList):
        in_stack.append((Context.LIST, iter(x)))
        output = []
    elif isinstance(x, StreamingJSONObject):
        in_stack.append((Context.DICT, iter(x.items())))
        output = {}
    else:
        return x
    out_stack.append(output)
    while len(in_stack) > 0:
        try:
            in_context, in_iter = in_stack[-1]
            in_elem = next(in_iter)
            if in_context == Context.LIST:
                if isinstance(in_elem, StreamingJSONList):
                    out_list = []
                    out_stack[-1].append(out_list)
                    out_stack.append(out_list)
                    in_stack.append((Context.LIST, iter(in_elem)))
                elif isinstance(in_elem, StreamingJSONObject):
                    out_dict = {}
                    out_stack[-1].append(out_dict)
                    out_stack.append(out_dict)
                    in_stack.append((Context.DICT, iter(in_elem.items())))
                else:
                    out_stack[-1].append(in_elem)
            elif in_context == Context.DICT:
                in_key, in_value = in_elem
                if isinstance(in_value, StreamingJSONList):
                    out_list = []
                    out_stack[-1][in_key] = out_list
                    out_stack.append(out_list)
                    in_stack.append((Context.LIST, iter(in_value)))
                elif isinstance(in_value, StreamingJSONObject):
                    out_dict = {}
                    out_stack[-1][in_key] = out_dict
                    out_stack.append(out_dict)
                    in_stack.append((Context.DICT, iter(in_value.items())))
                else:
                    out_stack[-1][in_key] = in_value
        except StopIteration:
            in_stack.pop()
            out_stack.pop()
    return output
