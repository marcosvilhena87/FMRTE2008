"""F24.2 independent validation of canonical 2020-12 schema and exact 28 mutations."""
import hashlib,json,os
from pathlib import Path
from jsonschema import Draft202012Validator
f=Path(__file__).resolve().parent
e=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
raw=(f/"F24DocumentaryEligibility.json").read_bytes()
schema_raw=(f/"F24DocumentaryEligibility.schema.json").read_bytes()
schema=json.loads(schema_raw)
Draft202012Validator.check_schema(schema)
v=Draft202012Validator(schema)
if list(v.iter_errors(json.loads(raw))):
    raise SystemExit("F24.2 canonical schema rejected")
report=json.loads((e/"F24DocumentaryEligibilityValidation.json").read_text(encoding="utf-8"))
cases=report["negativeCases"]
ids=[x["caseId"] for x in cases]
folder=e/"f24-eligibility-cases"
if len(ids)!=len(set(ids)) or len(ids)!=28 or report["negativeCasesRejected"]!=28:
    raise SystemExit("F24.2 negative inventory")
if {p.stem for p in folder.glob("*.json")}!=set(ids):
    raise SystemExit("F24.2 candidate files mismatch")
if report["manifestSha256"]!=hashlib.sha256(raw).hexdigest() or report["schemaSha256"]!=hashlib.sha256(schema_raw).hexdigest():
    raise SystemExit("F24.2 checksum mismatch")
out=[]
for x in cases:
    if x["result"]!="rejected" or x["expectedOutcome"]!="IneligibleEvidence" or x["actualOutcome"]!="IneligibleEvidence":
        raise SystemExit("F24.2 primary report false")
    errors=list(v.iter_errors(json.loads((folder/(x["caseId"]+".json")).read_text(encoding="utf-8"))))
    if not errors:raise SystemExit("F24.2 schema accepted "+x["caseId"])
    out.append({"caseId":x["caseId"],"result":"rejected","schemaErrorCount":len(errors)})
(e/"F24DocumentaryEligibilityIndependentValidation.json").write_text(json.dumps({
  "schemaVersion":1,"kind":"f24-documentary-eligibility-independent-schema",
  "canonicalAccepted":True,"manifestSha256":hashlib.sha256(raw).hexdigest(),
  "schemaSha256":hashlib.sha256(schema_raw).hexdigest(),
  "negativeCasesRejected":28,"negativeCases":out,
  "approved":False,"operational":False,"humanApproval":False
},indent=2),encoding="utf-8")
print("OK F24.2 independent JSON Schema: canonical accepted, 28/28 negatives rejected, no approval")
