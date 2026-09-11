#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Check plugin for the storage quota usage of NetApp StorageGRID tenant accounts.

The special agent fetches the list of tenant (Storage Tenant) accounts from
the Grid Management REST API (GET /api/v3/grid/accounts-cache), whose
response looks like this (see the StorageGRID Grid Management API
documentation)::

    {
      "data": [
        {
          "id": "12345678901234567890",
          "name": "Widgets Unlimited",
          "policy": {"quotaObjectBytes": 100000000000},
          "dataBytes": 123456789,
          "objectCount": 42
        }
      ]
    }

If a tenant has no quota configured, "policy.quotaObjectBytes" is null/absent
and the used bytes are reported without a percentage check.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

from cmk.agent_based.v2 import (
    AgentSection,
    check_levels,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    render,
    Result,
    Service,
    State,
    StringTable,
)

Tenant = Mapping[str, Any]
Section = Mapping[str, Tenant]


def _normalize(raw_tenant: Mapping[str, Any]) -> Tenant | None:
    name = raw_tenant.get("name")
    if not name:
        return None

    policy = raw_tenant.get("policy")
    policy = policy if isinstance(policy, Mapping) else {}

    return {
        "id": str(raw_tenant.get("id", "")),
        "name": str(name),
        "used_bytes": int(raw_tenant.get("dataBytes") or 0),
        "quota_bytes": policy.get("quotaObjectBytes"),
    }


def parse_netapp_storagegrid_tenant_quota(string_table: StringTable) -> Section:
    if not string_table:
        return {}

    raw = json.loads(string_table[0][0])
    tenants = raw if isinstance(raw, list) else raw.get("data", [])

    section = {}
    for raw_tenant in tenants:
        if not isinstance(raw_tenant, Mapping):
            continue
        tenant = _normalize(raw_tenant)
        if tenant is not None:
            section[tenant["name"]] = tenant
    return section


agent_section_netapp_storagegrid_tenant_quota = AgentSection(
    name="netapp_storagegrid_tenants",
    parse_function=parse_netapp_storagegrid_tenant_quota,
)


def discover_netapp_storagegrid_tenant_quota(section: Section) -> DiscoveryResult:
    for name in section:
        yield Service(item=name)


def check_netapp_storagegrid_tenant_quota(
    item: str,
    params: Mapping[str, Any],
    section: Section,
) -> CheckResult:
    tenant = section.get(item)
    if tenant is None:
        return

    used_bytes = tenant["used_bytes"]
    quota_bytes = tenant["quota_bytes"]

    if not quota_bytes:
        yield Result(
            state=State.OK,
            summary=f"Used: {render.bytes(used_bytes)}, no quota configured",
        )
        yield Metric("netapp_storagegrid_tenant_used_bytes", used_bytes)
        return

    used_percent = 100.0 * used_bytes / quota_bytes
    yield from check_levels(
        used_percent,
        levels_upper=params["levels_upper"],
        metric_name="netapp_storagegrid_tenant_quota_used_percent",
        label="Quota used",
        render_func=render.percent,
        boundaries=(0.0, 100.0),
    )
    yield Result(
        state=State.OK,
        notice=f"Used: {render.bytes(used_bytes)} of {render.bytes(quota_bytes)}",
    )
    yield Metric("netapp_storagegrid_tenant_used_bytes", used_bytes)
    yield Metric("netapp_storagegrid_tenant_quota_bytes", quota_bytes)


check_plugin_netapp_storagegrid_tenant_quota = CheckPlugin(
    name="netapp_storagegrid_tenant_quota",
    service_name="NetApp StorageGRID Tenant Quota %s",
    sections=["netapp_storagegrid_tenants"],
    discovery_function=discover_netapp_storagegrid_tenant_quota,
    check_function=check_netapp_storagegrid_tenant_quota,
    check_ruleset_name="netapp_storagegrid_tenant_quota",
    check_default_parameters={"levels_upper": ("fixed", (80.0, 90.0))},
)
