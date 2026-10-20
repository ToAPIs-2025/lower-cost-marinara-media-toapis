# Standalone image/video model sampler

[English](README.md) · [中文](README_zh-CN.md)

Pricing checked 2026-10-20. Image examples are dated 2026-10-17; video examples 2026-10-20. Tables sort by example amount or case USD/s. Presets and input modes differ; this is not a matched-settings quality ranking. Unknown-phase image logs are not confirmed final net settlements. Current quotes and historical amounts are separate. Video charges are billing=settled; case USD/s divides charge by actual file duration, never processing time. Token tariffs appear in small text and do not imply a fixed per-second price.

gpt-image-2(VIP) starts at $0.0019/image; this low/1K preset is $0.0019/image. The standalone sampler has 31 historically successful image request templates and 8 video presets. Current-key pricing matches 26 image and 8 video presets; 5 image templates block new paid submission until an exact price is available.

New model support applies to this standalone API client. It does not register a native provider in the upstream product or expand its acceptance status.

```powershell
$env:TOAPIS_API_KEY="your_private_generation_key"
python unified_client.py --model gpt-image-2-vip --prompt "A tiny red robot beside a harbor kiosk"
python unified_client.py --model gpt-image-2-vip --prompt "A tiny red robot beside a harbor kiosk" --live
python unified_client.py --model MiniMax-H3-Max-Turbo --prompt "A tiny red robot walks slowly beside a harbor kiosk" --max-usd 1.50 --live
python unified_client.py --model seedance-2-mini --prompt "A gentle camera push-in" --image first-frame.png --max-usd 1.50 --live
```

Without --live, query the current-key price only. Default estimate thresholds are $0.20/image and $1.50/video; they are client-side estimate checks, not hard hosted-account spend caps. Token costs vary, so reserve headroom. Persist before POST; uncertain submissions are not retried. The same run ID resumes the task, while a different run ID creates a new paid job. Only the generation key is used; no account credentials or balances are queried. Result downloads carry no key.

Python standard library only. Run from this directory. Set the key through environment variables; .env.example is a placeholder and is not automatically loaded. Presets are fixed in presets.json; unsupported options are not forwarded. Images are generation-only; video modes are preset-specific T2V or one PNG first frame.

[Full current rates and real cases](https://github.com/ToAPIs-2025/toapis-quickstart/tree/main/tutorials/model-support-2026-10-20) · [Pricing API](https://docs.toapis.com/docs/en/api-reference/account/pricing)
