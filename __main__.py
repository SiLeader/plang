#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import typing
import random
import string


GenSourceType = typing.List[str]
GenHeaderType = typing.List[str]

SourceType = typing.List[typing.Tuple[int, int, str]]
ReturnType = typing.Tuple[SourceType, GenSourceType]
OptionalReturnType = typing.Optional[ReturnType]


__variables = {}
__global_variables = {}
__indent_depth = 4


def __indented(dd: typing.List[str], base_depth=0) -> typing.List[str]:
    depth = base_depth
    d = []
    for datum in dd:
        if datum.endswith("{"):
            d.append(" " * depth + datum)
            depth += 4
        elif datum.startswith("}"):
            depth -= 4
            d.append(" " * depth + datum)
        else:
            d.append(" " * depth + datum)
    return d


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", action="store", type=str)
    parser.add_argument("-o", "--output", action="store", type=str, default=None)

    args = parser.parse_args()

    input_file = args.input
    input_file_base = input_file.split(".")[0]
    if args.output is None:
        output_file = input_file_base
    else:
        output_file = args.output

    with open(input_file) as fp:
        lines = fp.readlines()
        lines.append("from core import *")
        data, import_data = decode(lines)

    import_data = statements(import_data, 0)
    data = statements(data, 0)

    _, data = data
    _, import_data = import_data
    dd = [
        "//",
        "// Auto generated C++ Source file.",
        "// Generated from {}".format(input_file),
        "//",
        "",
        "#if __has_include(<{}.hpp>)".format(input_file_base),
        "#   include <{}.hpp>".format(input_file_base),
        '#elif __has_include("{}.hpp")'.format(input_file_base),
        '#   include "{}.hpp"'.format(input_file_base),
        "#else",
        '#   error cannot find self include file. name: {}.hpp"'.format(input_file_base),
        "#endif",
        ""
    ]
    dd.extend(import_data)
    dd.append("namespace {}".format(input_file_base) + " {")
    dd.extend(data)
    dd.append("} // " + input_file_base)
    d = __indented(dd)

    """with open(output_file + ".cpp", "w") as fp:
        fp.write("\n".join(d))
        fp.write("\n")"""

    with open(output_file + ".hpp", "w") as fp:
        iguard = "PLANG_{}".format(output_file.replace(".", "_").upper() + "_HPP")
        lines = [
            "#ifndef {}".format(iguard),
            "#define {}".format(iguard),
            ""
        ]
        lines.extend(d)
        lines.extend([
            "",
            "#endif // {}\n".format(iguard)
        ])
        fp.write("\n".join(lines))


def decode(data: typing.List[str]) -> typing.Tuple[SourceType, SourceType]:  # basic, import
    lines = []

    for line_number, datum in enumerate(data, 1):
        stripped = datum.lstrip()
        depth = len(datum) - len(stripped)

        stripped = stripped.split("#")[0]

        if ";" in stripped:
            stripped = [(line_number, depth, s.strip()) for s in stripped.split(";")]
        else:
            stripped = [(line_number, depth, stripped.strip())]
        lines.extend(stripped)

    lines = [(ln, depth, line) for ln, depth, line in lines if len(line) != 0 if line != "pass"]
    import_lines = [
        (ln, depth, line) for ln, depth, line in lines if line.startswith("import") or line.startswith("from")
    ]
    lines = [
        (ln, depth, line) for ln, depth, line in lines if not(line.startswith("import") or line.startswith("from"))
    ]
    return lines, import_lines


def decorator(data: SourceType) -> OptionalReturnType:
    line_number, depth, sen = data[0]

    if not sen.startswith("@"):
        return None


def _class(data: SourceType) -> OptionalReturnType:
    line_number, depth, sen = data[0]
    match = re.match("class\s+([a-zA-Z_]\w*)\s*:", sen)
    if match is None:
        match = re.match("class\s+([a-zA-Z_]\w*)\s*\((.*)\):", sen)
    if match is None:
        return None

    class_name = match.group(1)
    if len(match.groups()) >= 2:
        inherit_classes = match.group(2)
        inherit_classes = [
            i.split()
            for i in inherit_classes.split(",")
        ]
    else:
        inherit_classes = []

    class_definition = "class {}".format(class_name)
    if len(inherit_classes) > 0:
        class_definition += " : {}".format(", ".join(["public {}".format(i) for i in inherit_classes]))

    generated = [class_definition + " {"]

    data = data[1:]
    while True:
        if len(data) == 0:
            break
        _, f_depth, _ = data[0]
        if f_depth < depth:
            break

        source, gen = func(data, class_name)

        if re.search(" __", gen[0]) is not None:
            access = "private:"
        elif re.search(" _", gen[0]) is not None:
            access = "protected:"
        else:
            access = "public:"
        generated.append(access)
        generated.extend(gen)
        data = source

    generated.append("};")

    return data, generated


