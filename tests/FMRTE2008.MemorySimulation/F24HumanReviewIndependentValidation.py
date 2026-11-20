"""F24.3 independent Draft 2020-12 schema validation, fixed 32 negative cases."""
import hashlib,json,os
from pathlib import Path
from jsonschema import Draft202012Validator
f=Path(__file__).resolve().parent
e=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
raw=(f/"F24HumanReviewNotMade.json").read_bytes()
sr=(f/"F24HumanReviewNotMade.schema.json").read_bytes()
s=json.loads(sr);Draft202012Validator.check_schema(s)
v=Draft202012Validator(s)
if list(v.iter_errors(json.loads(raw))):raise SystemExit("F24.3 canonical rejected")
r=json.loads((e/"F24HumanReviewValidation.json").read_text(encoding="utf-8"))
cases=r["negativeCases"];ids=[c["caseId"] for c in cases]
folder=e/"f24-human-cases"
if len(ids)!=len(set(ids)) or len(ids)!=32 or r["negativeCasesRejected"]!=32:
    raise SystemExit("F24.3 negative IDs")
if {x.stem for x in folder.glob("*.json")}!=set(ids):
    raise SystemExit("F24.3 mutation files")
if r["manifestSha256"]!=hashlib.sha256(raw).hexdigest() or r["schemaSha256"]!=hashlib.sha256(sr).hexdigest():
    raise SystemExit("F24.3 hash drift")
out=[]
for x in cases:
    if x["result"]!="rejected" or x["expectedOutcome"]!="UndecidedViolation" or x["actualOutcome"]!="UndecidedViolation":
        raise SystemExit("F24.3 primary false result")
    errors=list(v.iter_errors(json.loads((folder/(x["caseId"]+".json")).read_text(encoding="utf-8"))))
    if not errors:raise SystemExit("F24.3 schema accepted "+x["caseId"])
    out.append({"caseId":x["caseId"],"result":"rejected","schemaErrorCount":len(errors)})
(e/"F24HumanReviewIndependentValidation.json").write_text(json.dumps({
    "schemaVersion":1,"kind":"f24-human-review-independent-schema",
    "canonicalAccepted":True,"manifestSha256":hashlib.sha256(raw).hexdigest(),
    "schemaSha256":hashlib.sha256(sr).hexdigest(),
    "negativeCasesRejected":32,"negativeCases":out,"decision":"NOT_MADE",
    "approved":False,"operational":False,"humanApproval":False
},indent=2),encoding="utf-8")
print("OK F24.3 independent JSON Schema: 32/32 negatives rejected, human decision NOT_MADE")
