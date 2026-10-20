# ToAPIs · Lower-cost Marinara Engine media guide

## Verified proposal workflow · 2026-10-20

The proposed external API chain has now completed: **scene image → uploaded URL reference edit → first-frame video**. The runnable [verification script](verify_marinara_flow.py), [protocol mapping](integration/proposed-media-contract.md), and [sanitized evidence](evidence/marinara-contract-2026-10-20.json) use the two models named in the proposed integration.

| Stage | Model / requested configuration | Result | Fee evidence |
| --- | --- | --- | --- |
| Text-to-image | gpt-image-2 / 1k / 16:9 | [PNG, 1696×960](examples/verified-2026-10-20/scene.png) | Current quote $0.015/image; task billing unavailable |
| URL-reference edit | gpt-image-2 / 1k / 16:9 / one uploaded reference | [PNG, 1696×960](examples/verified-2026-10-20/reference-edit.png) | Current quote $0.015/image; task billing unavailable |
| First-frame animation | seedance-2-mini / 4s / 480p tier / audio off | [MP4, 4.04s, 864×496, 97 decoded frames](examples/verified-2026-10-20/first-frame-mini.mp4) | Task settled $0.13338; this clip $0.033015/s |

The resolution/aspect-ratio fields are requested presets; actual file dimensions are shown above. The video fee is confirmed, while the two image quotes are not final net charges. The case USD/s is a conversion for this clip, not a fixed video tariff.

```bash
# Set TOAPIS_API_KEY privately in your environment first.
python verify_marinara_flow.py --max-usd 0.50
# Only this explicit flag submits paid tasks:
python verify_marinara_flow.py --max-usd 0.50 --live
```

Offline verification: 13 tests passed. **Native Marinara provider registration, Gallery import, Test Image/Test Video and in-app playback remain unverified.** Existing OpenAI/Seedance service contracts differ, so this is not a claim that changing their Base URL enables ToAPIs.


<!-- TOAPIS-MODELS-20261020 -->
## Model support and prices · 2026-10-20

Added standalone API presets: 31 image request templates and 8 video presets. Current-key pricing matches 26 image and 8 video presets; 5 image templates block new paid calls while pricing is unavailable. Native provider/UI/import/render acceptance remains as documented in the original guide below.

| Image model / tested preset | Current preset quote / image | Historical example amount / image | Fee evidence |
|---|---:|---:|---|
| gpt-image-2(VIP)<br><sub>low</sub> | $0.0019/image | **$0.0019/image** | Billing log, phase unknown |
| gpt-image-2.5-flare-vip<br><sub>low</sub> | Current-key quote unavailable | **$0.005272/image**<br><sub>Token-metered; current $/M unavailable. This sample is not a fixed image tariff.</sub> | Task receipt settled |
| nano_banana<br><sub>1K</sub> | $0.012/image | **$0.012/image** | Billing log, phase unknown |
| gemini-nano-banana-2.1<br><sub>1K</sub> | $0.015/image | **$0.015/image** | Billing log, phase unknown |
| gpt-image-2<br><sub>1K</sub> | $0.015/image | **$0.015/image** | Billing log, phase unknown |
| gemini-nano-banana-2.1-vip<br><sub>1K</sub> | $0.02/image | **$0.02/image** | Billing log, phase unknown |
| qwen-image-3.0<br><sub>1K</sub> | Current-key quote unavailable | **$0.021/image** | Billing log, phase unknown |
| gpt-image-2.5-flare<br><sub>high</sub> | $0.0225/image | **$0.0225/image** | Billing log, phase unknown |
| gpt-image-2.5-sunburst<br><sub>high</sub> | $0.0225/image | **$0.0225/image** | Billing log, phase unknown |
| flux-2-pro<br><sub>1K</sub> | $0.025/image | **$0.025/image** | Billing log, phase unknown |
| doubao-seedream-5-0-pro<br><sub>1K</sub> | $0.042857/image | **$0.042856/image** | Billing log, phase unknown |

| Video model | Preset / input | Settled clip charge | File duration | Case USD/s, ascending |
|---|---|---:|---:|---|
| MiniMax-H3-Max-Turbo | 5s / 480P / text-to-video | $0.125/clip | 5.18s | **$0.024131/s**<br><sub>Pricing tariff: $0.025/s</sub> |
| seedance-2-mini | 4s / 480p / first-frame | $0.13338/clip | 4.04s | **$0.033015/s**<br><sub>Pricing tariff: $3.285714/M total tokens</sub> |
| seedance-2-fast | 4s / 480p / text-to-video | $0.214568/clip | 4.04s | **$0.053111/s**<br><sub>Pricing tariff: $5.285714/M total tokens</sub> |
| kling-v3 | 5s / 720p / std / text-to-video | $0.3/clip | 5.04s | **$0.059524/s**<br><sub>Pricing tariff: $0.06/s</sub> |
| MiniMax-H3 | 5s / 768p / text-to-video | $0.32/clip | 5.17s | **$0.061896/s**<br><sub>Pricing tariff: $0.064/s</sub> |
| seedance-2 | 4s / 480p / first-frame | $0.26676/clip | 4.04s | **$0.06603/s**<br><sub>Pricing tariff: $6.571429/M total tokens</sub> |
| kling-3.0-turbo | 4s / 720p / text-to-video | $0.32/clip | 4.04s | **$0.079208/s**<br><sub>Pricing tariff: $0.08/s</sub> |
| seedance-2-5 | 4s / 480p / text-to-video | $0.3883/clip | 4.04s | **$0.096114/s**<br><sub>Pricing tariff: $10/M total tokens</sub> |

