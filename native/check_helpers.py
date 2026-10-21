"""Zero-paid checks for the new portable helper commands."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PUB=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PUB/'toapis-models'))
sys.path.insert(0,str(PUB/'native'))
import configure
import gallery_image

class Helpers(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state=Path(self.tmp.name)/'setup.json'
    def invoke(self,mod,args):
        with patch.object(sys,'argv',['helper']+args),contextlib.redirect_stdout(io.StringIO()):mod.main()
    def test_plan_is_zero_mutation(self):
        with patch.object(configure,'app_call',side_effect=AssertionError('unexpected local mutation')):
            self.invoke(configure,['--state',str(self.state)])
        self.assertFalse(self.state.exists())
    def test_setup_reuses_ids_and_correct_put(self):
        calls=[]
        def fake(app,path,body=None,method=None):
            calls.append((path,body,method))
            if path=='connections/':return {'id':body['model']}
            if path=='chats':return {'id':'fixture-chat'}
            return {}
        with patch.dict(os.environ,{'TOAPIS_API_KEY':'fixture-key'}),patch.object(configure,'app_call',side_effect=fake):
            self.invoke(configure,['--apply','--state',str(self.state)])
            self.invoke(configure,['--apply','--state',str(self.state)])
        self.assertEqual(sum(path=='connections/' for path,_,_ in calls),3)
        defaults=[(b,m) for path,b,m in calls if path.endswith('/default-parameters')]
        self.assertEqual(len(defaults),2)
        self.assertTrue(all(m=='PUT' and isinstance(b,dict) for b,m in defaults))
        self.assertEqual(defaults[0][0]['videoGeneration']['seedance']['durationSeconds'],4)
        self.assertNotIn('fixture-key',self.state.read_text())
        self.assertFalse(any('generat' in path for path,_,_ in calls))
    def test_lost_local_response_blocks_duplicate(self):
        with patch.dict(os.environ,{'TOAPIS_API_KEY':'fixture-key'}),patch.object(configure,'app_call',side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):self.invoke(configure,['--apply','--state',str(self.state)])
        with patch.dict(os.environ,{'TOAPIS_API_KEY':'fixture-key'}),patch.object(configure,'app_call') as api:
            with self.assertRaises(RuntimeError):self.invoke(configure,['--apply','--state',str(self.state)])
            api.assert_not_called()
    def prepare_image(self):
        configure.save(self.state,{'app':'http://127.0.0.1:17863','base_url':'https://toapis.cn/v1','chat_id':'fixture-chat','connections':{'image':'fixture-image'}})
    def test_image_quote_and_lost_submission_guard(self):
        self.prepare_image()
        posts=[]
        def fake(app,path,body=None,**kwargs):
            if body is None:return {'model':'gpt-image-2','baseUrl':'https://toapis.cn/v1'}
            posts.append(body);raise TimeoutError('fixture lost response')
        args=['--state',str(self.state),'--prompt','fixture scene']
        with patch.object(gallery_image,'Client',return_value=types.SimpleNamespace(json=lambda *a: {})),patch.object(gallery_image,'current_price',return_value={'unit':'request','maximum_unit_price':'0.015'}),patch.object(gallery_image,'app_call',side_effect=fake):
            self.invoke(gallery_image,args)
            self.assertEqual(posts,[])
            with self.assertRaises(TimeoutError):self.invoke(gallery_image,args+['--live'])
            with self.assertRaises(RuntimeError):self.invoke(gallery_image,args+['--live'])
        self.assertEqual(len(posts),1)
    def test_image_over_budget_blocks_submission(self):
        self.prepare_image()
        with patch.object(gallery_image,'Client',return_value=types.SimpleNamespace(json=lambda *a: {})),patch.object(gallery_image,'current_price',return_value={'unit':'request','maximum_unit_price':'0.03'}),patch.object(gallery_image,'app_call',return_value={'model':'gpt-image-2','baseUrl':'https://toapis.cn/v1'}) as api:
            with self.assertRaises(ValueError):self.invoke(gallery_image,['--state',str(self.state),'--prompt','fixture','--live'])
            self.assertEqual(api.call_count,1)
    def test_no_credentials_redirected_to_foreign_app(self):
        with self.assertRaises(ValueError):configure.app_call('https://foreign.example','connections/',{'apiKey':'fixture-key'})

if __name__=='__main__':unittest.main(verbosity=2)
