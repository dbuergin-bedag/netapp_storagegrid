#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    LevelDirection,
    Percentage,
    SimpleLevels,
)
from cmk.rulesets.v1.rule_specs import CheckParameters, HostAndItemCondition, Topic


def _parameter_form_netapp_storagegrid_tenant_quota() -> Dictionary:
    return Dictionary(
        title=Title("NetApp StorageGRID tenant quota"),
        help_text=Help(
            "Configure the levels for the percentage of a tenant account's object "
            "quota (policy.quotaObjectBytes) that is currently used. Tenants without "
            "a configured quota are always reported OK."
        ),
        elements={
            "levels_upper": DictElement(
                required=True,
                parameter_form=SimpleLevels(
                    title=Title("Levels for quota usage"),
                    form_spec_template=Percentage(),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(value=(80.0, 90.0)),
                ),
            ),
        },
    )


rule_spec_netapp_storagegrid_tenant_quota = CheckParameters(
    name="netapp_storagegrid_tenant_quota",
    title=Title("NetApp StorageGRID tenant quota"),
    topic=Topic.STORAGE,
    parameter_form=_parameter_form_netapp_storagegrid_tenant_quota,
    condition=HostAndItemCondition(item_title=Title("Tenant account name")),
)