Pricing checked 2026-10-20. Image examples are dated 2026-10-17; video examples 2026-10-20. Tables sort by example amount or case USD/s. Presets and input modes differ; this is not a matched-settings quality ranking. Unknown-phase image logs are not confirmed final net settlements. Current quotes and historical amounts are separate. Video charges are billing=settled; case USD/s divides charge by actual file duration, never processing time. Token tariffs appear in small text and do not imply a fixed per-second price.

gpt-image-2(VIP) starts at $0.0019/image; this low/1K preset is $0.0019/image. The standalone sampler has 31 historically successful image request templates and 8 video presets. Current-key pricing matches 26 image and 8 video presets; 5 image templates block new paid submission until an exact price is available.

[Local sampler](toapis-models/README.md) · [Full price table](PRICING.md) · [Original media and fee evidence](https://github.com/ToAPIs-2025/toapis-quickstart/tree/main/tutorials/model-support-2026-10-20)

Original project examples, historical charges and integration instructions follow. Historical amounts are not rewritten as today’s quotes.

<!-- /TOAPIS-MODELS-20261020 -->

Original Marinara Engine media examples with three image models and a first-frame Seedance clip.

[中文](README_zh-CN.md) · [Model & pricing](https://go2v.toapis.com/1019_mari_g) · [Upstream](https://github.com/Pasta-Devs/Marinara-Engine)

**Community guide operated by ToAPIs.** The validated boundary is: Optional image/scene-video API bridge; adult non-explicit fantasy environment example, full app pending. Individual project UI acceptance is listed below.

## Demo

![Three image models and their dated prices](social/image-comparison-en.png)

[![Play seedance-2 example](examples/video-preview.jpg)](examples/seedance-2.mp4)

**[Open / download the video](examples/seedance-2.mp4)** — $0.26676, API-settled; 4.04s decoded, 480p, first-frame input, no audio. This example is $0.06603/s; a case conversion, not a fixed per-second tariff.

## Model pricing and case amounts

Tested on 2026-10-19. Sorted from low to high by the displayed case amount. Image amounts marked **Quoted** are current configured per-request rates, not task-confirmed net settlements. Video amounts use settled API receipts.

| Model / tested preset | Type | Case amount / quote | Applicable model rate | Fee evidence |
|---|---|---:|---|---|
| gpt-image-2(VIP)<br>low / 1K | image | Quoted $0.0019 | $0.0019/image | Matched current rate; individual task billing unavailable; same-model batch logs recorded separately |
| gpt-image-2<br>1K | image | Quoted $0.015 | $0.015/image | Matched current rate; individual task billing unavailable; same-model batch logs recorded separately |
| gpt-image-2.5-flare<br>high / 1K | image | Quoted $0.0225 | $0.0225/image | Matched current rate; individual task billing unavailable; same-model batch logs recorded separately |
| seedance-2<br>4s requested / 480p / 4.04s decoded / no audio | video | $0.26676 | $6.571429/1M total tokens; this clip $0.06603/s | API billing=settled |

`gpt-image-2(VIP)` starts at **$0.0019/image**; this guide uses **low / 1K at $0.0019/image**. The API ID is `gpt-image-2-vip`. Prices apply to the shown configuration; requested 1K does not guarantee a fixed pixel size. Original output dimensions are in each evidence file.

Seedance token rates and case USD/s have different units. The clip fee excludes its separately listed first-frame image. Token-rate estimates do not lock a final charge.

## Reuse

Python 3.10+ for the standalone API examples. Copy `.env.example` to a private `.env`, configure your Key and a separate random local bridge token of at least 24 characters if using the optional bridge. Keep both private.

```bash
python run_case.py --job jobs/gpt-image-2-vip.json
# Review the current quote, then deliberately submit once:
python run_case.py --job jobs/gpt-image-2-vip.json --live
# Optional OpenAI-compatible bridge, loopback only:
python bridge.py
```

[Project-specific configuration and limits](integration/README.md). Saved state resumes the same task. A lost submit response stops for reconciliation; it is not an instruction to submit again. Use a new `run_id` only for a deliberate new paid example.

The server queries `/v1/pricing` with the same generation Key, submits to `/v1/images/generations` or `/v1/videos/generations`, polls the corresponding task path, and reads `billing` when available. It returns PNG/base64 to synchronous image consumers and adapts the supported multipart image-to-video route. Unsupported edit, chat and speech routes fail explicitly.

## Tested scope

[Detailed acceptance notes](ACCEPTANCE.md) · [Public evidence](evidence/) · [Input jobs](jobs/) · [Provider/recipe](integration/)

Inspected upstream revision: [`c56501495a8b`](https://github.com/Pasta-Devs/Marinara-Engine/commit/c56501495a8baf76c258e76534c8728a9b7859bb). Generated assets and API-boundary checks do not establish full upstream app integration or maintainer endorsement.

## Original prompt

```text
Cinematic 16:9 fantasy role-playing game scene illustration, an empty moonlit alchemist workshop in a coastal tower, brass instruments, blue glass bottles, an open star chart on a wooden desk, a candle, ocean visible through an arched window, painterly realism, calm atmospheric worldbuilding, no characters, no text, no watermark.
```

## References

- [Upstream project](https://github.com/Pasta-Devs/Marinara-Engine)
- [Pricing and actual charges](https://docs.toapis.com/docs/en/api-reference/account/pricing)
- [Try the matching image model](https://go2v.toapis.com/1019_mari_g)
- [Video model page](https://go2.toapis.com/1019_mari_v)

This guide is independently operated by ToAPIs and is not affiliated with, endorsed by, or supported by Pasta-Devs.
