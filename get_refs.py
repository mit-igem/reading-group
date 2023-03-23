#!/usr/bin/env python

import argparse
import json
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

    resp = r.json()["message"]
    refs = resp["reference"]
    title = resp.get("title", ["no title found"])[0]

    plen, slen = find_delta(refs[0]["key"], refs[1]["key"])

    # print(json.dumps(refs, indent=2))

    refs_dict = {}
    offset = None

    for ref in refs:
        key = ref["key"]
        refnum = int(key[plen:len(key)-slen])

        # for papers where key doesn't start at 1
        if offset is None:
            offset = refnum - 1

        refs_dict[refnum - offset] = ref

    return refs_dict, title

def normalize(refids):
    refids = refids.split(",")

    normalized = []
    for refid in refids:
        refid = refid.strip()
        if "-" in refid[1:]:
            start, stop = refid.split("-")
            expanded = range(int(start), int(stop) + 1)
            normalized.extend(expanded)
        else:
            normalized.append(int(refid))

    return normalized

def main(doi):
    paperrefs, title = get_refs(doi)
    print(f"DOI: {doi} ({title})")

    while True:
        user_input = input("> ")

        if user_input.startswith("doi:"):
            doi = user_input[4:].strip()
            paperrefs, title = get_refs(doi)
            print(f"Switching DOI: {doi} ({title})")
            continue

        refids = normalize(user_input)

        for refid in refids:
            if refid not in paperrefs:
                print(f"{refid}. no title (https://www.doi.org/{doi} ref {refid})")
                continue

            uid = paperrefs[refid].get("DOI")
            title = paperrefs[refid].get("article-title")
            unstructured = paperrefs[refid].get("unstructured", "no title")

            unstructured = " ".join(map(lambda s: s.strip(), unstructured.split("\n")))

            if uid:
                uid = f"https://www.doi.org/{uid}"
            else:
                uid = f"https://www.doi.org/{doi} ref {refid}"

            if title:
                print(f"{refid}. {title} ({uid})")
            else:
                print(f"{refid}. {unstructured} ({uid})")

    print("[i] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("doi")
    args = parser.parse_args()

    main(args.doi)
