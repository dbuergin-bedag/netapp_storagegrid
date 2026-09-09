#!/usr/bin/env python3
# Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Check plugin for currently active alerts on a NetApp StorageGRID cluster.

The special agent fetches the list of alerts from the Grid Management REST
API (GET /api/v3/grid/alerts), whose response looks like this (see the
StorageGRID Grid Management API documentation)::

    {
      "data": [
        {
          "id": "29ceeab5f2762acb",
          "name": "Low metadata storage",
          "annotations": {"description": "The space available ...", "ruleId": "LowMetadataStorage"},
          "inhibited": true,
          "inhibitedBy": ["ca8385152dae09c7"],
          "labels": {"severity": "critical", "instance": "DC1-S1", "site_name": "Data Center 1"},
          "silenced": true,
          "silencedBy": ["dde19261-4c59-42d7-8bd3-41976b95fda6"],
          "startsAt": "2026-09-09T12:20:26.387Z",
          "status": "active"
        }
      ]
    }
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    State,
    StringTable,
)

Alert = Mapping[str, Any]
Section = Sequence[Alert]

# Severities as used in the "labels.severity" field of the StorageGRID alerts API.
_SEVERITIES = ("CRITICAL", "MAJOR", "MINOR")

_STATE_PARAM_KEYS = {
    "CRITICAL": "state_critical",
    "MAJOR": "state_major",
    "MINOR": "state_minor",
}


def _normalize(raw_alert: Mapping[str, Any]) -> Alert:
    labels = raw_alert.get("labels")
    labels = labels if isinstance(labels, Mapping) else {}
    annotations = raw_alert.get("annotations")
    annotations = annotations if isinstance(annotations, Mapping) else {}

    severity = str(labels.get("severity") or "unknown").upper()
    name = str(raw_alert.get("name") or labels.get("alertname") or "Unknown alert")
    description = str(annotations.get("description") or name)
    node = str(labels.get("instance") or "unknown")
    site = str(labels.get("site_name") or "")

    return {
        "id": str(raw_alert.get("id", "unknown")),
        "severity": severity,
        "name": name,
        "message": description,
        "node": node,
        "site": site,
        "time": str(raw_alert.get("startsAt", "")),
        "status": str(raw_alert.get("status", "active")).lower(),
        "silenced": bool(raw_alert.get("silenced", False)),
        "inhibited": bool(raw_alert.get("inhibited", False)),
    }


def parse_netapp_storagegrid_alerts(string_table: StringTable) -> Section:
    if not string_table:
        return []

    raw = json.loads(string_table[0][0])
    alerts = raw if isinstance(raw, list) else raw.get("data", [])
    return [
        _normalize(alert)
        for alert in alerts
        if isinstance(alert, Mapping) and str(alert.get("status", "active")).lower() == "active"
    ]


agent_section_netapp_storagegrid_alerts = AgentSection(
    name="netapp_storagegrid_alerts",
    parse_function=parse_netapp_storagegrid_alerts,
)


def discover_netapp_storagegrid_alerts(section: Section) -> DiscoveryResult:  # noqa: ARG001
    # We cannot guess items from alerts: an empty list of alerts does not mean
    # there is nothing to monitor, so we always discover a single service.
    yield Service()


def check_netapp_storagegrid_alerts(
    params: Mapping[str, Any],
    section: Section,
) -> CheckResult:
    relevant = [
        alert
        for alert in section
        if not (params.get("ignore_silenced", True) and alert["silenced"])
        and not (params.get("ignore_inhibited", True) and alert["inhibited"])
    ]
    ignored_total = len(section) - len(relevant)

    counts: dict[str, int] = {severity: 0 for severity in _SEVERITIES}
    for alert in relevant:
        counts[alert["severity"]] = counts.get(alert["severity"], 0) + 1

    overall_state = State.OK
    for severity in _SEVERITIES:
        if counts.get(severity):
            overall_state = State.worst(overall_state, State(params[_STATE_PARAM_KEYS[severity]]))

    known_total = sum(counts.get(severity, 0) for severity in _SEVERITIES)
    other_total = len(relevant) - known_total

    summary = (
        f"{len(relevant)} alerts "
        f"(Critical: {counts['CRITICAL']}, Major: {counts['MAJOR']}, Minor: {counts['MINOR']})"
    )
    if ignored_total:
        summary += f", {ignored_total} silenced/inhibited alert(s) ignored"
    yield Result(state=overall_state, summary=summary)

    yield Metric("netapp_storagegrid_alerts_critical", counts["CRITICAL"])
    yield Metric("netapp_storagegrid_alerts_major", counts["MAJOR"])
    yield Metric("netapp_storagegrid_alerts_minor", counts["MINOR"])

    if other_total:
        yield Result(
            state=State.OK,
            notice=f"{other_total} alert(s) with unrecognized severity",
        )

    for alert in sorted(relevant, key=lambda a: a["time"], reverse=True)[:20]:
        site = f" ({alert['site']})" if alert["site"] else ""
        yield Result(
            state=State.OK,
            notice=(
                f"{alert['time']}\t[{alert['severity']}] {alert['node']}{site}: "
                f"{alert['name']} - {alert['message']}"
            ),
        )


check_plugin_netapp_storagegrid_alerts = CheckPlugin(
    name="netapp_storagegrid_alerts",
    service_name="NetApp StorageGRID Alerts",
    discovery_function=discover_netapp_storagegrid_alerts,
    check_function=check_netapp_storagegrid_alerts,
    check_ruleset_name="netapp_storagegrid_alerts",
    check_default_parameters={
        "state_critical": int(State.CRIT),
        "state_major": int(State.WARN),
        "state_minor": int(State.WARN),
        "ignore_silenced": True,
        "ignore_inhibited": True,
    },
)
