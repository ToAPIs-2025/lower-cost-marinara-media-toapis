"""Create isolated local Marinara connections. Never submits a paid API task."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlparse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def app_call(app, path, body=None, method=None, timeout=60):
    u = urlparse(app)
    if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost') or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('Use a local HTTP Marinara origin, e.g. http://127.0.0.1:17863')
    req = urllib.request.Request(app.rstrip('/') + '/api/' + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method or ('POST' if body is not None else 'GET'),
        headers={**({'Content-Type': 'application/json'} if body is not None else {}), 'x-marinara-csrf': '1', 'Origin': app.rstrip('/')})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError('Local Marinara HTTP ' + str(exc.code)) from None


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', choices=['cn', 'com'], default='cn')
    parser.add_argument('--app', default='http://127.0.0.1:17863')
    parser.add_argument('--state', type=Path, default=Path(__file__).parent / '.private/setup.json')
    parser.add_argument('--apply', action='store_true', help='Create local connections and a new Roleplay chat; no paid calls')
    args = parser.parse_args()
    base = 'https://toapis.' + args.site + '/v1'
    if not args.apply:
        print(json.dumps({'mode': 'plan_only', 'base_url': base, 'models': ['gpt-image-2', 'seedance-2-mini', 'deepseek-v4-flash'], 'paid_tasks': 0}))
        return
    key = os.environ.get('TOAPIS_API_KEY', '').strip()
    if not key:
        raise ValueError('Set TOAPIS_API_KEY privately before --apply')
    state = json.loads(args.state.read_text(encoding='utf-8')) if args.state.exists() else {}
    if state and (state.get('app') != args.app or state.get('base_url') != base):
        raise ValueError('Existing setup uses another app/site; select a separate --state file')
    state.update(app=args.app, base_url=base)
    state.setdefault('connections', {})
    save(args.state, state)
    for kind, model in [('image', 'gpt-image-2'), ('video', 'seedance-2-mini'), ('text', 'deepseek-v4-flash')]:
        if kind in state['connections']:
            app_call(args.app, 'connections/' + state['connections'][kind])
            continue
        if state.get('creating'):
            raise RuntimeError('A previous local creation response was lost. Reconcile in Connections before changing the private state.')
        payload = {'name': 'ToAPIs ' + kind + ' (community adapter)', 'provider': kind + '_generation' if kind != 'text' else 'custom',
            'baseUrl': base, 'apiKey': key, 'model': model, 'defaultForAgents': False, 'maxContext': 32768}
        if kind == 'image':
            payload.update(imageService='openai', imageGenerationSource='openai', imageGenerationQuality='auto')
        elif kind == 'video':
            payload.update(videoService='seedance', videoGenerationSource='seedance')
        state['creating'] = kind
        save(args.state, state)
        row = app_call(args.app, 'connections/', payload)
        state['connections'][kind] = row['id']
        state.pop('creating', None)
        save(args.state, state)
    # Creation drops defaultParameters: use the separate route and a JSON OBJECT.
    app_call(args.app, 'connections/' + state['connections']['video'] + '/default-parameters', {
        'videoGeneration': {'version': 1, 'service': 'seedance', 'seedance': {
            'durationSeconds': 4, 'resolution': '480p', 'aspectRatio': '16:9',
            'temporaryPublicReferenceUploadEnabled': False, 'temporaryPublicReferenceUploadExpiry': '12h'}}}, 'PUT')
    if not state.get('chat_id'):
        if state.get('creating'):
            raise RuntimeError('Reconcile previous chat creation before repeating')
        state['creating'] = 'chat'
        save(args.state, state)
        chat = app_call(args.app, 'chats', {'name': 'ToAPIs scene demo', 'mode': 'roleplay', 'characterIds': [], 'connectionId': state['connections']['text']})
        state['chat_id'] = chat['id']
        state.pop('creating', None)
        save(args.state, state)
    app_call(args.app, 'chats/' + state['chat_id'] + '/metadata', {
        'sceneVideoConnectionId': state['connections']['video'],
        'illustratorImageConnectionId': state['connections']['image'],
        'illustratorPromptConnectionId': state['connections']['text'],
        'enableAgents': False, 'activeAgentIds': []}, 'PATCH')
    print('Configured local demo chat. API key remains in Marinara storage; setup made 0 paid calls.')


if __name__ == '__main__':
    main()
