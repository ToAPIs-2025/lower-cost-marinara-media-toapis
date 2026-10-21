# ToAPIs inside Marinara Engine — tested community adapter

[中文配置](README_zh-CN.md) · [API documentation](https://docs.toapis.com/docs/cn/quickstart) · [Models and pricing](https://go2v.toapis.com/1019_mari_g)

Generate a scene image in Marinara's Gallery, then animate it through its native video review and playback UI. On **2026-10-21** we completed this flow in a locally patched Marinara **2.5.1**, pinned to upstream [`d0e4819`](https://github.com/Pasta-Devs/Marinara-Engine/commit/d0e481913f9a0e3bab0e9b767009500d0577f98a). This is a community adapter for assessment; it is not merged into or endorsed by upstream. An unmodified Marinara installation cannot enable this asynchronous media contract just by changing Base URL.

![Native Marinara video playback](../examples/native-2026-10-21/03-native-video-playing.png)

## Choose the correct website and API URL

Choose according to **the machine running the Marinara server**. For a server in mainland China, official documentation recommends `toapis.cn`; use `toapis.com` for an international deployment where reachable. The live native test used `.cn`. Both origins passed read-only model/pricing requests with the test key, but live native generation on `.com` was not completed: its Node connection timed out in this environment.

| Setting | Mainland China | International |
|---|---|---|
| Website / account entry | https://toapis.cn | https://toapis.com |
| Marinara / OpenAI SDK Base URL | `https://toapis.cn/v1` | `https://toapis.com/v1` |
| Standalone scripts `TOAPIS_BASE_URL` | `https://toapis.cn` | `https://toapis.com` |
| Image create | `https://toapis.cn/v1/images/generations` | `https://toapis.com/v1/images/generations` |
| Image query | `https://toapis.cn/v1/images/generations/{id}` | `https://toapis.com/v1/images/generations/{id}` |
| Video create | `https://toapis.cn/v1/videos/generations` | `https://toapis.com/v1/videos/generations` |
| Video query | `https://toapis.cn/v1/videos/generations/{id}` | `https://toapis.com/v1/videos/generations/{id}` |
| Reference upload | `https://toapis.cn/v1/uploads/images` | `https://toapis.com/v1/uploads/images` |
| Text / Prompt Model | `https://toapis.cn/v1/chat/completions` | `https://toapis.com/v1/chat/completions` |

Do not use `/login`, the documentation website, or `/v1/v1` as Base URL. Enter your generation API key from the chosen site's console. This test does not establish that all accounts, prices or regional policies are identical. See the [official quickstart](https://docs.toapis.com/docs/cn/quickstart). No project-specific attribution campaign is created by this patch.

## Install a separate test instance

Requires Git, Python 3.10+, Node **>=24 <27**, and **pnpm 10.34.5**. Download/clone this entire guide repository first; the helper imports the existing `toapis-models` billing utilities. Allow several GB for dependencies. Keep the checkout, pnpm store, application data and temporary files on a roomy drive. Do not overwrite a working installation.

Windows PowerShell, from this guide's repository root:

```powershell
# Install the pinned pnpm separately if needed: npm install -g pnpm@10.34.5
.\native\Install-CommunityAdapter.ps1 -Target 'D:\Marinara-ToAPIs'
Set-Location 'D:\Marinara-ToAPIs'
$env:DATA_DIR='D:\Marinara-ToAPIs-data'
$env:FILE_STORAGE_DIR='D:\Marinara-ToAPIs-data\storage'
$env:TEMP='D:\Marinara-ToAPIs-temp'; $env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:DATA_DIR,$env:FILE_STORAGE_DIR,$env:TEMP | Out-Null
$env:PORT='17863'; $env:HOST='127.0.0.1'
$env:MARINARA_LITE='true'; $env:AUTO_CREATE_DEFAULT_CONNECTION='false'
$env:AUTO_OPEN_BROWSER='false'; $env:UPDATES_APPLY_DISABLED='true'
node packages/server/dist/index.js
```

The installer fetches the pinned commit, checks and applies [the six-file patch](toapis-media.patch), installs dependencies with a frozen lockfile, and runs `pnpm check`. It never configures credentials or submits a paid task. The sparse checkout omits optional large artwork/Illustrator packages; install optional capabilities through Marinara separately if wanted. Standard dependencies are required; the published recipe does not depend on our private development runtime. On other systems fetch the same commit, run `git apply --check` and `git apply` with this patch, then `pnpm install --frozen-lockfile` and `pnpm check`.

## Configure image, video and text separately

| Marinara connection | Provider / service | Model ID | Important setting |
|---|---|---|---|
| Image generation | OpenAI image (`openai`) | `gpt-image-2` | Quality **Auto**; adapter uses ordinary 1k, one image |
| Video generation | Seedance (`seedance`) | `seedance-2-mini` | Defaults **4s / 480p / 16:9**, audio off |
| Text / Prompt Model | Custom OAI (`custom`) | `deepseek-v4-flash` | Used to draft the native video prompt; separately billed |

Use the same chosen `/v1` Base URL and your private key in all three. The service labels reuse existing UI entries; the patch selects the ToAPIs task protocol only for the two exact HTTPS hosts. Other providers retain their original paths. Never select a VIP model in this adapter. [Domestic JSON example](connections.cn.example.json) · [International JSON example](connections.com.example.json).

For repeatable local setup, open a **second** terminal at this guide's repository root:

```powershell
python native/configure.py --site cn
# Set TOAPIS_API_KEY privately in the terminal, then:
python native/configure.py --site cn --apply
```

The default command only prints a plan. `--apply` creates three local connections and a separate Roleplay demo chat, sets its image/video/Prompt Model selections, and makes **zero paid generation calls**. It does not change global default connections. Keep the same key in `TOAPIS_API_KEY` when checking prices. Local IDs, not the key, are saved to ignored `native/.private/setup.json`. Repeating setup reuses saved IDs. A lost local creation response stops for reconciliation rather than blindly creating duplicates.

**Video defaults must be saved with `PUT /api/connections/{id}/default-parameters` and a JSON object.** Passing `defaultParameters` while creating a connection is insufficient in this pinned version. The helper performs the correct PUT. In the UI, select this video connection in Roleplay → Chat Settings → Agents / Scene Videos, and select a text connection for the chat's Prompt Model. Enable prompt review before sending and confirm the preview shows **4s / 480p** before clicking Generate. Image canvas dimensions are controlled in Marinara's image/background settings; the live image used 1280×720 as input ratio, with an actual output of 1696×960.

## Generate and animate

The real image test used the actual local Gallery HTTP route with an explicit prompt, not the optional Illustrator agent's Illustrate button. To reproduce that path:

```powershell
python native/gallery_image.py --prompt 'An empty moonlit coastal observatory, painterly realism, no people, no text' --max-usd 0.02
# Deliberately create ONE paid image after reviewing the quote:
python native/gallery_image.py --prompt 'An empty moonlit coastal observatory, painterly realism, no people, no text' --max-usd 0.02 --live
```

The helper checks the selected ordinary model/site and the current key-scoped image quote before submission. It refuses an existing run receipt and never retries a paid POST. A new `--run-id` explicitly requests a different image. The API key used to quote must be the one configured in Marinara. The quote is not a provider-enforced spending cap. Refresh the demo chat, open Chat Settings → Gallery → **Animate gallery illustration**, review the prompt and parameters, then Generate. Video generation and the text prompt are additional paid calls. Watch the clip, use Download, and refresh to confirm persistence. You can instead upload your own image to Gallery before animating.

The local patch stores private task receipts under `DATA_DIR/toapis-tasks` before submitting. If a submission response is lost, stop and reconcile that receipt/account usage; do not repeat Generate automatically. Cancellation or a polling failure does not cancel upstream billing. Receipts retain task identity but this patch does not offer an automatic historical-resume UI or live billing panel. Keep receipts, prompts and API keys private.

## Prices and actual API costs — 2026-10-21

| Item | Current rate / quote | This native test |
|---|---|---|
| `gpt-image-2`, ordinary 1k, n=1 | **$0.015/image** key-scoped quote | 1 PNG; task billing unavailable, final debit unknown |
| `seedance-2-mini` | **$3.285714 / 1M total tokens** | First-frame clip requested 4s/480p; task **settled $0.13338** |
| Same video, normalized to actual 4.04s | **$0.033015/s for this case** | Case conversion only; not a fixed per-second tariff |
| `deepseek-v4-flash` | Public default-group reference: **$0.20/M input, $0.80/M output** | Two matching model/time-window logs: $0.000264 + $0.000444 = **$0.000708**, billing phase unknown |

Only **$0.13338** is confirmed media settlement for this run. Do not add the image quote or unknown-phase text logs to claim a fully settled total. The first video preview exposed wrong defaults and was stopped before video submission; that is why two text logs exist for one video. Text rates are public catalog references, not a `/v1/pricing` text quote: that endpoint currently covers image/video only. Actual account group, routing, model settings and time-based prices can differ. Check your console and [key-scoped pricing documentation](https://docs.toapis.com/docs/en/api-reference/account/pricing) before a new run.

## Evidence and test boundary

| Check | Result |
|---|---|
| `pnpm check` | Passed: localization, format, lint, types, production build; one existing unrelated hook warning |
| Official ToAPIs regression runner | **22 checks passed**, media HTTP mocked, zero paid tasks |
| UI gate regression | **2 passed**, desktop and mobile Edge viewports; no paid tasks |
| Real app image route | PNG 1696×960, fully decoded, 90.01s |
| Real UI first-frame video | 4.04s, 864×496, 24fps, 97 decoded frames, no audio, 92.585s |
| Playback, download, refresh | Browser played clip; downloaded SHA-256 matches original; 1 image + 1 video remain after refresh; no page errors |

[Sanitized live result](../evidence/marinara-native-2026-10-21.json) · [Regression summary](checks-2026-10-21.md) · [Native prompt review](../examples/native-2026-10-21/02-native-video-review.png) · [Image](../examples/native-2026-10-21/scene.png) · [MP4](../examples/native-2026-10-21/scene-video.mp4) · [Gallery after refresh](../examples/native-2026-10-21/04-gallery-after-refresh.png).

Still unverified: installing/using the optional Illustrator agent, native UI image-reference editing, mobile WebKit, other model variants, concurrent users and production deployment. Supported validation ranges (image ratios; video 4–15s and 480p/720p/1080p) are wider than the single real preset above. They must not be presented as fully live-tested combinations. Test Image/Test Video endpoints passed with mocked provider responses; they were not additional real paid button tests.

This folder distributes a derivative patch against Marinara under **AGPL-3.0**; see [LICENSE](LICENSE). ToAPIs does not claim official provider status. The older independent multi-model sampler remains separate and does not expand the native patch's two-model support.
