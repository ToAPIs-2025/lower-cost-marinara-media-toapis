# Proposed Marinara media contract and runnable verification

This is an independent ToAPIs API workflow. It does not add a provider to Marinara Engine.

## Run the exact proposal workflow

Requires Python 3.10+ and a private ToAPIs generation Key in the environment. Run from the repository root:

```bash
export TOAPIS_API_KEY='YOUR_PRIVATE_KEY'
python verify_marinara_flow.py --max-usd 0.50
# Quote only above. Deliberately create the three tasks:
python verify_marinara_flow.py --max-usd 0.50 --live
```

PowerShell uses `$env:TOAPIS_API_KEY = 'YOUR_PRIVATE_KEY'` instead of `export`. The script does not print the Key or require an account access token.

The workflow performs:

1. **Text-to-image:** `gpt-image-2`, `size: "16:9"`, `resolution: "1k"`, `n: 1`.
2. **Reference image edit:** upload the generated scene, then use its returned HTTPS URL in `reference_images` on the same image-generation endpoint.
3. **First-frame video:** upload the edited scene, then use `seedance-2-mini`, 4 seconds, 480p, `generate_audio: false`, and `image_with_roles: [{url, role: "first_frame"}]`.

`--max-usd` checks the combined current forecast. A token-based video forecast is not an upstream billing limit or a locked final charge. Receipts retain the actual settled charge when supplied by the API; missing billing stays unknown.

Saved state is under `.toapis-state/marinara-flow/`. Repeating the same run resumes its task receipts. A missing submission response stops the run for reconciliation. Changing `--run-id` is an explicit request for a new paid run.

## Request and response mapping

| Step | Method and route | Required mapping |
| --- | --- | --- |
| Upload an input | POST /v1/uploads/images, multipart file | Read data.url; use the real returned HTTPS URL |
| Create image | POST /v1/images/generations | Top-level model, prompt, size, resolution, n; reference_images for edits |
| Query image | GET /v1/images/generations/{id} | Retain the top-level task id |
| Create video | POST /v1/videos/generations | Top-level model, prompt, duration, aspect_ratio, resolution, generate_audio, image_with_roles |
| Query video | GET /v1/videos/generations/{id} | Retain the top-level task id |
| Finished task | status completed | Download result.data[0].url |
| Failed task | status failed | Surface error; do not silently submit another paid task |

The specific image model tested here is ordinary `gpt-image-2`. Other GPT Image channels and tiers can have different edit routes and size formats.

## Why changing a Base URL is insufficient

Inspected Marinara main commit: `c56501495a8baf76c258e76534c8728a9b7859bb`.

- Custom OAI is documented as a chat-format connection.
- Its OpenAI image result parser expects top-level `data[]`, while this ToAPIs image route returns an asynchronous task; GPT Image reference edits also use a different input route.
- Its existing Seedance service nests generation parameters under `input` and queries `/v1/tasks/{id}`. The ToAPIs route above uses top-level parameters and `/v1/videos/generations/{id}`.

These differences justify evaluating a media service adapter. They are not defects in adapters written for other providers. Another existing service may be reusable; that remains for the maintainer to confirm.

## Verification boundary

The runnable script checks the external API task chain. It does not prove native Test Image/Test Video, Gallery import, scene-video connection selection, or in-app playback.

The optional `bridge.py` is a separate generic loopback API bridge. This guide does not configure Marinara's existing xAI or Seedance services to use it. Marinara-side implementation remains with its maintainers, following their requested feature process.

Official API references: [GPT Image 2](https://docs.toapis.com/docs/cn/api-reference/images/gpt-image-2/generation), [Seedance 2](https://docs.toapis.com/docs/cn/api-reference/videos/seedance-2/generation), [image upload](https://docs.toapis.com/docs/cn/api-reference/uploads/images), [image status](https://docs.toapis.com/docs/cn/api-reference/tasks/image-status), [video status](https://docs.toapis.com/docs/cn/api-reference/tasks/video-status).

Run offline checks with `python -m unittest discover -s tests -v`. Only adding `--live` to the separate verification command performs paid generation.
