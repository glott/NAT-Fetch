#!/usr/bin/env python
# coding: utf-8

# In[ ]:


LAUNCH_VATSYS = True


# In[ ]:


import os, subprocess, sys
from datetime import datetime, timezone

import importlib.util as il
if None in [il.find_spec('requests')]:
    subprocess.check_call([sys.executable, '-m', 'pip', 
                       'install', 'requests']);
    os.system('cls')
    os.execv(sys.executable, ['python'] + sys.argv)
else:
    os.system('cls')

import requests

if 'true' in ' '.join(sys.argv[1:]).lower():
    LAUNCH_VATSYS = True


# In[ ]:


def fetch_nats():
    nats = {}
    all_ints = list()

    # FAA Source
    html = ''
    try: 
        url = 'https://www.notams.faa.gov/common/nat.html'
        html = requests.get(url).text
    except Exception:
        pass
    nat_html = html.split('\n')

    dt = 1000
    for i in range(len(nat_html) - 1):
        line = nat_html[i].split(' ')
        line_ = nat_html[i + 1].split(' ')
    
        if len(line) < 3:
            continue
        
        if 'INCLUSIVE' in line:
            d1, h1 = line_[1].split('/')
            h1, m1 = h1[0:2], h1[2:4]
            utc = datetime.now(timezone.utc)
            d0, h0, m0 = utc.day, utc.hour, utc.minute
    
            if int(d1) != int(d0):
                h1 = int(h1) + 24
            dt = (int(h1) - h0) + (int(m1) - m0) / 60
    
        if len(line[0]) == 1 and (line_[0] == 'EAST' or line_[0] == 'WEST'):
            for j in range(len(line)):
                e = line[j]
                if '/' in e:
                    if len(e) == 5:
                        line[j] = e[0:2] + e[3:] + 'N'
                    elif len(e) == 7:
                        line[j] = 'H' + e[0:2] + e[5:]
                if j != 0 and line[j] not in all_ints:
                    all_ints.append(line[j])
            if dt <= 8:
                nats[line[0]] = ' '.join(line[1:])

    # Flight Plan Database Source
    html = ''
    try:
        url = 'https://flightplandatabase.com/nav/NATS'
        html = requests.get(url).text
    except Exception:
        return nats, sorted(all_ints)
    
    nat_table = html.split('<table')[1].split('</table>')[0].replace('\t', '').replace('\n', '').split('<tr>')
    for row in nat_table:
        if '<td>' not in row:
            continue
        row = row.split('</td><td>')
        
        if len(row) < 4:
            continue
        trk = row[0].replace('<td>', '')
        rte = row[3].strip().split(' ')

        if trk not in nats.keys():
            for j in range(len(rte)):
                e = rte[j]
                if '/' in e:
                    if len(e) == 5:
                        rte[j] = e[0:2] + e[3:] + 'N'
                    elif len(e) == 7:
                        rte[j] = 'H' + e[0:2] + e[5:]
                if rte[j] not in all_ints:
                    all_ints.append(rte[j])
            nats[trk] = ' '.join(rte)
    
    return nats, sorted(all_ints)

def find_ints(all_ints, file):
    ints = {}

    if not os.path.isfile(file):
        return ints

    f = open(file, 'r')

    for l in f:
        l = l.split()
        if l[0] in all_ints:
            ints[l[0]] = [l[2], l[3]]

    f.close()
    return ints

def inject_awys(nats, ints, file):
    if not os.path.isfile(file):
        return

    idx = 0
    lines = ''
    with open(file, 'r') as f:
        lines = f.readlines()

        i = 0
        while i < len(lines):
            if len(lines[i]) > 5 and lines[i][0:3] == 'NAT':
                del lines[i]
            else:
                i += 1
    
    for i in range(min(len(lines), 50)):
        if len(lines[i]) > 1:
            if lines[i][0] == ';':
                idx = i
    idx += 1
    
    for nat in nats:
        trk = 'NAT' + nat
        nat = nats[nat].split(' ')
        for i in range(len(nat)):
            e = nat[i]
            line = trk.ljust(8, ' ') + str(i + 1).rjust(4, '0') + ' ' + e.ljust(20, ' ') \
                + str(ints[e][0]).ljust(14, ' ') + str(ints[e][1]).ljust(14, ' ') + 'H    \n'

            lines.insert(idx, line)
            idx += 1

    with open(file, 'w') as f:
        lines = ''.join(lines)
        f.write(lines)


# In[ ]:


navdata_dir = os.path.expanduser('~') + R'\Documents\vatSys Files\NavData'
ints_file = os.path.join(navdata_dir, 'ints.txt')
awys_file = os.path.join(navdata_dir, 'awys.txt')

if not 'vatSys.exe' in str(subprocess.check_output('tasklist')):
    nats, all_ints = fetch_nats()
    ints = find_ints(all_ints, ints_file)
    inject_awys(nats, ints, awys_file)
    inject_awys(nats, ints, awys_file.replace('Documents', R'OneDrive\Documents'))
    
    if LAUNCH_VATSYS:
        vatsys_dir = os.environ['ProgramFiles(x86)'] + R'\vatSys'
        vatsys_exe = vatsys_dir + R'\bin\vatSys.exe'
        if os.path.isfile(vatsys_exe):
            subprocess.Popen(vatsys_exe, cwd=vatsys_dir)

