# Acceptance — 2026-10-21 native community build

Pinned Marinara 2.5.1 commit: `d0e481913f9a0e3bab0e9b767009500d0577f98a`. [Setup and scope](native/README.md) · [中文](native/README_zh-CN.md) · [Live evidence](evidence/marinara-native-2026-10-21.json).

| Layer | Result | Boundary |
|---|---|---|
| Build/check | Passed | Existing unrelated React hook warning; no errors |
| Backend regression | 22 passed | Mocked external HTTP; includes real Fastify save/masking, Test Image/Video, Gallery generation/download routes |
| UI gate regression | Desktop + mobile Edge passed | No installed Illustrator; video controls appear only with configured Roleplay video connection; zero paid API tasks |
| Real image | Passed | Actual application Gallery HTTP route, explicit prompt; Illustrator button not exercised |
| Real video | Passed | Native preview → Generate; ToAPIs first-frame upload; no media HTTP mocking |
| Real playback/download | Passed | Browser played MP4; download SHA-256 matches original |
| Real persistence | Passed | Image and video remain after refresh; no duplicate video; no page errors |
| Regional origin | `.cn` live passed | `.com` read-only passed, Node native generation connection timed out; no native live acceptance on `.com` |
| Billing | Video settled $0.13338 | Image $0.015 is a quote; two text logs total $0.000708 have unknown phase |
| Upstream official provider | Pending maintainer assessment | No merge or endorsement claimed |

Not yet verified: Illustrator capability install / Illustrate button, UI reference-image editing, mobile WebKit, other model variants or all accepted parameter combinations, multi-user concurrency, production deployment, automatic historical task recovery UI.

The separate 2026-10-20 API workflow and broader historical model sampler retain their own evidence. Their coverage must not be combined into a claim that every model works in the native adapter.
