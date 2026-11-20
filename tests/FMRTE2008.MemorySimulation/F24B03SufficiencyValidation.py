"""F24.1: fail-closed documentary sufficiency checks for B03; no operational access."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator

FOLDER=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[2]
MANIFEST_PATH=FOLDER/"F24B03Sufficiency.json"
SCHEMA_PATH=FOLDER/"F24B03Sufficiency.schema.json"
MANIFEST_BYTES=MANIFEST_PATH.read_bytes()
SCHEMA_BYTES=SCHEMA_PATH.read_bytes()
MANIFEST=json.loads(MANIFEST_BYTES)
SCHEMA=json.loads(SCHEMA_BYTES)
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR=Draft202012Validator(SCHEMA)
FIELDS=("executor","observedAt","environment","collectionMethod","externalCorroboration")
IDS=tuple("R%02d"%i for i in range(1,8))
CRITERIA=tuple("P%02d"%i for i in range(1,6))

class SufficiencyViolation(ValueError):
    pass

def require(condition,detail):
    if not condition:
        raise SufficiencyViolation(detail)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def get_sources(m):
    meta=m["sources"]
    result={}
    for stage,path_key,sha_key in (
        ("F21","f21Path","f21Sha256"),
        ("F23.1","f23B03Path","f23B03Sha256")
    ):
        path=ROOT/meta[path_key]
        require(path.is_file(),stage+" document absent")
        data=path.read_bytes()
        require(sha(data)==meta[sha_key],stage+" source hash mismatch")
        result[stage]=json.loads(data)
    path=ROOT/meta["consolidatedPath"]
    require(path.is_file(),"consolidation document absent")
    result["F23.4"]=json.loads(path.read_bytes())
    return result

def validate(m,refs):
    require(not list(VALIDATOR.iter_errors(m)),"closed B03 sufficiency schema rejected")
    f21=refs["F21"];b03=refs["F23.1"];con=refs["F23.4"]
    meta=m["sources"]
    require(meta["mappingRepository"]==con["sourceRepository"]==b03["source"]["repository"],"source repository drift")
    require(meta["mappingCommit"]==con["sourceCommit"]==b03["source"]["commit"],"mapping commit drift")
    require(meta["f21Path"]==con["sources"][0]["path"] and
            meta["f21Sha256"]==con["sources"][0]["sha256"],"F21 commitment mismatch")
    require(meta["f23B03Path"]==con["sources"][2]["path"] and
            meta["f23B03Sha256"]==con["sources"][2]["sha256"],"B03 commitment mismatch")
    require([x["criterionId"] for x in m["criteria"]]==list(CRITERIA),"criteria order")
    require([x["sourceField"] for x in m["criteria"]]==list(FIELDS),"field mapping")
    require([x["observationId"] for x in m["observations"]]==list(IDS),"observation order")
    require(len(f21["observations"])==len(b03["observations"])==7,"source observation count")
    for i,entry in enumerate(m["observations"]):
        old=f21["observations"][i];new=b03["observations"][i]
        require(entry["observationId"]==old["observationId"]==new["observationId"],"source observation mismatch")
        require(entry["sourcePath"]==old["sourcePath"]==new["sourcePath"],"source path mismatch")
        require(entry["sourceBlobSha"]==old["sourceBlobSha"]==new["sourceBlobSha"],"source blob mismatch")
        require(old["sourceEvidenceStatus"]==new["sourceEvidenceStatus"]==
                entry["sourceEvidenceStatus"]=="user-reported-not-independently-audited","historical status promotion")
        require(old["provenanceStatus"]==new["provenanceStatus"]==
                entry["provenanceStatus"]=="PENDING-DECLARED","B03 provenance promotion")
        require(entry["sufficiency"]=="INSUFFICIENT_PRESERVED","false sufficiency")
        for j,field in enumerate(FIELDS):
            test=entry["criteria"][j]
            require(old[field] is None and new[field] is None,"invented historical metadata "+field)
            require(test["criterionId"]==CRITERIA[j] and test["sourceField"]==field,
                    "criterion/source field mismatch")
            require(test["status"]=="MISSING" and test["primaryEvidenceReference"] is None and
                    test["humanVerified"] is False,"fabricated criterion "+field)
    state=m["decision"]
    require(state=={"approved":False,"operational":False,"gateA12":"GATE-BLOQUEADO",
        "b03":"PENDING-DECLARED","humanApproval":None,"decision":"NOT_MADE",
        "sufficiency":"INSUFFICIENT_PRESERVED","approvedPlayerMaps":0},
        "operational or human promotion")
    require(b03["decision"]["approved"] is False and
            b03["decision"]["operational"] is False and
            b03["decision"]["humanApproval"] is None and
            b03["decision"]["b03"]=="PENDING-DECLARED" and
            b03["decision"]["gateA12"]=="GATE-BLOQUEADO","B03 source approved")

def altered(data,path,value):
    result=copy.deepcopy(data);cur=result
    for key in path[:-1]:
        cur=cur[key]
    cur[path[-1]]=value
    return result

def main():
    refs=get_sources(MANIFEST)
    validate(MANIFEST,refs)
    mutations=[
        ("fake-executor",("observations",0,"criteria",0,"status"),"DOCUMENTED_UNREVIEWED"),
        ("fake-time",("observations",1,"criteria",1,"status"),"REVIEW_REQUIRED"),
        ("fake-environment",("observations",2,"criteria",2,"humanVerified"),True),
        ("fake-method",("observations",3,"criteria",3,"primaryEvidenceReference"),"actions"),
        ("fake-corroboration",("observations",4,"criteria",4,"primaryEvidenceReference"),"github-sha"),
        ("promote-observation",("observations",5,"provenanceStatus"),"VERIFIED"),
        ("promote-source",("observations",6,"sourceEvidenceStatus"),"independently-audited"),
        ("promote-sufficiency",("observations",0,"sufficiency"),"SUFFICIENT"),
        ("wrong-observation",("observations",0,"observationId"),"R07"),
        ("wrong-source-path",("observations",1,"sourcePath"),"fake.md"),
        ("wrong-blob",("observations",2,"sourceBlobSha"),"0"*40),
        ("wrong-criterion",("observations",3,"criteria",0,"criterionId"),"P02"),
        ("wrong-field",("observations",4,"criteria",1,"sourceField"),"executor"),
        ("extra-criterion",("observations",5,"criteria",4,"ciApproved"),True),
        ("replace-criterion-reference",("criteria",0,"sourceField"),"ciActor"),
        ("wrong-f21-hash",("sources","f21Sha256"),"0"*64),
        ("wrong-b03-hash",("sources","f23B03Sha256"),"0"*64),
        ("wrong-mapping-commit",("sources","mappingCommit"),"0"*40),
        ("approve",("decision","approved"),True),
        ("operational",("decision","operational"),True),
        ("unblock-A12",("decision","gateA12"),"APPROVED"),
        ("close-B03",("decision","b03"),"VERIFIED"),
        ("fake-human-approval",("decision","humanApproval"),"CI"),
        ("decision-made",("decision","decision"),"APPROVED"),
        ("approved-map",("decision","approvedPlayerMaps"),1)
    ]
    cases=[]
    evidence=Path(os.environ["RUNNER_TEMP"])/"f20-evidence"
    cases_dir=evidence/"f24-sufficiency-cases"
    cases_dir.mkdir(parents=True,exist_ok=True)
    for name,path,value in mutations:
        candidate=altered(MANIFEST,path,value)
        (cases_dir/(name+".json")).write_text(json.dumps(candidate,indent=2),encoding="utf-8")
        try:
            validate(candidate,refs)
        except SufficiencyViolation as ex:
            cases.append({"caseId":name,"expectedOutcome":"SufficiencyViolation",
                "actualOutcome":"SufficiencyViolation","result":"rejected","reason":str(ex)})
        else:
            raise RuntimeError("F24.1 mutation accepted: "+name)
    source_cases=[]
    for name,stage,path,value in (
        ("f21-forged-executor","F21",("observations",0,"executor"),"CI"),
        ("f21-promote-provenance","F21",("observations",1,"provenanceStatus"),"VERIFIED"),
        ("b03-fabricated-method","F23.1",("observations",2,"collectionMethod"),"CI"),
        ("b03-false-corroboration","F23.1",("observations",3,"externalCorroboration"),"hash"),
        ("b03-forged-status","F23.1",("observations",4,"provenanceStatus"),"VERIFIED")
    ):
        mutated=copy.deepcopy(refs)
        mutated[stage]=altered(refs[stage],path,value)
        try:
            validate(MANIFEST,mutated)
        except SufficiencyViolation as ex:
            source_cases.append({"caseId":name,"sourceStage":stage,
                 "expectedOutcome":"SufficiencyViolation","actualOutcome":"SufficiencyViolation",
                 "result":"rejected","reason":str(ex)})
        else:
            raise RuntimeError("F24.1 source mutation accepted: "+name)
    require(len(cases)==25 and len(set(x["caseId"] for x in cases))==25,"negative inventory")
    require(len(source_cases)==5,"source negative inventory")
    evidence.joinpath("F24B03Sufficiency.json").write_bytes(MANIFEST_BYTES)
    evidence.joinpath("F24B03Sufficiency.schema.json").write_bytes(SCHEMA_BYTES)
    evidence.joinpath("F24B03SufficiencyValidation.json").write_text(json.dumps({
        "schemaVersion":1,"kind":"f24-b03-sufficiency-validation-offline",
        "manifestSha256":sha(MANIFEST_BYTES),"schemaSha256":sha(SCHEMA_BYTES),
        "f21Sha256":sha((ROOT/MANIFEST["sources"]["f21Path"]).read_bytes()),
        "f23B03Sha256":sha((ROOT/MANIFEST["sources"]["f23B03Path"]).read_bytes()),
        "observationsChecked":7,"criteriaChecked":35,"canonicalAccepted":True,
        "negativeCasesRejected":len(cases),"negativeCases":cases,
        "sourceCasesRejected":len(source_cases),"sourceCases":source_cases,
        "approved":False,"operational":False,"humanApproval":False,
        "b03":"PENDING-DECLARED","gateA12":"GATE-BLOQUEADO",
        "decision":"NOT_MADE","sufficiency":"INSUFFICIENT_PRESERVED"
    },indent=2),encoding="utf-8")
    print("OK F24.1: 7 observations x 5 criteria, 25/25 mutations, 5/5 source mutations rejected; no B03 attestation or approval")

if __name__=="__main__":
    main()
