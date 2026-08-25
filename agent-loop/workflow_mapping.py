from pathlib import Path


# TODO:
# verify and remove if not used
file_map = {
    "pre_extraction_details": "reports/artifacts/pre_extraction/pre_extraction_details.txt",
    "pains": "reports/artifacts/final/Executive Summary/Key pain points in the current state_10.txt",
    "background": "reports/artifacts/final/Executive Summary/Background_09.txt",
    "end_goal": "reports/artifacts/final/Key End State Goals_25.txt",
    "constraints": "reports/artifacts/final/Key constraints for modernisation_30.txt",
    "lessons_learnt": "reports/artifacts/final/Lessons from previous modernisation initiatives_27.txt",
    "key_advisory_goals": "reports/artifacts/final/Executive Summary/Key Goals of Advisory_07.txt",
    "existing_architecture": "reports/artifacts/final/Existing system/Architecture_40.txt",
    "techstack": "reports/artifacts/final/Existing system/Current Technology Stack_45.txt",
    "nfr": "reports/artifacts/final/Existing system/Non-Functional Requirements_50.txt",
    "recommendation_approach": "reports/artifacts/final/Executive Summary/Recommended Modernisation Approach_20.txt",
    "proposed_architecture": "reports/artifacts/final/Proposed Next Generation System/Proposed Architecture_55.txt",
    "recommended_techstack": "reports/artifacts/final/Proposed Next Generation System/Technology Stack_60.txt",
    "timelines": "reports/artifacts/final/Proposed Next Generation System/Timelines_90.txt",
    "roadmap": "reports/artifacts/final/Proposed Next Generation System/roadmap_70.txt",
    "roles_and_efforts": "reports/artifacts/final/Proposed Next Generation System/Roles and Efforts_95.txt",
    "cost_estimation": "reports/artifacts/final/Proposed Next Generation System/Cost_96.txt",
    "implementation_summary": "reports/artifacts/final/Executive Summary/Implementation Summary_30.txt",
    "glossary": "reports/artifacts/final/Glossary_97.txt"

}

TMP_FILE_MAP = {
    "pre_extraction_details": "reports/artifacts/pre_extraction/pre_extraction_details.txt",
    "pains": "reports/artifacts/tmp/pains.txt",
    "background": "reports/artifacts/tmp/background.txt",
    "end_goal": "reports/artifacts/tmp/goals.txt",
    "constraints": "reports/artifacts/tmp/constraints.txt",
    "lessons_learnt": "reports/artifacts/tmp/lessons.txt",
    "key_advisory_goals": "reports/artifacts/tmp/Key Goals of Advisory.txt",
    "existing_architecture": "reports/artifacts/tmp/existing_architecture.txt",
    "techstack": "reports/artifacts/tmp/current_Technology_stack.txt",
    "nfr": "reports/artifacts/tmp/system_nfr.txt",
    "recommendation_approach": "reports/artifacts/recommendation/approach.txt",
    "proposed_architecture": "reports/artifacts/tmp/proposed_architecture.txt",
    "recommended_techstack": "reports/artifacts/tmp/proposed_techstack.txt",
    "timelines": "reports/artifacts/tmp/timelines.txt",
    "roadmap": "reports/artifacts/tmp/roadmap.txt",
    "roles_and_efforts": "reports/artifacts/tmp/roles_and_efforts.txt",
    "cost_estimation": "reports/artifacts/tmp/cost.txt",
    "implementation_summary": "reports/artifacts/tmp/implementation_summary.txt",
    "glossary": "reports/artifacts/tmp/glossary.txt",
    "recommendation_comparison": "reports/artifacts/tmp/recommendation_comparison.txt"

}

ARTIFACT_FILES = {
    "reports/artifacts/pre_extraction/pre_extraction_details.txt": "pre_extraction_details",
    "reports/artifacts/final/Executive Summary/Key pain points in the current state_10.txt": "pains",
    "reports/artifacts/final/Executive Summary/Background_09.txt": "background",
    "reports/artifacts/final/Key End State Goals_25.txt": "end_goal",
    "reports/artifacts/final/Key constraints for modernisation_30.txt": "constraints",
    "reports/artifacts/final/Lessons from previous modernisation initiatives_27.txt": "lessons_learnt",
    "reports/artifacts/final/Executive Summary/Key Goals of Advisory_07.txt": "key_advisory_goals",
    "reports/artifacts/final/Existing system/Architecture_40.txt": "existing_architecture",
    "reports/artifacts/final/Existing system/Current Technology Stack_45.txt": "techstack",
    "reports/artifacts/final/Existing system/Non-Functional Requirements_50.txt": "nfr",
    "reports/artifacts/final/Executive Summary/Recommended Modernisation Approach_20.txt": "recommendation_approach",
    "reports/artifacts/final/Proposed Next Generation System/Proposed Architecture_55.txt": "proposed_architecture",
    "reports/artifacts/final/Proposed Next Generation System/Technology Stack_60.txt": "recommended_techstack",
    "reports/artifacts/final/Proposed Next Generation System/Timelines_90.txt": "timelines",
    "reports/artifacts/final/Proposed Next Generation System/roadmap_70.txt": "roadmap",
    "reports/artifacts/final/Proposed Next Generation System/Roles and Efforts_95.txt": "roles_and_efforts",
    "reports/artifacts/final/Proposed Next Generation System/Cost_96.txt": "cost_estimation",
    "reports/artifacts/final/Executive Summary/Implementation Summary_30.txt": "implementation_summary",
    "reports/artifacts/final/Glossary_97.txt": "glossary",
    "reports/artifacts/tmp/Recommendation Comparison_98.txt": "recommendation_comparison"

}

def get_workflow(artifact_file):
    for file in ARTIFACT_FILES:
        if str(Path(artifact_file).as_posix()).endswith(file):
            return ARTIFACT_FILES[file]

