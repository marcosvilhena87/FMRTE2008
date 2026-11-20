"""F24.1 independent JSON Schema verification of the exact adversarial cases."""
import hashlib
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator
folder=Path(__file__).resolve().parent
evidence=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
raw=(folder/"F24B03Sufficiency.json").read_bytes()
schema_bytes=(folder/"F24B03Sufficiency.schema.json").read_bytes()
schema=json.loads(schema_bytes)
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema)
if list(validator.iter_errors(json.loads(raw))):
    raise SystemExit("F24.1 canonical rejected")
report=json.loads((evidence/"F24B03SufficiencyValidation.json").read_text(encoding="utf-8"))
cases=report["negativeCases"]
ids=[x["caseId"] for x in cases]
directory=evidence/"f24-sufficiency-cases"
if len(ids)!=len(set(ids)) or len(ids)!=25 or report["negativeCasesRejected"]!=25:
    raise SystemExit("F24.1 case inventory wrong")
if {p.stem for p in directory.glob("*.json")}!=set(ids):
    raise SystemExit("F24.1 mutation documents missing/extra")
if report["manifestSha256"]!=hashlib.sha256(raw).hexdigest() or report["schemaSha256"]!=hashlib.sha256(schema_bytes).hexdigest():
    raise SystemExit("F24.1 digest mismatch")
results=[]
for c in cases:
    if c["result"]!="rejected" or c["actualOutcome"]!="SufficiencyViolation" or c["expectedOutcome"]!="SufficiencyViolation":
        raise SystemExit("F24.1 fail-open primary validator "+c["caseId"])
    candidate=json.loads((directory/(c["caseId"]+".json")).read_text(encoding="utf-8"))
    errors=list(validator.iter_errors(candidate))
    if not errors:
        raise SystemExit("F24.1 independent schema accepted "+c["caseId"])
    results.append({"caseId":c["caseId"],"result":"rejected","schemaErrorCount":len(errors)})
(evidence/"F24B03SufficiencyIndependentValidation.json").write_text(json.dumps({
    "schemaVersion":1,"kind":"f24-b03-independent-schema-validation",
    "canonicalAccepted":True,"manifestSha256":hashlib.sha256(raw).hexdigest(),
    "schemaSha256":hashlib.sha256(schema_bytes).hexdigest(),
    "negativeCasesRejected":len(results),"negativeCases":results,
    "approved":False,"operational":False,"historicalProvenanceAttested":False
},indent=2),encoding="utf-8")
print("OK F24.1 independent JSON Schema: 25/25 mutations rejected, canonical valid, no approval")
