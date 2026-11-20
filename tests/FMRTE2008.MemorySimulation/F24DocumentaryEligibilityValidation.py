"""F24.2: closed, source-bound, fail-closed documentary eligibility. Never approve a map."""
import copy
import hashlib
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator

FOLDER=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
RAW=(FOLDER/"F24DocumentaryEligibility.json").read_bytes()
SCHEMA_RAW=(FOLDER/"F24DocumentaryEligibility.schema.json").read_bytes()
DOC=json.loads(RAW)
SCHEMA=json.loads(SCHEMA_RAW)
Draft202012Validator.check_schema(SCHEMA)
SV=Draft202012Validator(SCHEMA)
PROV=["P01","P02","P03","P04","P05"]
class IneligibleEvidence(ValueError):
    pass
def check(ok,why):
    if not ok: raise IneligibleEvidence(why)
def sha(data): return hashlib.sha256(data).hexdigest()
def sources(m):
    out={}
    for tag,key,hashkey in (("F22","gatePath","gateSha256"),("F23.2","riskPath","riskSha256"),
                             ("F24.1","sufficiencyPath","sufficiencySha256"),
                             ("F23.3","humanDecisionPath","humanDecisionSha256")):
        p=ROOT/m["source"][key]
        check(p.is_file(),"missing source "+tag)
        raw=p.read_bytes()
        check(sha(raw)==m["source"][hashkey],"source digest drift "+tag)
        out[tag]=json.loads(raw)
    return out
def validate(m,src):
    check(not list(SV.iter_errors(m)),"closed schema rejected eligibility")
    f22=src["F22"];risk=src["F23.2"];suff=src["F24.1"];human=src["F23.3"]
    check(len(m["gates"])==len(f22["gates"])==5,"gate count")
    check(len(m["risks"])==len(risk["risks"])==8,"risk count")
    check(len(suff["observations"])==7,"observations")
    missing={"R%02d"%i for i in range(1,8)}
    for item in suff["observations"]:
        check(item["observationId"] in missing,"duplicate or invalid observation")
        missing.remove(item["observationId"])
        check(item["provenanceStatus"]=="PENDING-DECLARED" and
              item["sufficiency"]=="INSUFFICIENT_PRESERVED","promoted provenance")
        check([x["criterionId"] for x in item["criteria"]]==PROV,"criterion coverage")
        check(all(x["status"]=="MISSING" and x["primaryEvidenceReference"] is None and
                  x["humanVerified"] is False for x in item["criteria"]),"fabricated sufficiency")
    check(not missing,"incomplete R01-R07")
    expected_criteria={"A%02d"%i for i in range(1,13)}
    observed_criteria=set()
    for a,b in zip(m["gates"],f22["gates"]):
        check(a["gateId"]==b["gateId"],"gate ID")
        check(a["criteria"]==b["criteria"],"gate criteria")
        observed_criteria.update(b["criteria"])
        check(a["riskIds"]==b["risks"],"gate risk IDs")
        check(a["observationIds"]==[e["observationId"] for e in b["evidenceReferences"]],"gate observations")
        check(a["requiredProvenanceCriteria"]==PROV,"gate P01-P05")
        check(a["documentaryEligibility"]=="NOT_ELIGIBLE" and a["humanApproval"] is False,"gate promotion")
        for rid in a["observationIds"]:
            check(rid in {"R%02d"%i for i in range(1,8)},"unknown observation")
    check(observed_criteria==expected_criteria,"A01-A12 not covered")
    checked_risks=set()
    for a,b in zip(m["risks"],risk["risks"]):
        check(a["riskId"]==b["riskId"] and a["riskId"] not in checked_risks,"risk ID or duplicate")
        checked_risks.add(a["riskId"])
        check(a["gateId"]==b["gateId"] and a["criteria"]==b["criteria"] and
              a["observationIds"]==b["observationIds"],"risk traceability")
        check(a["requiredProvenanceCriteria"]==PROV,"risk P01-P05")
        check(a["status"]=="PENDING" and a["accepted"] is False and
              a["acceptanceReference"] is None and b["riskAccepted"] is False and
              b["riskAcceptanceReference"] is None,"risk accepted")
        gs=[g for g in f22["gates"] if b["riskId"] in g["risks"]]
        check(len(gs)==1 and gs[0]["gateId"]==b["gateId"],"risk mapped to wrong gate")
    check(checked_risks=={"RA-%02d"%i for i in range(1,9)},"missing RA")
    g5=f22["gates"][4]
    check(g5["gateId"]=="G5" and g5["criteria"]==["A12"] and g5["risks"]==[],"G5 is transversal")
    check(human["gate"]["gateId"]=="G5" and human["gate"]["criterion"]=="A12" and
          human["gate"]["status"]=="GATE-BLOQUEADO" and human["gate"]["humanSignoff"] is False,"human A12")
    check(human["humanReview"]["decision"]=="NOT_MADE" and
          all(human["humanReview"][k] is None for k in ("reviewer","reviewedAt","authorityReference","decisionReference")),"fabricated human reviewer")
    check(all(x["accepted"] is False and x["acceptanceReference"] is None for x in human["riskDecisions"]),"human risk accepted")
    check(human["outcome"]=={"approved":False,"operational":False,"approvedPlayerMaps":0},"human outcome")
    check(risk["decision"]["approved"] is False and risk["decision"]["operational"] is False and
          risk["decision"]["gateA12"]=="GATE-BLOQUEADO" and
          risk["decision"]["b03"]=="PENDING-DECLARED" and
          risk["decision"]["decisionStatus"]=="NOT_MADE","F23.2 decision")
    check(f22["decision"]["approved"] is False and f22["decision"]["operational"] is False and
          f22["decision"]["gateA12"]=="GATE-BLOQUEADO","F22 decision")
    check(suff["decision"]["approved"] is False and suff["decision"]["operational"] is False and
          suff["decision"]["sufficiency"]=="INSUFFICIENT_PRESERVED","F24.1 decision")
    check(m["decision"]=={"approved":False,"operational":False,"gateA12":"GATE-BLOQUEADO",
          "b03":"PENDING-DECLARED","humanDecision":"NOT_MADE","humanReviewOccurred":False,
          "documentaryEligibility":"NOT_ELIGIBLE","risksAccepted":0,"approvedPlayerMaps":0},
          "F24.2 eligibility promotion")
