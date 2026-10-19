"""Loopback image/video compatibility bridge. Never expose the API key to a UI."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
import base64,json,os,hmac,threading
from media_engine import MediaEngine,IMAGE_MODELS,VIDEO_MODELS

class Bridge(ThreadingHTTPServer):
    def __init__(self,address,engine,token):
        if address[0]!='127.0.0.1':raise ValueError('Bridge must bind to loopback')
        if not token or len(token)<24:raise ValueError('Set a separate BRIDGE_TOKEN of at least 24 characters')
        self.engine=engine;self.token=token;self.active=set();self.active_lock=threading.Lock()
        super().__init__(address,Handler)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,status,obj):
        raw=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def authorized(self):
        return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+self.server.token)
    def do_GET(self):
        if not self.authorized():return self.send_json(401,{'error':{'message':'Bridge authentication required'}})
        path=urlparse(self.path).path
        if path=='/v1/models':return self.send_json(200,{'object':'list','data':[{'id':m,'object':'model','type':'image' if m in IMAGE_MODELS else 'video'} for m in IMAGE_MODELS+VIDEO_MODELS]})
        if path.startswith('/v1/videos/'):
            parts=path.split('/');ident=parts[3]
            if len(ident)!=64 or any(c not in '0123456789abcdef' for c in ident):return self.send_json(404,{'error':{'message':'Unknown local job'}})
            file=self.server.engine.state/(ident+'.json')
            if not file.exists():return self.send_json(200,{'id':ident,'object':'video','status':'in_progress','progress':0})
            r=json.loads(file.read_text(encoding='utf-8'))
            if path.endswith('/content'):
                if r['status']!='completed':return self.send_json(409,{'error':{'message':'Video is not complete'}})
                raw=Path(r['output']).read_bytes();self.send_response(200);self.send_header('Content-Type','video/mp4');self.send_header('Content-Length',str(len(raw)));self.end_headers();return self.wfile.write(raw)
            status='completed' if r['status']=='completed' else 'failed' if r['status'] in ('failed','cancelled','expired','submission_uncertain') else 'in_progress'
            return self.send_json(200,{'id':ident,'object':'video','status':status,'progress':100 if status=='completed' else 0,'model':r['job']['model'],'billing':r.get('cost'),'video':{'url':r.get('source_url')} if status=='completed' else None})
        return self.send_json(404,{'error':{'message':'Unsupported route'}})
    def do_POST(self):
        if not self.authorized():return self.send_json(401,{'error':{'message':'Bridge authentication required'}})
        path=urlparse(self.path).path
        if path not in ('/v1/images/generations','/v1/videos'):return self.send_json(400,{'error':{'message':'Editing, chat and speech are not enabled'}})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>11*1024*1024:raise ValueError('Payload must be between 1 byte and 11 MiB')
            content_type=self.headers.get('Content-Type','');payload=self.rfile.read(size)
            kind='image' if path=='/v1/images/generations' else 'video'
            if content_type.split(';')[0]=='application/json':
                if size>65536:raise ValueError('JSON payload exceeds 64 KiB')
                body=json.loads(payload)
            elif kind=='video' and content_type.startswith('multipart/form-data;'):
                mime=BytesParser(policy=default).parsebytes(('Content-Type: '+content_type+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+payload)
                body={};reference=None
                for part in mime.iter_parts():
                    name=part.get_param('name',header='content-disposition')
                    if name in body:raise ValueError('Duplicate multipart parameter')
                    raw=part.get_payload(decode=True)
                    if name=='input_reference':
                        if reference is not None:raise ValueError('Duplicate first frame')
                        reference=raw
                    elif name in ('model','prompt','size','seconds','run_id'):body[name]=raw.decode('utf-8')
                    else:raise ValueError('Unmapped multipart parameter')
                if reference is None:raise ValueError('A first-frame PNG is required')
                body['image']=self.server.engine.upload_reference(reference)
            else:raise ValueError('Use JSON or the supported video multipart schema')
            if kind=='video':
                if 'seconds' in body:body['duration']=int(body.pop('seconds'))
                if 'size' in body:
                    dimensions=body.pop('size')
                    sizes={'1280x720':('720p','16:9'),'720x1280':('720p','9:16'),'720x720':('720p','1:1'),'848x480':('480p','16:9'),'854x480':('480p','16:9'),'480x480':('480p','1:1')}
                    if dimensions not in sizes:raise ValueError('Unsupported video dimensions')
                    body['resolution'],body['aspect_ratio']=sizes[dimensions]
                if not body.get('image'):raise ValueError('This recipe enables image-to-video only')
            allowed={'model','prompt','size','quality','n','response_format','output_format','run_id'} if kind=='image' else {'model','prompt','duration','resolution','aspect_ratio','image','run_id','generate_audio'}
            if set(body)-allowed:raise ValueError('Unmapped request parameters: '+','.join(sorted(set(body)-allowed)))
            if body.get('response_format') not in (None,'b64_json') or body.get('output_format') not in (None,'png'):raise ValueError('PNG/base64 response required')
            job={k:v for k,v in body.items() if k not in ('response_format','output_format')};job['kind']=kind;job.setdefault('run_id',self.headers.get('Idempotency-Key','default'))
            self.server.engine.prepare(job)
            if kind=='image':
                r=self.server.engine.run(job);raw=Path(r['output']).read_bytes()
                return self.send_json(200,{'model':job['model'],'data':[{'b64_json':base64.b64encode(raw).decode()}],'billing':r.get('cost')})
            ident=self.server.engine.identity(job)
            with self.server.active_lock:
                if ident not in self.server.active:
                    self.server.active.add(ident)
                    def run():
                        try:self.server.engine.run(job)
                        except Exception:
                            file=self.server.engine.state/(ident+'.json')
                            if not file.exists():file.write_text(json.dumps({'id':ident,'job':job,'kind':'video','status':'failed'}),encoding='utf-8')
                        finally:
                            with self.server.active_lock:self.server.active.discard(ident)
                    threading.Thread(target=run,daemon=True).start()
            return self.send_json(200,{'id':ident,'object':'video','model':job['model'],'status':'queued'})
        except ValueError as e:return self.send_json(400,{'error':{'message':str(e)}})
        except Exception:return self.send_json(502,{'error':{'message':'Media request unavailable. Inspect the private saved task; do not automatically resubmit.'}})

if __name__=='__main__':
    engine=MediaEngine()
    Bridge(('127.0.0.1',int(os.environ.get('BRIDGE_PORT','8769'))),engine,os.environ.get('BRIDGE_TOKEN')).serve_forever()
