# Marinara Engine integration paths

## Native community adapter — 2026-10-21

Use the [English setup guide](../native/README.md) or [中文配置](../native/README_zh-CN.md) for the pinned source patch, domestic/international Base URLs, three connection types, repeatable setup, prices and live results. Real Gallery generation and native first-frame video review/playback/download/persistence passed. The source patch is **not merged upstream** and supports ordinary `gpt-image-2` plus `seedance-2-mini` only. Custom OAI remains the existing text path.

## Independent API recipe — historical 2026-10-20

`verify_marinara_flow.py` remains a separate two-image / one-video external contract check. [Request mapping](proposed-media-contract.md) and [historical evidence](../evidence/marinara-contract-2026-10-20.json) cover an uploaded URL reference edit that has not been live-tested through the native UI.

`run_case.py`, `bridge.py` and `toapis-models/` are standalone utilities. Do not point the stock xAI adapter at the loopback bridge or assume their broader model coverage is native support. ToAPIs async task IDs, polling routes and reference fields need explicit mapping.

This guide is independently maintained by ToAPIs. The native derivative patch is distributed with its [AGPL-3.0 license](../native/LICENSE); no upstream endorsement or official provider status is claimed. Original non-explicit environment assets are included as test evidence.
