"""F24.3 human review remains NOT_MADE; no CI, PR, merge or identity inference."""
import json,hashlib,copy,os
from pathlib import Path
from jsonschema import Draft202012Validator
F=Path(__file__).resolve().parent
ROOT=F.parents[1]
OUT=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
RAW=(F/"F24HumanReviewNotMade.json").read_bytes()
SR=(F/"F24HumanReviewNotMade.schema.json").read_bytes()
D=json.loads(RAW)
S=json.loads(SR)
Draft202012Validator.check_schema(S)
V=Draft202012Validator(S)
class UndecidedViolation(ValueError): pass
def check(condition,why):
    if not condition:raise UndecidedViolation(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(d):
    out={}
    for label,p,h in [
        ("F23.3","f23HumanPath","f23HumanSha256"),
        ("F24.2","f24EligibilityPath","f24EligibilitySha256"),
        ("F24.1","f24SufficiencyPath","f24SufficiencySha256"),
        ("F23.2","f23RisksPath","f23RisksSha256")
    ]:
        content=(ROOT/d["source"][p]).read_bytes()
        check(sha(content)==d["source"][h],"source digest drift "+label)
        out[label]=json.loads(content)
    return out
def validate(d,src):
    check(not list(V.iter_errors(d)),"closed protocol schema")
    old=src["F23.3"];elig=src["F24.2"];suff=src["F24.1"];risks=src["F23.2"]
    check(d["review"]=={
      "reviewer":None,"reviewedAt":None,"authorityReference":None,
      "independenceDeclaration":None,"conflictOfInterestAssessment":None,
      "scopeReference":None,"evidenceVersionReference":None,
      "decisionReference":None,"decision":"NOT_MADE","reviewOccurred":False},
      "fabricated human reviewer/decision")
    check(all(v is False for v in d["ciSeparation"].values()),
      "CI/PR/merge implied human approval")
    check(old["humanReview"]=={
      "reviewer":None,"reviewedAt":None,"authorityReference":None,
      "decision":"NOT_MADE","decisionReference":None},"F23.3 historical human review mutated")
    check(old["gate"]=={"gateId":"G5","criterion":"A12",
      "status":"GATE-BLOQUEADO","humanSignoff":False},"F23.3 gate status mutated")
    check(d["gate"]=={"gateId":"G5","criterionId":"A12",
      "status":"GATE-BLOQUEADO","humanSignoff":False},"human signoff promoted")
    check(d["evidence"]["observationIds"]==[x["observationId"] for x in suff["observations"]],
      "provenance observation IDs changed")
    check(d["evidence"]["requiredCriteria"]==[x["criterionId"] for x in suff["criteria"]],
      "required criteria IDs changed")
    check(all(o["sufficiency"]=="INSUFFICIENT_PRESERVED" and
      o["provenanceStatus"]=="PENDING-DECLARED" and
      all(c["status"]=="MISSING" and c["humanVerified"] is False and
      c["primaryEvidenceReference"] is None for c in o["criteria"])
      for o in suff["observations"]),"falsely promoted provenance")
    check(d["evidence"]["documentaryEligibility"]=="NOT_ELIGIBLE" and
      d["evidence"]["sufficiency"]=="INSUFFICIENT_PRESERVED" and
      d["evidence"]["historicalProvenanceAttested"] is False,"false sufficiency")
    check(elig["decision"]["documentaryEligibility"]=="NOT_ELIGIBLE" and
      elig["decision"]["humanReviewOccurred"] is False and
      elig["decision"]["humanDecision"]=="NOT_MADE" and
      elig["decision"]["approved"] is False and
      elig["decision"]["operational"] is False,"F24.2 false eligibility")
    check(len(d["riskDecisions"])==len(risks["risks"])==len(old["riskDecisions"])==len(elig["risks"])==8,
      "risk count")
    for a,b,c,e in zip(d["riskDecisions"],risks["risks"],old["riskDecisions"],elig["risks"]):
        check(a["riskId"]==b["riskId"]==c["riskId"]==e["riskId"],"risk identity drift")
        check(a["accepted"] is False and a["acceptanceReference"] is None and
              a["humanAssessmentReference"] is None and b["riskAccepted"] is False and
              c["accepted"] is False and e["accepted"] is False,"risk accepted")
    check(d["outcome"]=={
      "approved":False,"operational":False,"approvedPlayerMaps":0,
      "acceptedRisks":0,"b03":"PENDING-DECLARED","humanApproval":False},
      "operational approval")
    check(old["outcome"]=={"approved":False,"operational":False,"approvedPlayerMaps":0},
      "F23.3 outcome mutated")
def mutate(root,path,val):
    x=copy.deepcopy(root);t=x
    for segment in path[:-1]:t=t[segment]
    t[path[-1]]=val
    return x
def main():
    src=load(D);validate(D,src)
    negative=[
       ("fake-reviewer",("review","reviewer"),"GITHUB_ACTOR"),
       ("fake-reviewed-date",("review","reviewedAt"),"2026-11-20"),
       ("fake-authority",("review","authorityReference"),"CI"),
       ("fake-independence",("review","independenceDeclaration"),"yes"),
       ("fake-conflict-check",("review","conflictOfInterestAssessment"),"clear"),
       ("fake-scope",("review","scopeReference"),"PR25"),
       ("fake-evidence-version",("review","evidenceVersionReference"),"HEAD"),
       ("fake-decision-reference",("review","decisionReference"),"CI"),
       ("decision-made",("review","decision"),"APPROVED"),
       ("review-occurred",("review","reviewOccurred"),True),
       ("CI-is-human",("ciSeparation","ciSuccessIsHumanApproval"),True),
       ("PR-is-human",("ciSeparation","prReviewIsHumanApproval"),True),
       ("Ready-is-human",("ciSeparation","readyForReviewIsHumanApproval"),True),
       ("Merge-is-human",("ciSeparation","mergeIsHumanApproval"),True),
       ("Actor-is-reviewer",("ciSeparation","githubActorIsHumanReviewer"),True),
       ("CI-time-review-date",("ciSeparation","ciTimestampIsReviewDate"),True),
       ("unblock-A12",("gate","status"),"APPROVED"),
       ("false-signoff",("gate","humanSignoff"),True),
       ("false-B03-attestation",("evidence","historicalProvenanceAttested"),True),
       ("false-eligibility",("evidence","documentaryEligibility"),"ELIGIBLE"),
       ("false-sufficiency",("evidence","sufficiency"),"SUFFICIENT"),
       ("wrong-observation",("evidence","observationIds",0),"R07"),
       ("wrong-criterion",("evidence","requiredCriteria",0),"P05"),
       ("risk-accepted",("riskDecisions",0,"accepted"),True),
       ("risk-acceptance-ref",("riskDecisions",1,"acceptanceReference"),"CI"),
       ("risk-human-assessment",("riskDecisions",2,"humanAssessmentReference"),"PR"),
       ("risk-identity",("riskDecisions",3,"riskId"),"RA-08"),
       ("outcome-approved",("outcome","approved"),True),
       ("outcome-operational",("outcome","operational"),True),
       ("outcome-accepted-risks",("outcome","acceptedRisks"),1),
       ("outcome-approved-map",("outcome","approvedPlayerMaps"),1),
       ("outcome-human-approval",("outcome","humanApproval"),True)
    ]
    folder=OUT/"f24-human-cases";folder.mkdir(parents=True,exist_ok=True)
    cases=[]
    for label,path,val in negative:
        candidate=mutate(D,path,val)
        (folder/(label+".json")).write_text(json.dumps(candidate,indent=2),encoding="utf-8")
        try:validate(candidate,src)
        except UndecidedViolation as ex:
            cases.append({"caseId":label,"expectedOutcome":"UndecidedViolation",
              "actualOutcome":"UndecidedViolation","result":"rejected","reason":str(ex)})
        else:raise RuntimeError("F24.3 accepted mutation "+label)
    source_cases=[]
    changes=[
       ("F23.3","reviewer-from-CI",("humanReview","reviewer"),"CI"),
       ("F23.3","signoff-from-CI",("gate","humanSignoff"),True),
       ("F23.3","accepted-legacy-risk",("riskDecisions",0,"accepted"),True),
       ("F24.2","eligibility-from-CI",("decision","documentaryEligibility"),"ELIGIBLE"),
       ("F24.2","review-occurred-from-PR",("decision","humanReviewOccurred"),True),
       ("F24.1","provenance-attested",("observations",0,"provenanceStatus"),"VERIFIED"),
       ("F24.1","source-human-verified",("observations",1,"criteria",0,"humanVerified"),True),
       ("F23.2","risk-accepted-source",("risks",0,"riskAccepted"),True)
    ]
    for stage,label,path,value in changes:
        altered=copy.deepcopy(src);altered[stage]=mutate(src[stage],path,value)
        try:validate(D,altered)
        except UndecidedViolation as ex:
            source_cases.append({"caseId":label,"sourceStage":stage,
              "expectedOutcome":"UndecidedViolation","actualOutcome":"UndecidedViolation",
              "result":"rejected","reason":str(ex)})
        else:raise RuntimeError("F24.3 source mutation accepted "+label)
    check(len(cases)==len({x["caseId"] for x in cases})==32 and
      len(source_cases)==len({x["caseId"] for x in source_cases})==8,
      "test inventory")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"F24HumanReviewNotMade.json").write_bytes(RAW)
    (OUT/"F24HumanReviewNotMade.schema.json").write_bytes(SR)
    (OUT/"F24HumanReviewValidation.json").write_text(json.dumps({
       "schemaVersion":1,"kind":"f24-human-review-validation-not-made",
       "manifestSha256":sha(RAW),"schemaSha256":sha(SR),
       "sourceSha256":{label:sha((ROOT/D["source"][key]).read_bytes()) for label,key in
         (("F23.3","f23HumanPath"),("F24.2","f24EligibilityPath"),
          ("F24.1","f24SufficiencyPath"),("F23.2","f23RisksPath"))},
       "canonicalAccepted":True,"negativeCasesRejected":len(cases),
       "negativeCases":cases,"sourceCasesRejected":len(source_cases),
       "sourceCases":source_cases,"reviewer":None,"reviewedAt":None,
       "decision":"NOT_MADE","acceptedRisks":0,"approved":False,"operational":False,
       "gateA12":"GATE-BLOQUEADO","b03":"PENDING-DECLARED"
     },indent=2),encoding="utf-8")
    print("OK F24.3: NOT_MADE, 8 risks unaccepted, 32/32 negatives, 8/8 linked-source mutations rejected; no approval")
if __name__=="__main__":main()
