from pathlib import Path
import json,argparse,shutil
from media_engine import MediaEngine
p=argparse.ArgumentParser();p.add_argument("--job",required=True);p.add_argument("--live",action="store_true");a=p.parse_args()
job=json.loads(Path(a.job).read_text(encoding="utf-8"));engine=MediaEngine()
if not a.live:
 q=engine.prepare(job);print(json.dumps({"model":job["model"],"rate":q["quote"]["maximum_unit_price"],"unit":q["quote"]["unit"],"estimated_usd":q["estimated_usd"],"estimate_only":True}))
else:
 if job["kind"]=="video" and "first_frame_file" in job:job["image"]=engine.upload_reference(Path(job.pop("first_frame_file")).read_bytes())
 r=engine.run(job);dest=Path("examples")/(job["model"]+(".png" if job["kind"]=="image" else ".mp4"));dest.parent.mkdir(exist_ok=True);shutil.copyfile(r["output"],dest)
 public=engine.public(r);public["file"]=dest.as_posix();Path("evidence").mkdir(exist_ok=True);Path("evidence",job["model"]+".json").write_text(json.dumps(public,indent=2),encoding="utf-8");print(json.dumps(public))
