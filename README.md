# Checkmk Special Agent: NetApp StorageGRID

> [!WARNING]
> Not usable right now

A Checkmk 2.5 special agent and check plugin family for monitoring
[NetApp StorageGRID](https://docs.netapp.com/us-en/storagegrid-119/) via its
Grid Management REST API.

## What it does

The special agent authenticates against the Grid Management API
(`POST /api/v3/authorize`) and fetches active alerts
(`GET /api/v3/grid/alerts`) as well as tenant account usage and quotas
(`GET /api/v3/grid/accounts-cache`). Two check plugins are shipped with
this package:

- **NetApp StorageGRID Alerts** reports the currently active alerts on
  the grid, grouped by severity (CRITICAL / MAJOR / MINOR).
- **NetApp StorageGRID Tenant Quota** reports, per tenant account, the
  percentage of the configured object quota that is currently used.

## Package layout

```
cmk_addons/plugins/netapp_storagegrid/
├── libexec/
│   └── agent_netapp_storagegrid       # the special agent executable
├── server_side_calls/
│   └── special_agent.py               # builds the special agent command line
├── rulesets/
│   ├── special_agent.py               # Setup rule: agent connection (host/credentials)
│   ├── alerts.py                      # Setup rule: check parameters (per-severity states)
│   └── tenant_quota.py                # Setup rule: check parameters (quota usage levels)
├── agent_based/
│   ├── alerts.py                      # parse/discover/check for the alerts service
│   └── tenant_quota.py                # parse/discover/check for the tenant quota service
└── checkman/
    ├── netapp_storagegrid_alerts      # man page shown in the Setup UI
    └── netapp_storagegrid_tenant_quota
```

## Installation

This source tree mirrors the layout Checkmk expects for a local extension
package (MKP). To install it on a Checkmk 2.5 site:

1. Copy the contents of `cmk_addons/plugins/netapp_storagegrid/` into
   `local/lib/python3/cmk_addons/plugins/netapp_storagegrid/` on the target
   site (or package it as an MKP with `mkp package` and install it via
   **Setup > Extension packages**).
2. Ensure `libexec/agent_netapp_storagegrid` is executable
   (`chmod +x`).
3. Restart the site / reload Checkmk so the new rule sets and plugins are
   picked up.

## Configuration

1. **Setup > Agents > Other integrations > NetApp StorageGRID**: configure
   the Grid Manager host, username, password, port/protocol and TLS
   certificate verification.
2. Assign the rule to the host representing the StorageGRID Admin Node.
3. Run service discovery. A **NetApp StorageGRID Alerts** service and one
   **NetApp StorageGRID Tenant Quota** service per tenant account will be
   discovered.
4. Optionally configure **NetApp StorageGRID alerts** (check parameters
   rule set) to change the monitoring state reported for each alert
   severity.
5. Optionally configure **NetApp StorageGRID tenant quota** (check
   parameters rule set) to change the WARN/CRIT levels for the percentage
   of a tenant's object quota that is used (default: WARN at 80%, CRIT at
   90%). Tenants without a configured quota are always reported OK.

## Notes on the API schema

NetApp's official documentation
(https://docs.netapp.com/us-en/storagegrid-119/) documents `alerts` as a
top-level Grid Management API resource and describes the CRITICAL / MAJOR /
MINOR severity model, but the full field-level JSON schema for individual
alert objects is only available live from a running system's Swagger UI
(`/grid/apidocs.html`). The parser in `agent_based/alerts.py` is therefore
deliberately defensive: it looks up several common field name variants
(`severity`, `message`/`description`, `hostName`/`nodeName`, `timeTriggered`)
and falls back to safe defaults instead of raising, so it should keep
working even if a given StorageGRID release uses slightly different field
names.

The tenant quota check uses `GET /api/v3/grid/accounts-cache` (documented in
`docu/grid-combined-schema.yaml`), which returns each tenant account's
`dataBytes` (used bytes) together with its `policy.quotaObjectBytes`
(configured object quota, `null` if unlimited) in a single call. This
endpoint has no pagination marker, so the agent requests a high `limit`
(500) to retrieve all tenants in one page; cached usage data can lag up to
15 minutes behind the actual state.

