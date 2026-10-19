"""ToAPIs media adapter. Only fixed, inspected presets; no automatic POST retries."""
from pathlib import Path
from decimal import Decimal
from urllib.parse import quote
import base64,hashlib,json,os,time,threading,uuid
from toapis_tools.toapis_async import ToAPIsClient,build_request
from toapis_tools.toapis_models import MODEL_ROUTES
from toapis_tools.toapis_billing import current_price,observe,refresh_settlement,cost_summary

IMAGE_MODELS=('gpt-image-2-vip','gpt-image-2','gpt-image-2.5-flare')
VIDEO_MODELS=('seedance-2-mini','seedance-2','seedance-2-5')

def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,path)

class MediaEngine:
    def __init__(self,key=None,base=None,state=None):
        envfile=Path('.env')
        if envfile.exists():
            for line in envfile.read_text(encoding='utf-8-sig').splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    name,value=line.split('=',1);name=name.strip()
                    if name in ('TOAPIS_API_KEY','TOAPIS_BASE_URL','TOAPIS_STATE_DIR','TOAPIS_MAX_IMAGE_USD','TOAPIS_MAX_VIDEO_USD','BRIDGE_TOKEN','BRIDGE_PORT'):os.environ.setdefault(name,value.strip().strip('\"\x27'))
        self.state=Path(state or os.environ.get('TOAPIS_STATE_DIR','.toapis-state'))
        self.state.mkdir(parents=True,exist_ok=True)
        self.client=ToAPIsClient(key or os.environ.get('TOAPIS_API_KEY'),base or os.environ.get('TOAPIS_BASE_URL','https://toapis.com'),state_dir=self.state/'transport')
        self.lock=threading.Lock()

    def prepare(self,job):
        model=job['model'];kind=job['kind']
        if not isinstance(job.get('prompt'),str) or not job['prompt'].strip():raise ValueError('Non-empty prompt required')
        if kind=='image':
            if model not in IMAGE_MODELS:raise ValueError('Image model not enabled')
            args={'model':model,'prompt':job['prompt'],'size':job.get('size','1024x1024'),'n':1}
            if job.get('n',1)!=1:raise ValueError('Only one image per request is enabled')
            route=MODEL_ROUTES[model]
            if job.get('quality') not in (None,route['quality']):raise ValueError('Quality differs from the inspected preset')
            body,_=build_request(args)
            conditions={'resolution':'1K','n':1,'input_image_count':0}
            if route['quality'] is not None:conditions['quality']=route['quality']
            pricing=current_price(self.client._json,model,'image',conditions)
            if pricing['unit']!='request' or pricing['price_basis']!='request':raise ValueError('Fixed image price required')
            estimate=Decimal(pricing['maximum_unit_price']);cap=Decimal(os.environ.get('TOAPIS_MAX_IMAGE_USD','0.10'))
        elif kind=='video':
            if model not in VIDEO_MODELS:raise ValueError('Video model not enabled')
            resolution=job.get('resolution','480p')
            if int(job.get('duration',4))!=4 or resolution not in ('480p','720p'):raise ValueError('Only 4-second 480p/720p video presets are enabled')
            if job.get('generate_audio',False):raise ValueError('Audio is not enabled')
            ratio=job.get('aspect_ratio','16:9')
            if ratio not in ('16:9','1:1','9:16'):raise ValueError('Aspect ratio not enabled')
            # Seedance 2.5's token-rate rows use duration=-1 for dynamic length.
            # Keep the actual generation request at 4 seconds; only the rate-row selector differs.
            conditions={'resolution':resolution,'duration':'-1' if model=='seedance-2-5' else 4,'has_video_input':False,'has_audio_input':False,'has_image_input':True,'output_format':'mp4','input_image_count':1,'generate_audio':False}
            pricing=current_price(self.client._json,model,'video',conditions)
            if pricing['unit']!='1m_tokens' or pricing['price_basis']!='total_tokens':raise ValueError('Unexpected video pricing basis')
            estimate=Decimal('38400' if resolution=='480p' else '86400')*Decimal(pricing['maximum_unit_price'])/Decimal(1000000)
            cap=Decimal(os.environ.get('TOAPIS_MAX_VIDEO_USD','1.50'))
            body={'model':model,'prompt':job['prompt'],'duration':4,'resolution':resolution,'aspect_ratio':ratio,'generate_audio':False}
        else:raise ValueError('Unknown media kind')
        if estimate>cap:raise ValueError('Current Key-scoped quote exceeds per-request cap')
        return {'request':body,'quote':pricing,'estimated_usd':str(estimate),'estimate_only':True}

    def identity(self,job):
        canonical=json.dumps(job,sort_keys=True,ensure_ascii=False)
        return hashlib.sha256((self.client.origin+hashlib.sha256(self.client.key.encode()).hexdigest()+canonical).encode()).hexdigest()

    def upload_reference(self,raw):
        if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw)>10*1024*1024:raise ValueError('Reference must be a PNG of at most 10 MiB')
        fingerprint=hashlib.sha256(raw).hexdigest();cache=self.state/('reference-'+fingerprint+'.json')
        if cache.exists():return json.loads(cache.read_text(encoding='utf-8'))['url']
        boundary='ToAPIs'+uuid.uuid4().hex
        data=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="reference.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
        response=self.client._json('uploads/images',data,'multipart/form-data; boundary='+boundary)
        url=response['data']['url']
        if not url.startswith('https://'):raise ValueError('Upload did not return HTTPS URL')
        save(cache,{'url':url});return url

    def run(self,job):
        ident=self.identity(job);path=self.state/(ident+'.json')
        with self.lock:
            old=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
            if old and old.get('status')=='completed':return old
            if old and old.get('status') in ('submitting','submission_uncertain','failed','cancelled','expired'):raise RuntimeError('Existing task must be reconciled; no new submission')
            prepared=self.prepare(job)
            if job['kind']=='image':return self._image(job,prepared,ident,path)
            return self._video(job,prepared,ident,path,old)

    def _image(self,job,prepared,ident,path):
        # Canonical transport persists before POST and resumes only the saved task.
        self.client.run_id=job.get('run_id',ident)
        result=self.client.generate(model=job['model'],prompt=job['prompt'],size=job.get('size','1024x1024'),n=1)
        receipt=self.client.last_receipt
        raw=base64.b64decode(result.data[0].b64_json)
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Enabled image presets require actual PNG bytes')
        dest=self.state/'assets'/(ident+'.png');dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
        record={'job':job,'id':ident,'status':'completed','kind':'image','output':str(dest.resolve()),'source_url':receipt['result_url'],'receipt':receipt,'cost':cost_summary(receipt),'quote':prepared['quote'],'asset_sha256':hashlib.sha256(raw).hexdigest()}
        save(path,record);return record

    def _video(self,job,prepared,ident,path,old):
        record=old
        if not record:
            body=prepared['request'];image=job.get('image')
            if isinstance(image,dict):image=image.get('url')
            if not isinstance(image,str) or not image.startswith('https://'):raise ValueError('A public HTTPS first-frame URL is required')
            body['image_with_roles']=[{'url':image,'role':'first_frame'}]
            body['client_business_id']='community-'+ident[:32]
            receipt={'task_id':None,'model':job['model'],'request':body,'observations':[],'quote':prepared['quote']}
            record={'id':ident,'job':job,'kind':'video','status':'submitting','receipt':receipt,'quote':prepared['quote']}
            with path.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
            try:task=self.client._json('videos/generations',body)
            except Exception:
                record['status']='submission_uncertain';save(path,record);raise RuntimeError('Submission uncertain; do not repeat POST') from None
            receipt['task_id']=task.get('id');observe(receipt,task);record['status']='submitted';save(path,record)
            if not receipt['task_id']:raise RuntimeError('Missing task identity; do not repeat POST')
        receipt=record['receipt'];deadline=time.monotonic()+900
        while time.monotonic()<deadline:
            try:task=self.client._json('videos/generations/'+quote(receipt['task_id'],safe=''))
            except Exception:time.sleep(8);continue
            observe(receipt,task);record['status']=task.get('status');save(path,record)
            if record['status'] in ('completed','failed','cancelled','expired'):
                try:refresh_settlement(self.client._json,receipt,'video',lambda:save(path,record),timeout=30)
                except Exception:record['settlement_refresh']='unavailable'
                record['cost']=cost_summary(receipt);save(path,record)
            if record['status']=='completed':
                url=task['result']['data'][0]['url'];raw=self.client._asset(url)
                if b'ftyp' not in raw[:40]:raise ValueError('Video result is not an MP4')
                dest=self.state/'assets'/(ident+'.mp4');dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
                record.update(output=str(dest.resolve()),source_url=url,asset_sha256=hashlib.sha256(raw).hexdigest());save(path,record);return record
            if record['status'] in ('failed','cancelled','expired'):raise RuntimeError('Video task ended without a successful result; no resubmission')
            time.sleep(8)
        raise RuntimeError('Polling timed out; resume saved task only')

    def public(self,record):
        return {'model':record['job']['model'],'kind':record['kind'],'status':record['status'],'parameters':{k:record['job'][k] for k in ('size','duration','resolution','aspect_ratio') if k in record['job']},'cost':record.get('cost'),'catalog_rate':record['quote']['maximum_unit_price'],'catalog_unit':record['quote']['unit']}
