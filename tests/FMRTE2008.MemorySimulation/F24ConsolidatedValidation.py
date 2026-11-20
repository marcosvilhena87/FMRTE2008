"""F24.4: independent cross-stage document and GitHub CI evidence; fail-closed."""
from __future__ import annotations
import copy,hashlib,json,os,re
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
FOLDER=Path(__file__).resolve().parent
OUT=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
RAW=(FOLDER/"F24ConsolidatedEvidence.json").read_bytes()
SCHEMA_RAW=(FOLDER/"F24ConsolidatedEvidence.schema.json").read_bytes()
DOC=json.loads(RAW);SCHEMA=json.loads(SCHEMA_RAW)
Draft202012Validator.check_schema(SCHEMA)
SCHEMA_VALIDATOR=Draft202012Validator(SCHEMA)
STAGES=("F21","F22","F23.1","F23.2","F23.3","F23.4","F24.1","F24.2","F24.3")
class EvidenceViolation(ValueError):pass
def check(ok,why):
    if not ok:raise EvidenceViolation(why)
def digest(b):return hashlib.sha256(b).hexdigest()
def load_sources(m):
    source={}
    check([x["stage"] for x in m["sources"]]==list(STAGES),"stage order or omission")
    for e in m["sources"]:
        path=ROOT/e["path"]
        check(path.is_file(),"missing document "+e["stage"])
        raw=path.read_bytes()
        check(digest(raw)==e["sha256"],"SHA-256 commitment "+e["stage"])
        source[e["stage"]]=json.loads(raw)
    return source
