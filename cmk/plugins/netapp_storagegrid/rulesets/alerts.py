#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import BooleanChoice, DefaultValue, DictElement, Dictionary, ServiceState
from cmk.rulesets.v1.rule_specs import CheckParameters, HostCondition, Topic


def _parameter_form_netapp_storagegrid_alerts() -> Dictionary:
    return Dictionary(
        title=Title("NetApp StorageGRID alerts"),
        help_text=Help(
            "Configure the monitoring state that is reported when the NetApp StorageGRID "
            "cluster currently has active alerts of a given severity."
        ),
        elements={
            "state_critical": DictElement(
                required=True,
                parameter_form=ServiceState(
                    title=Title("State if CRITICAL alerts are present"),
                    prefill=DefaultValue(ServiceState.CRIT),
                ),
            ),
            "state_major": DictElement(
                required=True,
                parameter_form=ServiceState(
                    title=Title("State if MAJOR alerts are present"),
                    prefill=DefaultValue(ServiceState.WARN),
                ),
            ),
            "state_minor": DictElement(
                required=True,
                parameter_form=ServiceState(
                    title=Title("State if MINOR alerts are present"),
                    prefill=DefaultValue(ServiceState.WARN),
                ),
            ),
            "ignore_silenced": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    title=Title("Silenced alerts"),
                    label=Label("Ignore alerts that have been silenced in StorageGRID"),
                    prefill=DefaultValue(True),
                ),
            ),
            "ignore_inhibited": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    title=Title("Inhibited alerts"),
                    label=Label(
                        "Ignore alerts that are inhibited by another, already counted alert"
                    ),
                    prefill=DefaultValue(True),
                ),
            ),
        },
    )


rule_spec_netapp_storagegrid_alerts = CheckParameters(
    name="netapp_storagegrid_alerts",
    title=Title("NetApp StorageGRID alerts"),
    topic=Topic.STORAGE,
    parameter_form=_parameter_form_netapp_storagegrid_alerts,
    condition=HostCondition(),
)
