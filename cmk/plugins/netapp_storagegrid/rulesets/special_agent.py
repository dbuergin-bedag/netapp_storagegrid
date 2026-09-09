#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    migrate_to_password,
    Password,
    SingleChoice,
    SingleChoiceElement,
    String,
    TimeMagnitude,
    TimeSpan,
    validators,
)
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _parameter_form() -> Dictionary:
    return Dictionary(
        title=Title("NetApp StorageGRID"),
        help_text=Help(
            "This rule configures the special agent for NetApp StorageGRID. It connects "
            "to the Grid Management REST API to retrieve monitoring data, for example "
            "currently active alerts on the StorageGRID cluster."
        ),
        elements={
            "username": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Username"),
                    help_text=Help("Grid Manager user name with permission to view alerts."),
                    custom_validate=(validators.LengthInRange(min_value=1),),
                ),
            ),
            "password": DictElement(
                required=True,
                parameter_form=Password(
                    title=Title("Password"),
                    custom_validate=(validators.LengthInRange(min_value=1),),
                    migrate=migrate_to_password,
                ),
            ),
            "port": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("TCP port for connection"),
                    prefill=DefaultValue(443),
                    custom_validate=(validators.NetworkPort(),),
                ),
            ),
            "proto": DictElement(
                required=False,
                parameter_form=SingleChoice(
                    title=Title("Protocol"),
                    elements=[
                        SingleChoiceElement(name="https", title=Title("HTTPS")),
                        SingleChoiceElement(name="http", title=Title("HTTP")),
                    ],
                    prefill=DefaultValue("https"),
                ),
            ),
            "no_cert_check": DictElement(
                required=False,
                parameter_form=BooleanChoice(
                    title=Title("SSL certificate verification"),
                    label=Label("Disable SSL certificate verification"),
                    prefill=DefaultValue(False),
                ),
            ),
            "timeout": DictElement(
                required=False,
                parameter_form=TimeSpan(
                    title=Title("API call timeout"),
                    displayed_magnitudes=[TimeMagnitude.SECOND],
                    prefill=DefaultValue(10.0),
                ),
            ),
        },
    )


rule_spec_special_agent_netapp_storagegrid = SpecialAgent(
    name="netapp_storagegrid",
    title=Title("NetApp StorageGRID"),
    topic=Topic.STORAGE,
    parameter_form=_parameter_form,
)