def validate(m,docs):
    check(not list(SCHEMA_VALIDATOR.iter_errors(m)),"closed schema rejected")
    check(set(docs)==set(STAGES),"missing source")
    f21,f22,b03,risks,human,f23,suff,elig,review=(docs[k] for k in STAGES)
    ids=m["traceability"]
    check(f21["sourceRepo"]==f23["sourceRepository"]==m["sourceRepository"],"source repository")
    check(f21["sourceCommit"]==f23["sourceCommit"]==m["sourceCommit"],"source commit")
    check([x["observationId"] for x in f21["observations"]]==ids["observations"],"F21 observations")
    check([x["observationId"] for x in b03["observations"]]==ids["observations"],"F23.1 observations")
    check([x["observationId"] for x in suff["observations"]]==ids["observations"],"F24.1 observations")
    check([x["gateId"] for x in f22["gates"]]==ids["gates"],"F22 gates")
    check([x["gateId"] for x in elig["gates"]]==ids["gates"],"F24.2 gates")
    check(sorted({x for gate in f22["gates"] for x in gate["criteria"]})==sorted(ids["criteria"]),"A01-A12")
    check([x["riskId"] for x in risks["risks"]]==ids["risks"],"F23.2 risks")
    check([x["riskId"] for x in human["riskDecisions"]]==ids["risks"],"F23.3 risks")
    check([x["riskId"] for x in elig["risks"]]==ids["risks"],"F24.2 risks")
    check([x["riskId"] for x in review["riskDecisions"]]==ids["risks"],"F24.3 risks")
    check([x["criterionId"] for x in suff["criteria"]]==ids["provenanceCriteria"],"P01-P05")
    check(review["evidence"]["requiredCriteria"]==ids["provenanceCriteria"],"F24.3 criteria")
    check(review["evidence"]["observationIds"]==ids["observations"],"F24.3 observations")
    check(f23["sources"]==[
       {"stage":x["stage"],"path":x["path"],"sha256":x["sha256"]}
       for x in m["sources"][:5]],"F23 commitments changed")
    for i,ob in enumerate(suff["observations"]):
        old=f21["observations"][i];source=b03["observations"][i]
        check(old["sourcePath"]==source["sourcePath"]==ob["sourcePath"] and
              old["sourceBlobSha"]==source["sourceBlobSha"]==ob["sourceBlobSha"],"historical path/blob drift")
        check(old["provenanceStatus"]==source["provenanceStatus"]==ob["provenanceStatus"]=="PENDING-DECLARED",
              "historical provenance promoted")
        for item in ob["criteria"]:
            field=item["sourceField"]
            check(old[field] is None and source[field] is None and item["status"]=="MISSING" and
                  item["humanVerified"] is False and item["primaryEvidenceReference"] is None,
                  "fabricated observation "+field)
    for i,g in enumerate(elig["gates"]):
        old=f22["gates"][i]
        check(g["criteria"]==old["criteria"] and g["riskIds"]==old["risks"] and
              g["observationIds"]==[x["observationId"] for x in old["evidenceReferences"]],
              "gate/criteria/risk/observation mismatch")
        check(g["documentaryEligibility"]=="NOT_ELIGIBLE" and g["humanApproval"] is False,
              "gate eligibility promoted")
    for i,x in enumerate(elig["risks"]):
        a=risks["risks"][i];b=review["riskDecisions"][i];c=human["riskDecisions"][i]
        check(x["riskId"]==a["riskId"]==b["riskId"]==c["riskId"],"risk linkage")
        check(x["gateId"]==a["gateId"] and x["criteria"]==a["criteria"] and
              x["observationIds"]==a["observationIds"],"risk source linkage")
        check(x["accepted"] is False and a["riskAccepted"] is False and
              b["accepted"] is False and c["accepted"] is False and
              b["humanAssessmentReference"] is None,"risk promoted")
    check(human["humanReview"]["decision"]==review["review"]["decision"]=="NOT_MADE",
          "decision fabricated")
    check(all(v is None for k,v in review["review"].items() if k not in ("decision","reviewOccurred")),
          "reviewer, date or authority fabricated")
    check(review["review"]["reviewOccurred"] is False,"review occurred")
    check(all(v is False for v in review["ciSeparation"].values()),"CI/PR became human approval")
    check(human["gate"]["status"]==review["gate"]["status"]=="GATE-BLOQUEADO" and
          human["gate"]["humanSignoff"] is False and review["gate"]["humanSignoff"] is False,
          "A12 human signoff promoted")
    check(m["decision"]=={
      "approved":False,"operational":False,"approvedPlayerMaps":0,"acceptedRisks":0,
      "b03":"PENDING-DECLARED","gateA12":"GATE-BLOQUEADO",
      "documentaryEligibility":"NOT_ELIGIBLE","sufficiency":"INSUFFICIENT_PRESERVED",
      "humanDecision":"NOT_MADE","humanReviewOccurred":False,"ciIsHumanApproval":False,
      "prReviewIsHumanApproval":False},"F24.4 decision promoted")
    check(m["provenance"]=={
      "historicalAttestation":False,"humanReviewer":None,"humanReviewDate":None,
      "humanAuthority":None,"observationSourceIndependent":False},
      "F24.4 provenance promoted")
    check(f22["decision"]["approved"] is False and
          f22["decision"]["operational"] is False and
          f22["decision"]["gateA12"]=="GATE-BLOQUEADO" and
          f22["decision"]["b03"]=="PENDING-DECLARED","F22 gate/decision promoted")
    check(b03["decision"]["approved"] is False and
          b03["decision"]["operational"] is False and
          b03["decision"]["gateA12"]=="GATE-BLOQUEADO" and
          b03["decision"]["b03"]=="PENDING-DECLARED","F23.1 decision promoted")
    check(risks["decision"]["approved"] is False and
          risks["decision"]["operational"] is False and
          risks["decision"]["decisionStatus"]=="NOT_MADE" and
          risks["decision"]["gateA12"]=="GATE-BLOQUEADO","F23.2 decision promoted")
    check(suff["decision"]["approved"] is False and
          suff["decision"]["operational"] is False and
          suff["decision"]["decision"]=="NOT_MADE" and
          suff["decision"]["sufficiency"]=="INSUFFICIENT_PRESERVED","F24.1 decision promoted")
    check(f23["approval"]["approved"] is False and f23["approval"]["operational"] is False
          and f23["approval"]["gateA12"]=="GATE-BLOQUEADO","F23 approval drift")
    check(elig["decision"]["approved"] is False and elig["decision"]["operational"] is False
          and elig["decision"]["documentaryEligibility"]=="NOT_ELIGIBLE","eligibility drift")
    check(review["outcome"]["approved"] is False and review["outcome"]["operational"] is False
          and review["outcome"]["approvedPlayerMaps"]==0,"F24.3 outcome drift")