def mutated(obj,path,value):
    out=copy.deepcopy(obj);cur=out
    for step in path[:-1]:cur=cur[step]
    cur[path[-1]]=value
    return out
def main():
    src=sources(DOC);validate(DOC,src)
    cases=[
        ("approve",("decision","approved"),True),
        ("operational",("decision","operational"),True),
        ("unblock-A12",("decision","gateA12"),"APPROVED"),
        ("verify-B03",("decision","b03"),"VERIFIED"),
        ("decision-made",("decision","humanDecision"),"APPROVED"),
        ("fake-review",("decision","humanReviewOccurred"),True),
        ("eligibility-promoted",("decision","documentaryEligibility"),"ELIGIBLE"),
        ("risk-count-promoted",("decision","risksAccepted"),1),
        ("approved-map",("decision","approvedPlayerMaps"),1),
        ("wrong-f22-hash",("source","gateSha256"),"0"*64),
        ("wrong-f23-risk-hash",("source","riskSha256"),"0"*64),
        ("wrong-f24-suff-hash",("source","sufficiencySha256"),"0"*64),
        ("wrong-human-hash",("source","humanDecisionSha256"),"0"*64),
        ("wrong-gate",("gates",0,"gateId"),"G3"),
        ("wrong-A01",("gates",0,"criteria",0),"A12"),
        ("wrong-gate-risk",("gates",1,"riskIds",0),"RA-01"),
        ("wrong-gate-observation",("gates",2,"observationIds",0),"R01"),
        ("wrong-required-P",("gates",3,"requiredProvenanceCriteria",0),"P05"),
        ("gate-eligible",("gates",4,"documentaryEligibility"),"ELIGIBLE"),
        ("gate-human",("gates",4,"humanApproval"),True),
        ("missing-RA",("risks",0,"riskId"),"RA-08"),
        ("risk-gate",("risks",1,"gateId"),"G1"),
        ("risk-A",("risks",2,"criteria",0),"A01"),
        ("risk-observation",("risks",3,"observationIds",0),"R01"),
        ("risk-required-P",("risks",4,"requiredProvenanceCriteria",0),"P03"),
        ("risk-accepted",("risks",5,"accepted"),True),
        ("risk-acceptance-reference",("risks",6,"acceptanceReference"),"CI"),
        ("risk-status-promoted",("risks",7,"status"),"CLOSED")
    ]
    BASE.mkdir(parents=True,exist_ok=True)
    folder=BASE/"f24-eligibility-cases";folder.mkdir(exist_ok=True)
    negatives=[]
    for name,path,value in cases:
        candidate=mutated(DOC,path,value)
        (folder/(name+".json")).write_text(json.dumps(candidate,indent=2),encoding="utf-8")
        try:validate(candidate,src)
        except IneligibleEvidence as e:
            negatives.append({"caseId":name,"result":"rejected",
               "expectedOutcome":"IneligibleEvidence","actualOutcome":"IneligibleEvidence","reason":str(e)})
        else:raise RuntimeError("F24.2 accepted manifest mutation "+name)
    linked=[]
    mutations=[
      ("f22-gate-risk","F22",("gates",0,"risks",0),"RA-08"),
      ("f22-gate-criterion","F22",("gates",1,"criteria",0),"A01"),
      ("f22-false-human","F22",("decision","gateA12"),"APPROVED"),
      ("f23-risk-accept","F23.2",("risks",0,"riskAccepted"),True),
      ("f23-risk-observation","F23.2",("risks",1,"observationIds",0),"R01"),
      ("f24-provenance","F24.1",("observations",0,"provenanceStatus"),"VERIFIED"),
      ("f24-fake-evidence","F24.1",("observations",1,"criteria",0,"primaryEvidenceReference"),"CI"),
      ("f24-fake-human-check","F24.1",("observations",2,"criteria",1,"humanVerified"),True),
      ("human-reviewer","F23.3",("humanReview","reviewer"),"CI"),
      ("human-decision","F23.3",("humanReview","decision"),"APPROVED"),
      ("human-risk-accept","F23.3",("riskDecisions",0,"accepted"),True)
    ]
    for name,stage,path,value in mutations:
        alt=copy.deepcopy(src);alt[stage]=mutated(src[stage],path,value)
        try:validate(DOC,alt)
        except IneligibleEvidence as e:
            linked.append({"caseId":name,"stage":stage,"result":"rejected",
               "expectedOutcome":"IneligibleEvidence","actualOutcome":"IneligibleEvidence","reason":str(e)})
        else:raise RuntimeError("F24.2 accepted source mutation "+name)
    check(len(negatives)==28 and len({x["caseId"] for x in negatives})==28,"negative inventory")
    check(len(linked)==11 and len({x["caseId"] for x in linked})==11,"source negative inventory")
    (BASE/"F24DocumentaryEligibility.json").write_bytes(RAW)
    (BASE/"F24DocumentaryEligibility.schema.json").write_bytes(SCHEMA_RAW)
    (BASE/"F24DocumentaryEligibilityValidation.json").write_text(json.dumps({
        "schemaVersion":1,"kind":"f24-documentary-eligibility-validation-offline",
        "manifestSha256":sha(RAW),"schemaSha256":sha(SCHEMA_RAW),
        "sourceDigests":{tag:sha((ROOT/DOC["source"][key]).read_bytes()) for tag,key in
             (("F22","gatePath"),("F23.2","riskPath"),("F24.1","sufficiencyPath"),("F23.3","humanDecisionPath"))},
        "gatesChecked":5,"risksChecked":8,"criteriaChecked":12,"observationsChecked":7,
        "negativeCasesRejected":28,"negativeCases":negatives,
        "sourceCasesRejected":11,"sourceCases":linked,
        "canonicalAccepted":True,"approved":False,"operational":False,
        "humanApproval":False,"documentaryEligibility":"NOT_ELIGIBLE",
        "gateA12":"GATE-BLOQUEADO","b03":"PENDING-DECLARED"
    },indent=2),encoding="utf-8")
    print("OK F24.2: G1-G5=5, A01-A12=12, RA-01..08=8, P01-P05 linked; 28/28 negatives, 11/11 source mutations rejected; no approval")
if __name__=="__main__":main()
