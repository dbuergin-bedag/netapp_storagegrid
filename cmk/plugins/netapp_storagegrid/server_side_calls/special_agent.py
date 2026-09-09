#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Iterable

from pydantic import BaseModel

from cmk.server_side_calls.v1 import HostConfig, Secret, SpecialAgentCommand, SpecialAgentConfig


class Params(BaseModel):
    username: str
    password: Secret
    port: int | None = None
    proto: str = "https"
    no_cert_check: bool = False
    timeout: float | None = None


def commands_function(
    params: Params,
    host_config: HostConfig,
) -> Iterable[SpecialAgentCommand]:
    command_arguments: list[str | Secret] = [
        "--username",
        params.username,
        "--password-id",
        params.password,
        "--proto",
        params.proto,
    ]

    if params.port is not None:
        command_arguments += ["--port", str(params.port)]

    if params.no_cert_check:
        command_arguments.append("--no-cert-check")
    else:
        command_arguments += ["--cert-server-name", host_config.name]

    if params.timeout is not None:
        command_arguments += ["--timeout", str(params.timeout)]

    command_arguments.append(host_config.name)

    yield SpecialAgentCommand(command_arguments=command_arguments)


special_agent_netapp_storagegrid = SpecialAgentConfig(
    name="netapp_storagegrid",
    parameter_parser=Params.model_validate,
    commands_function=commands_function,
)