def check_reports(m):
    files=[]
    for entry in m["sources"]:
        f=OUT/entry["report"]
        check(f.is_file(),"missing structured report "+entry["stage"])
        rep=json.loads(f.read_text(encoding="utf-8"))
        cases=rep["negativeCases"];ids=[x["caseId"] for x in cases]
        check(rep[entry["hashField"]]==entry["sha256"],"report digest "+entry["stage"])
        check(rep[entry["countField"]]==len(cases)==len(set(ids))==entry["negativeCases"],
              "report count/case IDs "+entry["stage"])
        check(all(c["result"]=="rejected" for c in cases),"non-rejected case "+entry["stage"])
        check(rep["approved"] is False and rep["operational"] is False,"report approval "+entry["stage"])
        files.append({"stage":entry["stage"],"report":entry["report"],
           "sourceSha256":entry["sha256"],"negativeCasesRejected":len(cases),
           "uniqueCaseIds":len(set(ids)),"result":"verified"})
    independent={
       "F22":("F22IndependentSchemaValidation.json",32),
       "F23.1":("F23IndependentSchemaValidation.json",22),
       "F23.2":("F23ResidualRiskIndependentSchemaValidation.json",25),
       "F23.3":("F23HumanDecisionIndependentSchemaValidation.json",28),
       "F24.1":("F24B03SufficiencyIndependentValidation.json",25),
       "F24.2":("F24DocumentaryEligibilityIndependentValidation.json",28),
       "F24.3":("F24HumanReviewIndependentValidation.json",32)
    }
    for stage,(path,count) in independent.items():
        rep=json.loads((OUT/path).read_text(encoding="utf-8"))
        check(rep["canonicalAccepted"] is True and rep["negativeCasesRejected"]==count
              and len(rep["negativeCases"])==count
              and len({x["caseId"] for x in rep["negativeCases"]})==count
              and all((x["actual"] if stage=="F22" else x["result"])=="rejected" and
                      x["schemaErrorCount"]>0 and (stage!="F22" or x["expected"]=="rejected")
                      for x in rep["negativeCases"]),stage+" independent negative")
        prior=json.loads((OUT/next(x["report"] for x in m["sources"] if x["stage"]==stage)).read_text(encoding="utf-8"))
        check({x["caseId"] for x in prior["negativeCases"]}==
              {x["caseId"] for x in rep["negativeCases"]},stage+" independent ID mismatch")
        files.append({"stage":stage+"-independent","report":path,
            "negativeCasesRejected":count,"uniqueCaseIds":count,"result":"verified"})
    return files
def run_identity():
    ex=json.loads((OUT/"F20ExecutionEvidence.json").read_text(encoding="utf-8"))
    check(ex["workflowRunId"]==os.environ["GITHUB_RUN_ID"] and
          ex["workflowAttempt"]==os.environ["GITHUB_RUN_ATTEMPT"] and
          ex["eventName"]==os.environ["GITHUB_EVENT_NAME"],"GitHub CI run identity")
    check(ex["checkoutSha"]==os.environ["GITHUB_SHA"],"checkout identity")
    check(re.fullmatch("[0-9a-f]{40}",ex["prHeadSha"]) is not None,"PR head identity format")
    check(ex["mappingCommit"]==DOC["sourceCommit"],"mapping commit identity")
    check(ex["approval"]["approved"] is False and
          ex["approval"]["operational"] is False,"CI approved maps")
    prev=json.loads((OUT/"F23ConsolidatedValidation.json").read_text(encoding="utf-8"))
    check(prev["execution"]["runId"]==ex["workflowRunId"] and
          prev["execution"]["event"]==ex["eventName"] and
          prev["execution"]["checkoutSha"]==ex["checkoutSha"] and
          prev["execution"]["prHeadSha"]==ex["prHeadSha"],"F23 CI linked identity")
    return {"workflowRunId":ex["workflowRunId"],"workflowAttempt":ex["workflowAttempt"],
      "eventName":ex["eventName"],"checkoutSha":ex["checkoutSha"],
      "prHeadSha":ex["prHeadSha"],"checkoutAndPrHeadDistinct":ex["checkoutSha"]!=ex["prHeadSha"],
      "mappingCommit":ex["mappingCommit"],"ciIsHumanApproval":False}
def changed(obj,path,value):
    x=copy.deepcopy(obj);y=x
    for step in path[:-1]:y=y[step]
    y[path[-1]]=value
    return x
def negative(name,group,m,docs):
    try:validate(m,docs)
    except EvidenceViolation as e:
        return {"caseId":name,"group":group,"expectedOutcome":"EvidenceViolation",
          "actualOutcome":"EvidenceViolation","result":"rejected","reason":str(e)}
    raise RuntimeError("F24.4 accepted mutation "+name)
