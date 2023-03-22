#!/usr/bin/env python

import argparse
import json
import requests

def get_refs(doi):
    endpoint = f"https://api.crossref.org/works/{doi}"
    r = requests.get(endpoint)

    resp = r.json()["message"]
    refs = resp["reference"]
    title = resp.get("title", ["no title found"])[0]

    return refs, title

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
            if refid - 1 >= len(paperrefs):
                print("refid out of range")
                continue

            if refid - 1 < 0:
                print("refid out of range")
                continue

            uid = paperrefs[refid - 1].get("DOI")
            title = paperrefs[refid - 1].get("article-title")
            unstructured = paperrefs[refid - 1].get("unstructured", "no title")

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
