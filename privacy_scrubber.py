import copy
import re


_REPLACEMENTS = [
    (r"\bCPIC report\b", "external database record"),
    (r"\bCPIC\b", "external database"),
    (r"\bReport Number\b", "Record ID"),
    (r"\breport number\b", "record id"),
    (r"\barrest report\b", "custody record"),
    (r"\bpolice report\b", "incident record"),
    (r"\bbooking report\b", "intake record"),
    (r"\bwitness materials\b", "supporting materials"),
    (r"\bWitness Materials\b", "Supporting Materials"),
    (r"\bwitness statement\b", "supporting statement"),
    (r"\bWitness Statement\b", "Supporting Statement"),
    (r"\bOfficer Conduct\b", "State Conduct"),
    (r"\bofficer conduct\b", "state conduct"),
    (r"\bOfficer Misconduct\b", "State-Process Concern"),
    (r"\bofficer misconduct\b", "state-process concern"),
    (r"\bPolice Misconduct\b", "Official-Process Concern"),
    (r"\bpolice misconduct\b", "official-process concern"),
    (r"\bpolice bad faith\b", "official bad faith"),
    (r"\bPolice Bad Faith\b", "Official Bad Faith"),
    (r"\bCrown Conduct\b", "Prosecution Review"),
    (r"\bcrown conduct\b", "prosecution review"),
    (r"\bCrown Misconduct\b", "Prosecution Review"),
    (r"\bcrown misconduct\b", "prosecution review"),
    (r"\bProsecutorial Misconduct\b", "Prosecution Concern"),
    (r"\bprosecutorial misconduct\b", "prosecution concern"),
    (r"\bWitness\b", "Source Party"),
    (r"\bwitness\b", "source party"),
    (r"\bOfficer\b", "Official"),
    (r"\bofficer\b", "official"),
    (r"\bSuspect\b", "Subject"),
    (r"\bsuspect\b", "subject"),
]


def scrub_party_identifiers(value):
    if isinstance(value, str):
        text = value
        for pattern, replacement in _REPLACEMENTS:
            text = re.sub(pattern, replacement, text)
        return text
    if isinstance(value, list):
        return [scrub_party_identifiers(item) for item in value]
    if isinstance(value, dict):
        return {
            key: scrub_party_identifiers(item)
            for key, item in value.items()
        }
    return copy.deepcopy(value)
