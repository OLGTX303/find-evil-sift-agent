import Evtx.Evtx as evtx
import re, sys

path = "/mnt/windows/Users/PC User/Desktop/security.evtx"
interesting = ["4624","4625","4634","4648","4672","4688","4698","4720","4732"]
count = 0
with evtx.Evtx(path) as log:
    recs = list(log.records())
    print(f"Total records: {len(recs)}")
    for r in recs:
        xml = r.xml()
        eid_m = re.search(r"<EventID[^>]*>(\d+)", xml)
        if not eid_m:
            continue
        eid = eid_m.group(1)
        if eid not in interesting:
            continue
        ts_m  = re.search(r'SystemTime="([^"]+)"', xml)
        usr_m = re.search(r'Name="TargetUserName">(.*?)<', xml)
        log_m = re.search(r'Name="LogonType">(.*?)<', xml)
        ip_m  = re.search(r'Name="IpAddress">(.*?)<', xml)
        row = " | ".join([
            (ts_m.group(1)[:19] if ts_m else "?"),
            eid,
            (usr_m.group(1) if usr_m else "-"),
            (log_m.group(1) if log_m else "-"),
            (ip_m.group(1) if ip_m else "-"),
        ])
        print(row)
        count += 1
        if count > 80:
            break
