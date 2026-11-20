"""F24.4 independent Draft202012 schema verification, exact case IDs and SHA-256."""
import json,hashlib,os
from pathlib import Path
from jsonschema import Draft202012Validator
f=Path(__file__).resolve().parent
out=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
raw=(f/"F24ConsolidatedEvidence.json").read_bytes()
sr=(f/"F24ConsolidatedEvidence.schema.json").read_bytes()
schema=json.loads(sr)
Draft202012Validator.check_schema(schema)
v=Draft202012Validator(schema)
if list(v.iter_errors(json.loads(raw))):raise SystemExit("F24.4 schema rejected canonical")
report=json.loads((out/"F24ConsolidatedValidation.json").read_text(encoding="utf-8"))
cases=report["negativeCases"]
manifest=[x for x in cases if x["group"]=="manifest"]
source=[x for x in cases if x["group"]=="source"]
ids=[x["caseId"] for x in manifest]
candidate_dir=out/"f24-consolidated-cases"
if len(ids)!=len(set(ids)) or len(ids)!=32 or len(source)!=12:
    raise SystemExit("F24.4 wrong negative case inventory")
if set(ids)!={x.stem for x in candidate_dir.glob("*.json")}:
    raise SystemExit("F24.4 negative candidate mismatch")
if report["manifestSha256"]!=hashlib.sha256(raw).hexdigest() or report["schemaSha256"]!=hashlib.sha256(sr).hexdigest():
    raise SystemExit("F24.4 schema/manifest digest mismatch")
structured=[]
for case in manifest:
    if case["result"]!="rejected" or case["actualOutcome"]!="EvidenceViolation" or case["expectedOutcome"]!="EvidenceViolation":
        raise SystemExit("F24.4 primary failed negative "+case["caseId"])
    errors=list(v.iter_errors(json.loads((candidate_dir/(case["caseId"]+".json")).read_text(encoding="utf-8"))))
    if not errors:raise SystemExit("F24.4 independent accepted "+case["caseId"])
    structured.append({"caseId":case["caseId"],"result":"rejected","schemaErrorCount":len(errors)})
if any(c["result"]!="rejected" for c in source):
    raise SystemExit("F24.4 source mutation not rejected")
(out/"F24ConsolidatedIndependentValidation.json").write_text(json.dumps({
  "schemaVersion":1,"kind":"f24-consolidated-independent-schema",
  "manifestSha256":hashlib.sha256(raw).hexdigest(),
  "schemaSha256":hashlib.sha256(sr).hexdigest(),
  "canonicalAccepted":True,"negativeCasesRejected":32,
  "negativeCases":structured,"sourceCasesRejectedBySemanticValidator":12,
  "approved":False,"operational":False,"humanApproval":False
},indent=2),encoding="utf-8")
print("OK F24.4 independent JSON Schema: 32/32 manifest negatives rejected; 12 source negatives semantically rejected; no approval")
