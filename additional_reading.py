#!/usr/bin/env python
"""
expected file format:

>DOI1 # TITLE1
- TOPIC1: REF1, REF2, REFa-b
- TOPIC2: REF3, REF4

>DOI2 # TITLE2
- TOPIC1: REF1, REF2, REFa-b
- TOPIC2: REF3, REF4

etc.
"""

import argparse
import requests

def find_delta(a, b):
    prefix = []
    for ca, cb in zip(a, b):
        if ca == cb:
            prefix.append(ca)
        else:
            break
    
    suffix = []
    for ca, cb in zip(a[::-1], b[::-1]):
        if ca == cb:
            suffix.append(ca)
        else:
            break
    
    return len(prefix), len(suffix)

def get_refs(doi):
    endpoint = f"https://api.crossref.org/works/{doi}"
    r = requests.get(endpoint)

    refs = r.json()["message"]["reference"]

    plen, slen = find_delta(refs[0]["key"], refs[1]["key"])

    refs_dict = {}

    for ref in refs:
        key = ref["key"]
        refnum = int(key[plen:len(key)-slen])
        refs_dict[refnum] = ref

    return refs_dict

def normalize(refids):
    refids = refids.split(",")

    normalized = []
    for refid in refids:
        refid = refid.strip()
        if "-" in refid:
            start, stop = refid.split("-")
            expanded = range(int(start), int(stop) + 1)
            normalized.extend(expanded)
        else:
            normalized.append(int(refid))

    return normalized

def main(refs, ofile):
    data = {}
    doi2title = {}
    # data: dict[doi -> dict[topic -> list[refs]]]

    with open(refs) as f:
        topic2refs = {}
        doi = None

        for line in f:
            if line.startswith(">"):
                if doi is not None and len(topic2refs) != 0:
                    data[doi] = topic2refs.copy()

                doi, title = line[1:].split("#")
                doi = doi.strip()
                title = title.strip()
                doi2title[doi] = title
                topic2refs = {}

            elif line.startswith("-"):
                topic, refids = line[1:].strip().split(":")
                topic2refs[topic.strip()] = refids.strip()

        if doi is not None and len(topic2refs) != 0:
            data[doi] = topic2refs.copy()


    with open(ofile, "w") as fout:
        for doi, topic2refs in data.items():
            paperrefs = get_refs(doi)

            fout.write(f"- {doi2title[doi]} (https://www.doi.org/{doi})\n")

            for topic, refids in topic2refs.items():
                refids = normalize(refids)

                fout.write(f"  - {topic}\n")
                for refid in refids:
                    if refid in paperrefs:
                        uid = paperrefs[refid].get("DOI")
                        title = paperrefs[refid].get("article-title")
                        unstructured = paperrefs[refid].get("unstructured", "no title")
                    else:
                        uid = None
                        title = None
                        unstructured = "no title"

                    if uid:
                        uid = f"https://www.doi.org/{uid}"
                    else:
                        uid = f"https://www.doi.org/{doi} ref {refid}"
                    
                    if title:
                        fout.write(f"    - {title} ({uid})\n")
                    else:
                        fout.write(f"    - {unstructured} ({uid})\n")


    print("[i] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("refs")
    parser.add_argument("ofile")
    args = parser.parse_args()
    main(args.refs, args.ofile)
