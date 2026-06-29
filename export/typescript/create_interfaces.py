import enum
import inspect
from types import NoneType
from typing import Any, Union, get_args, get_origin, get_type_hints

from pyobs import interfaces


def hint_to_ts(hint: Any) -> str:
    if hint is int or hint is float:
        return "number"
    if hint is NoneType:
        return "void"
    if hint is str:
        return "string"
    if hint is bool:
        return "boolean"
    if hint is Any:
        return "any"
    if get_origin(hint) is tuple or get_origin(hint) is list:
        return "[" + ", ".join([hint_to_ts(h) for h in get_args(hint)]) + "]"
    if get_origin(hint) is dict:
        args = get_args(hint)
        return "{" + hint_to_ts(args[0]) + ": " + hint_to_ts(args[1]) + "}"
    if get_origin(hint) is Union:
        return " | ".join([hint_to_ts(hint) for hint in get_args(hint)])
    if issubclass(hint, enum.Enum):
        return "string"
    return str(hint)


with open("pyobs_interfaces.ts", "w") as f:
    f.write("import { rpcCall } from './xmpp';\n\n")
    for name, obj in inspect.getmembers(interfaces, inspect.isclass):
        print(name)

        f.write(f"export class {name} {{\n")
        f.write("  jid: string;\n")
        f.write("  constructor(jid: string) {\n")
        f.write("    this.jid = jid;\n")
        f.write("  }\n")

        for funcname, member in inspect.getmembers(obj, inspect.isroutine):
            if funcname.startswith("_"):
                continue
            print("  -", funcname)

            params = []
            param_names = []
            rettype = ""
            for name, hint in get_type_hints(member).items():
                print(name, hint)
                # ignore kwargs
                if name == "kwargs":
                    continue
                if name == "return":
                    rettype = hint_to_ts(hint)
                    continue
                typ = hint_to_ts(hint)
                params.append(f"{name}: {typ}")
                param_names.append(name)
            rettype = "" if rettype == "void" else ": Promise<" + rettype + ">"
            sig = "(" + ", ".join(params) + ")" + rettype

            print("    - ", sig)

            f.write(f"  public async {funcname}{sig} {{\n")
            f.write(f"    return await rpcCall(this.jid, '{funcname}'")
            if len(param_names) > 0:
                f.write(", [" + ", ".join(param_names) + "]")
            f.write(");\n")
            f.write("  }\n")
        f.write("}\n\n")
