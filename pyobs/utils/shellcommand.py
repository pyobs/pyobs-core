from __future__ import annotations

import pprint
import tokenize
from enum import Enum
from io import BytesIO
from typing import Any

from pyobs.comm import Comm
import pyobs.utils.exceptions as exc


class ParserState(Enum):
    START = 0
    MODULE = 1
    MODSEP = 2
    COMMAND = 3
    OPEN = 4
    PARAM = 5
    PARAMSEP = 6
    CLOSE = 7


class ShellCommand:
    last_command_number: int = 0

    def __init__(self, command_string: str, module: str, command: str, params: list[Any]) -> None:
        self.command_string = command_string
        self.module = module
        self.command = command
        self.params = params

        self.last_command_number += 1
        self.command_number = self.last_command_number

    @staticmethod
    def parse(cmd: str) -> ShellCommand:
        # tokenize command
        tokens = tokenize.tokenize(BytesIO(cmd.encode("utf-8")).readline)

        # init values
        module: str | None = None
        command: str | None = None
        params: list[Any] = []
        sign = 1

        # we start here
        state = ParserState.START

        # loop tokens
        for t in tokens:
            if state == ParserState.START:
                # first token is always ENCODING
                if t.type != tokenize.ENCODING:
                    raise ValueError("Invalid command.")
                state = ParserState.MODULE

            elif state == ParserState.MODULE:
                # 2nd token is always a NAME with the command
                if t.type != tokenize.NAME:
                    raise ValueError("Invalid command.")
                module = t.string
                state = ParserState.MODSEP

            elif state == ParserState.MODSEP:
                # 3rd token is always a point
                if t.type != tokenize.OP or t.string != ".":
                    raise ValueError("Invalid command.")
                state = ParserState.COMMAND

            elif state == ParserState.COMMAND:
                # 4th token is always a NAME with the command
                if t.type != tokenize.NAME:
                    raise ValueError("Invalid command.")
                command = t.string
                state = ParserState.OPEN

            elif state == ParserState.OPEN:
                # 5th token is always an OP with an opening bracket
                if t.type != tokenize.OP or t.string != "(":
                    raise ValueError("Invalid parameters.")
                state = ParserState.PARAM

            elif state == ParserState.PARAM:
                # if params list is empty, we accept an OP with a closing bracket, otherwise it must be
                # a NUMBER or STRING
                if len(params) == 0 and t.type == tokenize.OP and t.string == ")":
                    state = ParserState.CLOSE
                elif t.type == tokenize.OP and t.string == "-":
                    sign = -1
                elif t.type == tokenize.NUMBER or t.type == tokenize.STRING:
                    if t.type == tokenize.STRING:
                        if t.string[0] == t.string[-1] and t.string[0] in ['"', '"']:
                            params.append(t.string[1:-1])
                        else:
                            params.append(t.string)
                    else:
                        params.append(sign * float(t.string))
                    sign = 1
                    state = ParserState.PARAMSEP
                else:
                    raise ValueError("Invalid parameters.")

            elif state == ParserState.PARAMSEP:
                # following a PARAM, there must be an OP, either a comma, or a closing bracket
                if t.type != tokenize.OP:
                    raise ValueError("Invalid parameters.")
                if t.string == ",":
                    state = ParserState.PARAM
                elif t.string == ")":
                    state = ParserState.CLOSE
                else:
                    raise ValueError("Invalid parameters.")

            elif state == ParserState.CLOSE:
                # must be a closing bracket
                if t.type not in [tokenize.NEWLINE, tokenize.ENDMARKER]:
                    raise ValueError("Expecting end of command after closing bracket.")

                # return results
                if module is None or command is None:
                    raise ValueError("Found end of command without module and/or command.")
                return ShellCommand(cmd, module, command, params)

        # if we came here, something went wrong
        raise ValueError("Invalid parameters.")

    async def execute(self, comm: Comm) -> ShellCommandResponse:
        try:
            proxy = await comm.proxy(self.module)
        except ValueError:
            return self.__err(f"Could not find module: {self.module}")

        try:
            response = await proxy.execute(self.command, *self.params)
        except ValueError as e:
            return self.__err(f"Invalid parameter: {str(e)}")
        except exc.RemoteError as e:
            return self.__err(f"Exception raised: {str(e)}")

        # log response
        msg = "OK" if response is None else pprint.pformat(response)
        return self.__res(msg)

    def __str__(self) -> str:
        return f"$ (#{self.command_number}) {self.command_string}"

    def __err(self, message: str) -> ShellCommandResponse:
        return ShellCommandResponse(self.command_number, self, message, is_error=True)

    def __res(self, response: Any) -> ShellCommandResponse:
        return ShellCommandResponse(self.command_number, self, response)


class ShellCommandResponse:
    def __init__(self, command_number: int, command: ShellCommand, response: str, is_error: bool = False) -> None:
        self.command_number = command_number
        self.command = command
        self.response = response
        self.is_error = is_error

    def __str__(self) -> str:
        return f"(#{self.command_number}): {self.response}"

    @property
    def color(self) -> str:
        return "red" if self.is_error else "lime"

    @property
    def bbcode(self) -> str:
        return f"[{self.color}]{str(self)}[/{self.color}]"


__all__ = ["ShellCommand", "ShellCommandResponse"]
