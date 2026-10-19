from pathlib import Path
import sys,threading,json,urllib.request,urllib.error,tempfile,unittest
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from bridge import Bridge
class Fake:
 def __init__(self):self.state=Path(tempfile.mkdtemp());self.calls=0;self.jobs=[]
 def prepare(self,job):
  if job['model'] not in ('gpt-image-2-vip','seedance-2-mini'):raise ValueError('Unsupported model')
  self.jobs.append(job)
 def run(self,job):self.calls+=1;raise RuntimeError('No live network in contract test')
 def identity(self,job):return 'b'*64
 def upload_reference(self,raw):return 'https://example.com/original-reference.png'
class Tests(unittest.TestCase):
 def setUp(self):
  self.engine=Fake();self.srv=Bridge(('127.0.0.1',0),self.engine,'a'*32);self.thread=threading.Thread(target=self.srv.serve_forever,daemon=True);self.thread.start();self.url='http://127.0.0.1:'+str(self.srv.server_port)
 def tearDown(self):self.srv.shutdown();self.srv.server_close()
 def req(self,path,body=None,token='a'*32):
  request=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_auth_and_model_discovery(self):
  self.assertEqual(self.req('/v1/models',token='bad')[0],401);code,data=self.req('/v1/models');self.assertEqual(code,200);self.assertEqual(len(data['data']),6);self.assertEqual(self.engine.calls,0)
 def test_unknown_parameters_rejected_before_generation(self):
  code,_=self.req('/v1/images/generations',{'model':'gpt-image-2-vip','prompt':'x','mask':'not-supported'});self.assertEqual(code,400);self.assertEqual(self.engine.calls,0)
 def test_edits_not_silently_accepted(self):
  self.assertEqual(self.req('/v1/images/edits',{'prompt':'x'})[0],400);self.assertEqual(self.engine.calls,0)
 def test_generation_failure_is_not_retried(self):
  code,_=self.req('/v1/images/generations',{'model':'gpt-image-2-vip','prompt':'x'});self.assertEqual(code,502);self.assertEqual(self.engine.calls,1)
 def test_multipart_video_size_seconds_and_first_frame(self):
  boundary='ContractBoundary';raw=b''
  for name,value in {'model':'seedance-2-mini','prompt':'x','seconds':'4','size':'1280x720'}.items():raw+=f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
  raw+=f'--{boundary}\r\nContent-Disposition: form-data; name="input_reference"; filename="input.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+b'PNG fixture'+f'\r\n--{boundary}--\r\n'.encode()
  req=urllib.request.Request(self.url+'/v1/videos',data=raw,headers={'Authorization':'Bearer '+'a'*32,'Content-Type':'multipart/form-data; boundary='+boundary})
  with urllib.request.urlopen(req) as r:self.assertEqual(r.status,200)
  job=self.engine.jobs[-1];self.assertEqual(job['duration'],4);self.assertEqual(job['resolution'],'720p');self.assertEqual(job['aspect_ratio'],'16:9');self.assertEqual(job['image'],'https://example.com/original-reference.png')
 def test_existing_completed_job_is_not_submitted_again(self):
  from media_engine import MediaEngine,save
  from types import SimpleNamespace
  e=MediaEngine.__new__(MediaEngine);e.state=self.engine.state;e.lock=threading.Lock();e.client=SimpleNamespace(origin='https://toapis.com',key='synthetic-key')
  job={'kind':'image','model':'gpt-image-2-vip','prompt':'x'};ident=e.identity(job);save(e.state/(ident+'.json'),{'status':'completed','already_saved':True});self.assertTrue(e.run(job)['already_saved'])
if __name__=='__main__':unittest.main()