def func(data: SourceType, class_name=None) -> OptionalReturnType:
    line_number, depth, sen = data[0]
    match = re.match("def\s+([a-zA-Z_][0-9a-zA-Z_]*)\s*\((.*)\)\s*->\s*([a-zA-Z_][0-9a-zA-Z_.]*)\s*:", sen)
    if match is None:
        match = re.match("def\s+([a-zA-Z_][0-9a-zA-Z_]*)\s*\((.*)\)\s*:", sen)
    if match is None:
        return None
    func_name = match.group(1)
    parameter = match.group(2).strip()
    if len(match.groups()) >= 3:
        return_type = match.group(3)
    else:
        return_type = "auto"

    if class_name is not None:
        method_table = {
            "__init__": class_name,
            "__str__": "__str__",  # func str
            "__bytes__": "__bytes__",
            "__format__": "__format__",

            "__iter__": "__iter__",
            "__next__": "__next__",
            "__reversed__": "__reversed__",

            "__getattribute__": "__getattribute__",
            "__getattr__": "__getattr__",
            "__setattr__": "__setattr__",
            "__delattr__": "__delattr__",
            "__dir__": "__dir__",

            "__call__": "operator()",

            "__len__": "__len__",  # func len
            "__contains__": "__contains__",

            "__getitem__": "__getitem__",
            "__setitem__": "__setitem__",
            "__delitem__": "__delitem__",
            "__missing__": "__missing__",

            "__add__": "operator+",
            "__sub__": "operator-",
            "__mul__": "operator*",
            "__truediv__": "__truediv__",
            "__floordiv__": "operator/",
            "__mod__": "operator%",
            "__pow__": "__pow",
            "__lshift__": "operator<<",
            "__rshift__": "operator>>",
            "__and__": "operator&",
            "__xor__": "operator^",
            "__or__": "operator|",

            "__iadd__": "operator+=",
            "__isub__": "operator-=",
            "__imul__": "operator*=",
            "__itruediv__": "__itruediv__",
            "__ifloordiv__": "operator/=",
            "__imod__": "operator%=",
            "__ilshift__": "operator<<=",
            "__irshift__": "operator>>=",
            "__iand__": "operator&=",
            "__ixor__": "operator^=",
            "__ior__": "operator|=",

            "__neg__": "operator-",
            "__pos__": "operator+",
            "__abs__": "__abs__",  # func abs
            "__invert__": "operator~",
            "__complex__": "__complex__",
            "__int__": "operator int",  # func int
            "__float__": "operator double",  # func float
            "__round__": "__round__",  # func round(x), round(x, n)
            "__ceil__": "__ceil__",  # func math.ceil
            "__floor__": "__floor__",  # func math.floor
            "__trunc__": "__trunc__",  # func math.trunc

            "__eq__": "operator==",
            "__ne__": "operator!=",
            "__lt__": "operator<",
            "__le__": "operator<=",
            "__gt__": "operator>",
            "__ge__": "operator>=",
            "__bool__": "operator bool",

            "__del__": "~{}".format(class_name)
        }

        if func_name in ["__del__", "__init__"]:
            return_type = ""
        if func_name in method_table:
            func_name = method_table[func_name]
            if func_name.startswith("operator "):
                return_type = ""

    parameter_list = []
    template_parameter_list = []
    if len(parameter) > 0:
        for p in parameter.split(","):
            p = p.strip()
            if ":" in p:
                p = [pp.strip() for pp in p.split(":")]
                parameter_list.append((p[0], p[1]))
            else:
                if class_name is not None and p in ["self", "cls"]:
                    continue
                pname = "_" + p.upper()
                template_parameter_list.append("class {}".format(pname))
                parameter_list.append((p, pname))

    if len(template_parameter_list) > 0:
        generated = ["template<{}>".format(", ".join(template_parameter_list))]
    else:
        if class_name is None:
            generated = ["inline"]
        else:
            generated = []

    generated.append("{} {}({})".format(
        return_type, func_name, ", ".join(["{} {}".format(t, n) for n, t in parameter_list])
    ) + " {")

    source, gen = statements(data[1:], depth + __indent_depth)

    generated.extend(gen)
    generated.append("}")

    """print(generated[0])
    if generated[0].startswith("template"):
        header_gen = copy.deepcopy(generated)
        generated.clear()
    else:
        prototype = generated[0].strip(" \n{") + ";"
        if class_name is not None:
            prototype = prototype.replace("{}::".format(class_name), "")
        header_gen = [prototype]
    header_gen.extend(header)"""

    return source, generated


