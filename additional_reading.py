#!/usr/bin/env python

import argparse
import os
import requests

def get_refs(doi):
    endpoint = f"https://api.crossref.org/works/{doi}"
    r = requests.get(endpoint)

    refs = r.json()["message"]["reference"]
    return refs

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
    # data: dict[doi -> dict[topic -> list[refs]]]

    with open(refs) as f:
        topic2refs = {}
        doi = None

        for line in f:
            if line.startswith(">"):
                if doi is not None and len(topic2refs) != 0:
                    data[doi] = topic2refs.copy()

                doi = line[1:].split("#")[0].strip()
                topic2refs = {}

            elif line.startswith("-"):
                topic, refids = line[1:].strip().split(":")
                topic2refs[topic.strip()] = refids.strip()

    with open(ofile, "w") as fout:
        for doi, topic2refs in data.items():
            paperrefs = get_refs(doi)

            fout.write(f"original article: https://www.doi.org/{doi}\n")

            for topic, refids in topic2refs.items():
                refids = normalize(refids)

                fout.write(f"- {topic}\n")
                for refid in refids:
                    uid = paperrefs[refid - 1].get('DOI')

                    if uid:
                        uid = f"https://www.doi.org/{uid}"
                    else:
                        uid = f"https://www.doi.org/{doi} ref {refid}"

                    fout.write(f"  - {uid}\n")

    print("[i] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("refs")
    parser.add_argument("ofile")
    args = parser.parse_args()
    main(args.refs, args.ofile)
