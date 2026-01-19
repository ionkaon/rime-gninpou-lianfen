from collections import defaultdict
from itertools import chain
from datetime import date
import re


def get_freq(s):
    '''
    >>> get_freq('2')
    2.0
    >>> get_freq('2%')
    0.02
    '''
    if s[-1] == '%':
        return float(s[:-1]) * 0.01
    else:
        return float(s)

# Traditional Chinese to Simplified Chinese


with open('TSCharacters.txt', encoding="utf-8") as f:
    d_t2s = {a: bx.split(' ')
             for line in f for a, bx in (line.rstrip().split('\t'),)}

# rime-cantonese dictionary data

d_trad = defaultdict(list)
d_simp = defaultdict(list)

with open('wugniu_gninpou.dict.yaml', encoding="utf-8") as f:
    # skip the yaml header
    for line in f:
        if line == '...\n':
            break
    next(f)

    # dictionary data
    for line in f:
        if line[0] != '#':  # skip comments
            parts = line.rstrip().split('\t')
            char = parts[0]
            if len(char) == 1:  # restrict to single character
                # remove pronunciation with low frequency
                if len(parts) == 2 or get_freq(parts[2]) > 0.07:
                    # replace if a character has two syllables
                    wuphin = parts[1].replace(' ', '')
                    if wuphin == "": continue

                    # the original Traditional Chinese character
                    d_trad[char].append(wuphin)

                    try:
                        for ch in d_t2s[char]:
                            # Simplified Chinese character
                            d_simp[ch].append(wuphin)
                    except KeyError:
                        pass

# override

with open('override.txt', encoding="utf-8") as f1, open('radicals.txt', encoding="utf-8") as f2:
    d_override = {a: bx.split(' ') for line in chain(f1, f2)
                  for a, bx in (line.rstrip().split('\t'),)}

# combine dictionaries

d = {**d_simp, **d_trad, **d_override}

res = []
error_keys = set()

with open('lfzy.tsv', encoding="utf-8") as f:
    for line in f:
        ch = line[0]
        line_clean = re.sub(r"\(.\)", "", line)

        try:
            if " " in line:
                word_l, word_r = re.split(r" +", line_clean[2:-1])
                if len(word_l) > 1 or len(word_r) > 1:
                    word_l = word_l[0]
                    word_r = word_r[0]
                for wuphin_l in d[word_l]:
                    for wuphin_r in d[word_r]:
                        res.append((ch, wuphin_l + "=" + wuphin_r))
            else:
                word = line_clean[2]
                for wuphin in d[word]:
                    res.append((ch, wuphin))
        except KeyError as e:
            cause = e.args[0]
            error_keys.add(cause)

if error_keys:
    with open('missing.log', 'w', encoding="utf-8") as f:
        for k in error_keys:
            print(k, file=f)

with open('../gninpou_lianfen.dict.yaml', 'w', encoding="utf-8", newline="\n") as f:
    f.write("""# Rime dictionary
# encoding: utf-8
#
# Lianfen, the Ningbo dialect version of Liang Fen (兩分) input method.
#
# Based on lfzy data (https://github.com/osfans/MCPDict/blob/master/tools/tables/data/lfzy.tsv),
# and the dictionary of the rime-wugniu_gninpou input method (https://github.com/NGLI/rime-wugniu_gninpou).

---
name: gninpou_lianfen
""" + date.today().strftime('version: "%Y.%m.%d"') +
"""
sort: by_weight
use_preset_vocabulary: true
max_phrase_length: 1
...

""")
    for l, r in res:
        print(l, r, sep='\t', file=f)