def __variable_name(name: str, vid: str) -> str:
    return name + "_" + vid


def _while(data: SourceType, start_depth: int) -> OptionalReturnType:
    line_number, depth, sen = data[0]
    sen = sen.split(" ")
    if not sen[0].startswith("while"):
        return None

    condition = _single_expression((line_number, depth, (" ".join(sen[1:])).strip(":")), need_semicolon=False)
    generated = ["while({})".format(" ".join(condition)) + " {"]
    d, g = statements(data[1:], start_depth + __indent_depth)
    generated.extend(g)
    generated.append("}")

    return d, generated


def _if(data: SourceType, start_depth: int) -> OptionalReturnType:
    line_number, depth, sen = data[0]
    sen = sen.split(" ")
    if not sen[0].startswith("if"):
        return None

    condition = _single_expression((line_number, depth, (" ".join(sen[1:])).strip(":")), need_semicolon=False)
    generated = ["if({})".format(" ".join(condition)) + " {"]
    d, g = statements(data[1:], start_depth + __indent_depth)
    generated.extend(g)
    generated.append("}")

    return d, generated


def _single_expression(data: typing.Tuple[int, int, str], need_semicolon=True) -> typing.List[str]:
    line_number, depth, sen = data
    str_delimiter = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])

    while '"""' in sen:
        sen = sen \
            .replace('"""', 'R"{}('.format(str_delimiter), 1).replace('"""', '){}"'.format(str_delimiter))
    match = re.fullmatch("([a-zA-Z_][0-9a-zA-Z_]*)\s*=\s*([^=\s]+)", sen)
    if match is not None:
        name = match.group(1)
        value = match.group(2)
        vid = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])

        sen = "auto {} = {}".format(__variable_name(name, vid), value)
        __variables[name] = vid

    else:
        for name, vid in __variables.items():
            if name in sen:
                sen = sen.replace(name, __variable_name(name, vid))

    match = re.search("([a-zA-Z_][a-zA-Z0-9_]*|\[[^\n\f\r]*\])\s*(\[[^\n\f\r]+\])", sen)
    if match is not None:  # match slice
        operand = match.group(1)
        # sl = match.group(2)
        sen = sen.replace(operand, operand.replace("[", "list(").replace("]", ")"))
    else:
        sen = sen.replace("[", "list(").replace("]", ")")
        pass

    if need_semicolon:
        sen += ";"
    return [sen]


def _expression(data: SourceType) -> ReturnType:
    sen = _single_expression(data[0])
    return data[1:], sen


def _statement(data: SourceType, start_depth: int) -> OptionalReturnType:
    line_number, depth, sen = data[0]
    if depth < start_depth:
        return None

    return _expression(data)


def _import(data: SourceType) -> OptionalReturnType:
    line_number, depth, sen = data[0]

    appendix = []
    match = re.match("import\s+(\w+)\s+as\s+(\w+)", sen)
    if match is not None:
        include = match.group(1)
        import_name = match.group(2)
        appendix = ["namespace {} = {};".format(import_name, include)]
    else:
        match = re.match("import\s+(\w+)", sen)
        if match is None:
            match = re.match("from\s+(\w+)\s+import\s+([\w*]+)", sen)
            if match is None:
                return None
            else:
                include = match.group(1)
                show = [m.strip() for m in match.group(2).split(",")]
                if show[0] == "*":
                    appendix = ["using namespace {};".format(include)]
                else:
                    appendix = ["using {}::{};".format(include, m) for m in show]
        else:
            include = match.group(1)

    ret = [
        "#if __has_include(<{}.hpp>)".format(include),
        "#   include <{}.hpp>".format(include),
        '#elif __has_include("{}.hpp")'.format(include),
        '#   include "{}.hpp"'.format(include),
        "#else",
        '#   error "cannot import include file. name: {}"'.format(include),
        "#endif"
    ]
    if len(appendix) != 0:
        ret.extend(appendix)
    ret.append("")

    return data[1:], ret


def statements(data: SourceType, start_depth: int) -> ReturnType:
    generated = []
    while True:
        if len(data) == 0:
            break
        _, depth, _ = data[0]
        if depth < start_depth:
            break

        ret = _import(data)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        ret = _while(data, start_depth)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        ret = _if(data, start_depth)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        ret = func(data)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        ret = _class(data)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        ret = _statement(data, start_depth)
        if ret is not None:
            d, g = ret
            data = d
            generated.extend(g)
            continue

        break
    return data, generated


if __name__ == '__main__':
    main()
