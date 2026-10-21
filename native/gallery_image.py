"""Quote one scene image; --live creates it through the actual local app route."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from configure import app_call, save

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'toapis-models'))
from unified_client import Client
from toapis_billing import current_price


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, default=Path(__file__).parent / '.private/setup.json')
    p.add_argument('--prompt', required=True)
    p.add_argument('--run-id', default='scene-1', help='A new ID deliberately authorizes a separate paid image')
    p.add_argument('--max-usd', default='0.02')
    p.add_argument('--live', action='store_true')
    a = p.parse_args()
    state = json.loads(a.state.read_text(encoding='utf-8'))
    client = Client(base=state['base_url'].removesuffix('/v1'), state=a.state.parent / 'pricing')
    # Fail closed if a different connection/model is selected in the app.
    connection = app_call(state['app'], 'connections/' + state['connections']['image'])
    if connection.get('model') != 'gpt-image-2' or connection.get('baseUrl') != state['base_url']:
        raise ValueError('Restore the configured ordinary gpt-image-2 connection and site')
    quote = current_price(client.json, 'gpt-image-2', 'image', {'resolution': '1K', 'n': 1, 'input_image_count': 0})
    maximum = Decimal(a.max_usd)
    price = Decimal(quote['maximum_unit_price'])
    if not maximum.is_finite() or maximum <= 0 or quote['unit'] != 'request' or price > maximum:
        raise ValueError('Image quote missing, ambiguous, or over --max-usd')
    print(json.dumps({'model': 'gpt-image-2', 'quote_usd': str(price), 'is_final_charge': False, 'live': a.live}))
    if not a.live:
        return
    identity = hashlib.sha256((a.run_id + '\0' + state['app'] + '\0' + state['chat_id']).encode()).hexdigest()[:24]
    receipt_path = a.state.parent / ('gallery-' + identity + '.json')
    if receipt_path.exists():
        raise RuntimeError('This run already has a receipt. Inspect Gallery and private server toapis-tasks; do not repeat the POST automatically.')
    receipt = {'run_id': a.run_id, 'status': 'submission_started', 'quote_usd': str(price)}
    save(receipt_path, receipt)
    # No automatic paid retry. The server separately persists the provider task ID.
    row = app_call(state['app'], 'gallery/' + state['chat_id'] + '/generate-image',
        {'prompt': a.prompt, 'promptOverride': a.prompt}, timeout=1200)
    receipt.update(status='completed', gallery_image_id=row['id'])
    save(receipt_path, receipt)
    print('Image saved in the demo chat Gallery. Open it to preview or animate.')


if __name__ == '__main__':
    main()