def main():
    docs=load_sources(DOC);validate(DOC,docs)
    reports=check_reports(DOC)
    execution=run_identity()
    mutations=[
      ("fake-reviewer",("provenance","humanReviewer"),"GitHub actor"),
      ("fake-review-date",("provenance","humanReviewDate"),"CI timestamp"),
      ("fake-authority",("provenance","humanAuthority"),"PR review"),
      ("historical-attestation",("provenance","historicalAttestation"),True),
      ("independent-observation",("provenance","observationSourceIndependent"),True),
      ("approved",("decision","approved"),True),
      ("operational",("decision","operational"),True),
      ("approved-map",("decision","approvedPlayerMaps"),1),
      ("accepted-risk",("decision","acceptedRisks"),1),
      ("unblock-A12",("decision","gateA12"),"APPROVED"),
      ("verify-B03",("decision","b03"),"VERIFIED"),
      ("eligible",("decision","documentaryEligibility"),"ELIGIBLE"),
      ("sufficient",("decision","sufficiency"),"SUFFICIENT"),
      ("decision-made",("decision","humanDecision"),"APPROVED"),
      ("review-occurred",("decision","humanReviewOccurred"),True),
      ("CI-human",("decision","ciIsHumanApproval"),True),
      ("PR-human",("decision","prReviewIsHumanApproval"),True),
      ("wrong-mapping-commit",("sourceCommit",),"0"*40),
      ("wrong-f21-hash",("sources",0,"sha256"),"0"*64),
      ("wrong-f22-path",("sources",1,"path"),"fake.json"),
      ("wrong-b03-stage",("sources",2,"stage"),"F21"),
      ("wrong-risk-report",("sources",3,"report"),"missing.json"),
      ("wrong-F23.3-hash",("sources",4,"sha256"),"0"*64),
      ("wrong-F23.4-hash",("sources",5,"sha256"),"0"*64),
      ("wrong-F24.1-hash",("sources",6,"sha256"),"0"*64),
      ("wrong-F24.2-hash",("sources",7,"sha256"),"0"*64),
      ("wrong-F24.3-hash",("sources",8,"sha256"),"0"*64),
      ("wrong-observation",("traceability","observations",0),"R07"),
      ("wrong-gate",("traceability","gates",0),"G5"),
      ("wrong-A12",("traceability","criteria",11),"A11"),
      ("wrong-risk",("traceability","risks",0),"RA-08"),
      ("wrong-provenance",("traceability","provenanceCriteria",0),"P05")
    ]
    folder=OUT/"f24-consolidated-cases";folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,path,value in mutations:
        mutated=changed(DOC,path,value)
        (folder/(name+".json")).write_text(json.dumps(mutated,indent=2),encoding="utf-8")
        records.append(negative(name,"manifest",mutated,docs))
    source_mutations=[
      ("F21","historical-executor",("observations",0,"executor"),"CI"),
      ("F22","gate-approval",("decision","gateA12"),"APPROVED"),
      ("F23.1","B03-promoted",("observations",0,"provenanceStatus"),"VERIFIED"),
      ("F23.2","risk-accepted",("risks",0,"riskAccepted"),True),
      ("F23.3","human-decided",("humanReview","decision"),"APPROVED"),
      ("F23.4","F23-approved",("approval","approved"),True),
      ("F24.1","criterion-verified",("observations",0,"criteria",0,"humanVerified"),True),
      ("F24.2","eligibility-promoted",("decision","documentaryEligibility"),"ELIGIBLE"),
      ("F24.3","CI-promoted",("ciSeparation","ciSuccessIsHumanApproval"),True),
      ("F24.3","reviewer-forged",("review","reviewer"),"GITHUB_ACTOR"),
      ("F24.2","gate-human-approved",("gates",4,"humanApproval"),True),
      ("F24.3","risk-human-accepted",("riskDecisions",0,"accepted"),True)
    ]
    for stage,name,path,value in source_mutations:
        changed_docs=copy.deepcopy(docs);changed_docs[stage]=changed(docs[stage],path,value)
        records.append(negative(name,"source",DOC,changed_docs))
    check(len(records)==44 and len(set(x["caseId"] for x in records))==44,"negative inventory")
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"F24ConsolidatedEvidence.json").write_bytes(RAW)
    (OUT/"F24ConsolidatedEvidence.schema.json").write_bytes(SCHEMA_RAW)
    report={
      "schemaVersion":1,"kind":"f24-consolidated-ci-evidence-offline",
      "manifestSha256":digest(RAW),"schemaSha256":digest(SCHEMA_RAW),
      "canonicalAccepted":True,"sourcesVerified":9,
      "priorReportsVerified":len(reports),"priorReports":reports,
      "execution":execution,
      "negativeCasesRejected":len(records),"negativeCases":records,
      "manifestMutationsRejected":32,"sourceMutationsRejected":12,
      "approved":False,"operational":False,"humanApproval":False,
      "b03":"PENDING-DECLARED","gateA12":"GATE-BLOQUEADO",
      "documentaryEligibility":"NOT_ELIGIBLE","decision":"NOT_MADE"}
    (OUT/"F24ConsolidatedValidation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("OK F24.4: 9 SHA-256 sources, "+str(len(reports))+
      " prior CI reports, 32/32 manifest negatives, 12/12 source negatives; no approval")
    print("OK F24.4 CI: run="+execution["workflowRunId"]+
      " event="+execution["eventName"]+" checkout="+execution["checkoutSha"]+
      " prHead="+execution["prHeadSha"]+" manifestSHA256="+report["manifestSha256"])
if __name__=="__main__":main()
