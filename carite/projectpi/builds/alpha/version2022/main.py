# import standard python libraries
import re
import json
import shutil
import sys
import os
import hashlib
import difflib
import platform
import subprocess
import datetime
import time
import logging
import random
import traceback

# import external
from langlist import get_list_of_reference_languages
from phono import phonoInvToTable

# version!
local_version = 2

# import pip libraries and error if necessary
try:
    import jinja2
except:
    print("WARNING: Unable to load jinja2")
    print("WARNING: Please install it through pip install jinja2")
    sys.exit()

try:
    import latexcompiler
except:
    print("WARNING: Unable to load latexcompiler")
    print("WARNING: Please install it through pip install latexcompiler")
    sys.exit()

try:
    import PySimpleGUI
except:
    print("WARNING: Unable to load PYSimpleGui")
    print("WARNING: Please install it through pip install pysimplegui")
    sys.exit()

import PySimpleGUI as sg

# load latexcompiler & jinja
from latexcompiler import LC
from jinja2 import Template
latex_jinja_env = jinja2.Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = jinja2.FileSystemLoader("%s/system_files" % os.path.abspath('.'))
)

# lesgo

debug = ("debug" in sys.argv)
if debug:
    print("Debug enabled!")

if getattr(sys, 'frozen', False):
    application_path = sys.executable.replace("\\","/").rsplit("/", 1)[0]
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# log uncaught exceptions
if not debug:
    logger = logging.getLogger('logger')
    fh = logging.FileHandler('%s/log.log' % application_path)
    logger.addHandler(fh)
    def exc_handler(exctype, value, tb):
        logger.exception(''.join(traceback.format_exception(exctype, value, tb)))
    sys.excepthook = exc_handler

f_sources = open("%s/sources.json" % application_path, encoding='utf8')
dt_sources = json.load(f_sources)

# parse bibliography
def parse_bibliography():
    global source_dict
    print("Parsing bibliography...")
    output = True
    internals = []
    # go through sources, add year=0 if missing and add a failsafe if amount of first and last names don't match
    for entry in dt_sources['sources']:
        if not 'year' in entry:
            entry['year'] = 0
            print("Added missing year entry for '%s'" % entry['title'])
        if len(entry['firstname']) != len(entry['lastname']):
            output = False
            print("The amount of first and last names for '%s' do not match. Please fix this and try again." % entry['title'])
        if 'internalreference' in entry:
            internals.append(entry['internalreference'])
    # reorder sources alphabetically (by last name), then by year, then by title
    dt_sources['sources'] = sorted(dt_sources['sources'], key = lambda x: (x['lastname'][0], x['year'], x['title']))
    # add/update reference text & internal
    for i, entry in enumerate(dt_sources['sources']):
        # to do: add support for multiple sources with the same name+year
        # store it
        entry['reference'] = "%s (%s)" % (entry['lastname'][0], entry['year'])
        if not 'internalreference' in entry:
            offset = 0
            while (entry['lastname'][0] + str(offset)) in internals:
                offset += 1
            entry['internalreference'] = entry['lastname'][0] + str(offset)
            internals.append(entry['lastname'][0] + str(offset))
        source_dict[entry['internalreference']] = i
    # dump it
    save_json(dt_sources, "sources.json")
    print("Bibliography parsed correctly!")
    return output

# apply sound changes (arg1) to a word (arg0)
def apply_sc(word,sc,sporadic_input):
    sporadic_list = {}
    applied_rules = []
    i = -1
    for group in sc:
        oldword2 = str(word)
        i = i + 1
        # if repeat changes is true, keeps repeating all regexes until the word no longer changes
        if 'repeatchanges' in group:
            oldword = ""
            triggered = False
            while oldword != word:
                oldword = word
                for set in group['changes']:
                    for reg in set['regex']:
                        word = re.sub(reg[0], reg[1], word)
                if oldword != word:
                    triggered = True
            if triggered == True:
                applied_rules.append([i, 0])
        elif 'sporadic' in group:
            oldword = word
            for set in group['changes']:
                for reg in set['regex']:
                    word = re.sub(reg[0], reg[1], word)
            if oldword != word:
                apply_sporadicness = False
                if group['sporadic'] in sporadic_input:
                    apply_sporadicness = sporadic_input[group['sporadic']]
                if apply_sporadicness == False:
                    word = oldword
                    sporadic_list[group['sporadic']] = False
                else:
                    sporadic_list[group['sporadic']] = True
                    applied_rules.append([i, 0])
        else:
            for j, set in enumerate(group['changes']):
                oldword = word
                for reg in set['regex']:
                    word = re.sub(reg[0], reg[1], word)
                if oldword != word:
                    applied_rules.append([i, j])
                    if debug == True:
                        if 'display' in set:
                            print("%s: %s" % (set['display'], word))
                        else:
                            print(word)
        for x in applied_rules:
            if x[0] == i:
                x.append(oldword2)
                x.append(word)
    return(word, sporadic_list, applied_rules)

# apply orthography rules
def apply_orthography(word, rules, capitalise):
    lst = []
    for spelling in rules:
        wrd = word
        for reg in spelling['rules']:
            wrd = re.sub(reg[0], reg[1], wrd)
        if capitalise:
            wrd = wrd.capitalize()
        lst.append(wrd)
    return lst

# pronunciation
def get_pronunciation(word, rules):
    for rule in rules:
        word = re.sub(rule[0], rule[1], word)
    return word

def pie_to_apie(word):
    # add actual check for illegal characters later
    word = word.lower()
    substitutes = [
        ["\*", ""],
        ["ḱ", "k'"],
        ["ǵ", "g'"],
        ["ʷ", "v"],
        ["ʰ", "h"],
        ["ĺ̥", "\"l."],
        ["ŕ̥", "\"r."],
        ["̥", "."],
        ["h₁", "x1"],
        ["h₂", "x2"],
        ["h₃", "x3"],
        ["hₓ", "xx"],
        ["á", "\"a"],
        ["é", "\"e"],
        ["í", "\"i"],
        ["ó", "\"o"],
        ["ú", "\"u"],
        ["ā", "a:"],
        ["ē", "e:"],
        ["ī", "i:"],
        ["ō", "o:"],
        ["ū", "u:"],
        ["ā́", "\"a:"],
        ["ḗ", "\"e:"],
        ["ḗ", "\"e:"],
        ["ī́", "\"i:"],
        ["ṓ", "\"o:"],
        ["ū́", "\"u:"]
    ]
    for i in substitutes:
        word = re.sub(i[0], i[1], word)
    return word

def apie_to_pie(word):
    substitutes = [
        ["k'", "ḱ"],
        ["g'", "ǵ"],
        ["([kg])v", "\\1ʷ"],
        ["([pbtdkḱgǵ]v?)h", "\\1ʰ"],
        ["\"l.", "ĺ̥"],
        ["\"r.", "ŕ̥"],
        ["\.", "̥"],
        ["x1", "h₁"],
        ["x2", "h₂"],
        ["x3", "h₃"],
        ["xx", "hₓ"],
        ["\"a:", "ā́"],
        ["\"e:", "ḗ"],
        ["\"i:", "ī́"],
        ["\"o:", "ṓ"],
        ["\"u:", "ū́"],
        ["\"a", "á"],
        ["\"e", "é"],
        ["\"i", "í"],
        ["\"o", "ó"],
        ["\"u", "ú"],
        ["a:", "ā"],
        ["e:", "ē"],
        ["i:", "ī"],
        ["o:", "ō"],
        ["u:", "ū"],
        ["\"@", "ǝ́"], # this is a carite hack, should probably be removed later!
        ["@", "ǝ"] # this is a carite hack, should probably be removed later!
    ]
    for i in substitutes:
        word = re.sub(i[0], i[1], word)
    return "*" + word

def get_list_of_stages():
    lst = []
    for i in dt_general["stages"]:
        lst.append(i['name'])
    return lst

def get_list_of_cases():
    return [["NOM", "Nominative"],["VOC", "Vocative"],["ACC", "Accusative"],["GEN", "Genitive"],["ABL", "Ablative"],["DAT", "Dative"],["LOC", "Locative"],["INS", "Instrumental"]]

def get_number_name(inp):
    out = "?"
    match inp:
        case "SG":
            out = "Singular"
        case "DU":
            out = "Dual"
        case "PL":
            out = "Plural"
    return out

def repair_vocabulary(stage):
    wd_progresswindow = sg.Window('Project π', [[sg.Text("Progress", key='-TEXT-')]], finalize=True)
    vocab_retained = 0
    vocab_changed = 0
    for i, entry in enumerate(dt_vocab['vcb'][stage]):
        oldword = entry['lemma']
        newword, sporadic_list, applied_list = apply_sc(entry['pie_formation2'],dt_sound_changes['sc'][stage],entry['sporadics'])
        if oldword == newword:
            vocab_retained += 1
        else:
            vocab_changed += 1
        entry['lemma'] = newword
        entry['sporadics'] = sporadic_list
        entry['ortho'] = apply_orthography(newword, dt_general['stages'][stage]['orthography'], entry['capitalise'])
        entry['applied_changes'] = applied_list
        wd_progresswindow['-TEXT-'].update("Repairing %s vocabulary: %s/%s" % (get_list_of_stages()[stage], i, len(dt_vocab['vcb'][stage])))
        wd_progresswindow.read(timeout=1)
    save_json(dt_vocab,"%s/vocab.json" % project_name)
    if not brand_new_project and vocab_changed > 0:
        sg.popup("Repaired %s vocabulary: %s entries retained, %s entries fixed" % (get_list_of_stages()[stage], vocab_retained, vocab_changed), title="Project π", keep_on_top=True)
    # also applies SC again to declension endings
    if 'declhash' in dt_cache:
        vocab_retained = 0
        vocab_changed = 0
        for entry in dt_declensions['decl'][stage]:
            for i, dt in enumerate(dt_declensions['decl'][stage][entry]['input']):
                for j, inp in enumerate(dt):
                    oldword = dt_declensions['decl'][stage][entry]['output'][i][j]
                    newword = apply_sc(inp, dt_sound_changes['sc'][stage], {})[0]
                    if oldword == newword:
                        vocab_retained += 1
                    else:
                        vocab_changed += 1
                        dt_declensions['decl'][stage][entry]['output'][i][j] = newword
            wd_progresswindow['-TEXT-'].update("Repairing %s declensions: %s/%s" % (get_list_of_stages()[stage], list(dt_declensions['decl'][stage].keys()).index(entry), len(dt_declensions['decl'][stage])))
            wd_progresswindow.read(timeout=1)
        save_json(dt_declensions,"%s/declensions.json" % project_name)
        dt_cache['declhash'][stage] = declension_to_key(dt_declensions['decl'][stage])
        save_json(dt_cache, "%s/cache.json" % project_name)
        if not brand_new_project and vocab_changed > 0:
            sg.popup("Repaired %s inflections: %s affixes retained, %s affixes fixed" % (get_list_of_stages()[stage], vocab_retained, vocab_changed), title="Project π", keep_on_top=True)
    wd_progresswindow.close()

def repair_orthography(stage):
    vocab_retained = 0
    vocab_changed = 0
    for entry in dt_vocab['vcb'][stage]:
        if 'ortho' in entry:
            oldword = entry['ortho']
        else:
            oldword = ""
        newword = apply_orthography(entry['lemma'], dt_general['stages'][stage]['orthography'], entry['capitalise'])
        if oldword == newword:
            vocab_retained += 1
        else:
            vocab_changed += 1
            entry['ortho'] = newword
    save_json(dt_vocab,"%s/vocab.json" % project_name)
    if not brand_new_project:
        sg.popup("Repaired %s orthography: %s entries retained, %s entries fixed" % (get_list_of_stages()[stage], vocab_retained, vocab_changed), title="Project π", keep_on_top=True)

def is_orphaned_lemma(word):
    return not ('declension' in word)

def repair_declension(stage):
    # look for orphans and decouple them!
    noOrphans = True
    for entry in dt_vocab['vcb'][stage]:
        if 'declension' in entry:
            if entry['declension'] not in dt_declensions['decl'][stage].keys():
                print("Stage %s lemma %s orphaned: no declension %s found!" % (stage, entry['lemma'], entry['declension']))
                del entry['declension']
    if noOrphans:
        print("No new orphans found in stage %s!" % stage)

def save_json(data, file):
    jsonobj = json.dumps(data, indent=4, ensure_ascii=False)
    with open(file, "w", encoding='utf8') as outfile:
        outfile.write(jsonobj)
    # also save last edited information
    if not chose_folder:
        return
    dt_general['general_settings']['timespent'] = int(time.time() - edit_start_time + edit_start_time_extra)
    dt_general['general_settings']['lastedited'] = datetime.datetime.now().isoformat()
    jsonobj = json.dumps(dt_general, indent=4, ensure_ascii=False)
    with open("%s/general.json" % project_name, "w", encoding='utf8') as outfile:
        outfile.write(jsonobj)

def sound_changes_to_key(soundchanges):
    string = ""
    for entry in soundchanges:
        if "sporadic" in entry:
            string += entry["sporadic"]
        if "repeatchanges" in entry:
            string += "REPEATCHANGES"
        for changes in entry['changes']:
            for regex in changes['regex']:
                string += regex[0] + regex[1]
    return(hashlib.md5(string.encode()).hexdigest())

def orthography_to_key(ortho):
    string = ""
    for entry in ortho:
        for regex in entry['rules']:
                string += regex[0] + regex[1]
    return(hashlib.md5(string.encode()).hexdigest())

def declension_to_key(declension):
    return(hashlib.md5(str(declension).encode()).hexdigest())

def get_compatible_declensions(word, declensionlist):
    lst = []
    for entry, dict in declensionlist.items():
        isMatch = True
        # automaticlaly false if both bits are empty
        if dict['identifier'][0] == "" and dict['identifier'][1] == "":
            isMatch = False
        # origin match (1st bit)
        if dict['identifier'][0] != "":
            if not re.search(dict['identifier'][0], word['pie_formation2']):
                isMatch = False
        # actual lemma match (2nd bit)
        if dict['identifier'][1] != "":
            if not re.search(dict['identifier'][1], word['lemma']):
                isMatch = False
        # add if qualifying
        if isMatch:
            lst.append(entry)
    return lst

def create_etymo_text(word, mode):
    if word['pie_formation2'] != word['pie_formation']:
        string = "From Pre-%s _%s_, from %s _%s_" % (dt_general['stages'][0]['abbreviation'], apie_to_pie(word['pie_formation2']), dt_general['stages'][0]['originabbreviation'], apie_to_pie(word['pie_formation']))
    else:
        string = "From %s _%s_" % (dt_general['stages'][0]['originabbreviation'], apie_to_pie(word['pie_formation2']))
    if len(word['pie_formation_meaning']) > 0:
        if word['pie_formation_meaning'] == word['meaning']:
            string += " (id.)"
        else:
            string += " (%s)" % ", ".join(word['pie_formation_meaning'])
    if 'pie_root' in word:
        string += ", from _%s_ (%s)" % (apie_to_pie(word['pie_root']), ", ".join(dt_roots[word['pie_root']][word['pie_root_index']]))
    string += "."
    if 'etymoprose' in word:
        string += " " + word['etymoprose']
    # format accordingly
    if mode == "latex":
        return format_text_latex(string)
    return string

def format_text_preview(string, multiliner):
    wd_window[multiliner].update("")
    string = string.replace("<<", "⟨")
    string = string.replace(">>", "⟩")
    # first look for bits with regex and whenever something special may happen, add a weird character
    string = re.sub("(::[^:]*::)", "∎\\1∎", string) # bold
    string = re.sub("(_[^_]*_)", "∎\\1∎", string) # italic
    string = re.sub("(§[^§]*§)", "∎\\1∎", string) # source
    string = re.sub("([^\s\.!;,\?]*@[^\s\.!,;\?]*:?)", "∎\\1∎", string) # links/references
    # split string
    array = string.split("∎")
    for x in array:
        method = ""
        if x.startswith("::") and x.endswith("::"):
            # bold
            x = re.sub("^::", "", x)
            x = re.sub("::$", "", x)
            method = " bold"
        if x.startswith("_") and x.endswith("_"):
            # italic
            x = re.sub("^_", "", x)
            x = re.sub("_$", "", x)
            method = " italic"
        if x.startswith("§") and x.endswith("§"):
            # source
            x = x.replace("§", "")
            if x in list(source_dict.keys()):
                x = dt_sources['sources'][source_dict[x]]['reference'] + "[" + dt_sources['sources'][source_dict[x]]['title'] + "]"
            else:
                x = "INVALID-SOURCE-" + x
        if "@" in x:
            # reference
            method = " italic underline"
            arz = x.split("@")
            if arz[0] in list(get_list_of_reference_languages().keys()):
                offs = 0
                if len(arz) == 1:
                    x = "INVALID-REFERENCE-" + arz[0]
                else:
                    if arz[1] != "":
                        wd_window[multiliner].print(get_list_of_reference_languages()[arz[0]]['name'], end=' ', font=("Arial 10"))
                    else:
                        offs = 1
                    if len(arz) > (2 + offs):
                        # has alternate notation
                        offs += 1
                    x = arz[offs + 1]
                    if "=" in x:
                        # ignore romanisation for now
                        x = x.split("=")[0]
                    # extra formatting depending on the source language
                    if 'proto' in get_list_of_reference_languages()[arz[0]]:
                        x = "*" + x
                    if 'romanisation' in get_list_of_reference_languages()[arz[0]]:
                        method = " underline"
            else:
                x = "INVALID-REFERENCE " + arz[0]
        # do the printing
        wd_window[multiliner].print(x, end='', font=("Arial 10" + method))

def format_text_latex(string):
    string += "\n "
    string = string.replace(" - ", " — ")
    # references
    for x in re.findall("[^\s\.!;,\?]*@[^\s\.!,;\?]*:?", string):
        out = ""
        arz = x.split("@")
        if arz[0] in list(get_list_of_reference_languages().keys()):
            offs = 0
            if len(arz) == 1:
                x = "INVALID-REFERENCE-" + arz[0]
            else:
                if arz[1] != "":
                    out = get_list_of_reference_languages()[arz[0]]['name']
                else:
                    offs = 1
                if len(arz) > (2 + offs):
                    # has alternate notation
                    offs += 1
                out2 = arz[offs + 1]
                if "=" in out2:
                    # ignore romanisation for now
                    out2 = out2.split("=")[0]
                out2 = format_text_latex(out2)
                # extra formatting depending on the source language
                if 'proto' in get_list_of_reference_languages()[arz[0]]:
                    out2 = "*" + out2
                if not 'romanisation' in get_list_of_reference_languages()[arz[0]]:
                    out2 = "_" + out2 + "_"
                out += " " + out2
        else:
            out = "INVALID-REFERENCE " + arz[0]
        string = string.replace(x, out)
    # check for sources
    for x in re.findall("§[^§]*§", string):
        out = x.replace("§", "")
        if out in list(source_dict.keys()):
            out = dt_sources['sources'][source_dict[out]]['reference']
        else:
            out = "INVALID-SOURCE-" + out
        string = string.replace(x, out)
    # generic
    string = re.sub("::([^\:]*)::", "∎textbf{\\1}", string) # bold
    string = re.sub("_([^_]*)_", "∎textit{\\1}", string) # italic
    string = re.sub("(\n- [\s\S]*?)(\n[^-])", "\n∎begin{itemize}\\1\n∎end{itemize}\\2", string) # list p1
    string = re.sub("-( [\s\S]*?)\n", "∎item \\1∎∎\n", string) # list p2
    string = re.sub("([^\n])∎item", "\\1", string) # fix overzealous itemisation
    # special latex sorcery
    string = string.strip()
    string = re.sub("(\n[^∎])", "∎∎\\1", string)
    string = re.sub("(itemize})∎∎", "\\1", string)
    string = string.replace("~", "$∎sim$")
    string = string.replace("∎", "\\")
    return string

def getTextFormattingRightClickMenu(key):
    return ['&Right', ['Font', ['Bold::' + key, 'Italic::' + key], 'Source', [x['title'] + " [" + x['reference'] + ']::SOURCE_SELECT@' + x['internalreference'] + "@" + key for x in sorted(dt_sources['sources'], key = lambda x: (x['title'][0], x['lastname']))]]]

def get_word_class_info(entry,stage):
    if 'declension' in entry:
        return ["noun", dt_declensions['decl'][stage][entry['declension']]['abbreviation'], dt_declensions['decl'][stage][entry['declension']]['gender'].lower()]
    return ["UNDEFINED"]

def get_example_difference(a, b):
    s = difflib.SequenceMatcher(None, a, b)
    pat1 = []
    pat2 = []
    for block in s.get_matching_blocks():
        if block[2] != 0:
            pat1.append([block[0], block[0] + block[2]])
            pat2.append([block[1], block[1] + block[2]])
    res = ""
    res2 = ""
    # pat & res 1
    index = 0
    while len(pat1) > 0:
        while index < pat1[0][0]:
            res += a[index]
            index += 1
        res += "|" + a[pat1[0][0]:pat1[0][1]] + "|"
        index = pat1[0][1]
        pat1.pop(0)
    while index < len(a):
        res += a[index]
        index += 1
    # res = res.replace("||", "|_|")
    res = ("|" + res + "|").replace("||", "").replace("|", "::")
    # pat & res 2
    index = 0
    while len(pat2) > 0:
        while index < pat2[0][0]:
            res2 += b[index]
            index += 1
        res2 += "|" + b[pat2[0][0]:pat2[0][1]] + "|"
        index = pat2[0][1]
        pat2.pop(0)
    while index < len(b):
        res2 += b[index]
        index += 1
    # res2 = res2.replace("||", "|_|")
    res2 = ("|" + res2 + "|").replace("||", "").replace("|", "::")
    return [res, res2]

def render_latex(stage):
    # disable button
    wd_window['-RENDER-LATEX-BUTTON-'].update(disabled=True)
    # prepare latex data
    # TO DO: fix sorting
    lt_dictionary = []
    for entry in dt_vocab['vcb'][stage]:
        loc_orth = entry['ortho'][0]
        if len(entry['ortho']) > 1:
            loc_orth += " (%s)" % entry['ortho'][1]
        wclassinfo = get_word_class_info(entry, stage)
        lt_dictionary.append({"spelling": loc_orth, "meaning": ", ".join(entry['meaning']), "etymo": create_etymo_text(entry, "latex"), "ipa": get_pronunciation(entry['lemma'],dt_general['stages'][stage]['pronunciation']), "wordclass": wclassinfo[0]})
    lt_dictionary = sorted(lt_dictionary, key = lambda x: x['spelling'].lower())

    lt_soundchanges = []
    i = -1
    for x in dt_sound_changes['sc'][stage]:
        i = i + 1
        out = x.copy()
        out['prose'] = format_text_latex(out['prose'])
        if 'newchapter' in out:
            out['newchapter'] = format_text_latex(out['newchapter'])
        if 'prose_after' in out:
            out['prose_after'] = format_text_latex(out['prose_after'])
        out['changes'] = [(re.sub("([_#&])", "∎\\1", y['display'])).replace("∎", "\\") for y in out['changes']]
        ewt = []
        for j in enumerate(x['changes']):
            ewt.append([])
        for j, vcb in enumerate(dt_vocab['vcb'][stage]):
            for q in vcb['applied_changes']:
                if q[0] == i:
                    exdiff = get_example_difference(apie_to_pie(q[2]), apie_to_pie(q[3]))
                    ewt[q[1]].append([apie_to_pie(vcb['pie_formation']), apie_to_pie(vcb['pie_formation2']) if not vcb['pie_formation2'] == vcb['pie_formation'] else '', format_text_latex(exdiff[0]), format_text_latex(exdiff[1]), vcb['lemma'], apie_to_pie(q[2])])
        out['examples'] = []
        for j in ewt:
            if j != []:
                arr = random.choice(j)
                if arr[1] != "":
                    # Depart from pre-lang
                    st = "\\textsc{pre-" + dt_general['stages'][stage]['abbreviation'] + "} & " + arr[1]
                    ref = 1
                else:
                    # Depart from PIE
                    st = "\\textsc{" + dt_general['stages'][stage]['originabbreviation'] + "} & " + arr[0]
                    ref = 0
                if arr[5] != arr[ref]:
                    # add intermediate step
                    st += " & → & " + arr[2]
                else:
                    # skip intermediate step
                    st += " & = & " + arr[2]
                st += " & → & " + arr[3] + " & → & \\textsc{" + dt_general['stages'][stage]['abbreviation'] + "} & " + arr[4]
                out['examples'].append(st)
        if out['examples'] == []:
            del out['examples']
        lt_soundchanges.append(out)

    # prepare
    latex_folder = "%s/build/latex" % os.getcwd()
    dependencies = ["abbreviations.tex", "baabbrevs.sty", "baarux-0.9.9.sty", "cover.tex"]

    # clean up previous build
    if os.path.exists(latex_folder):
        shutil.rmtree(latex_folder)
    os.mkdir(latex_folder)

    # copy dependencies
    for x in dependencies:
        shutil.copyfile("%s/system_files/%s" % (os.getcwd(), x), "%s/%s" % (latex_folder, x))

    template = latex_jinja_env.get_template('template.tex')
    tex_name = "%s/%s.tex" % (latex_folder, get_list_of_stages()[stage].lower())
    with open(tex_name, "w", encoding='utf8') as f:
        f.write(template.render(lt_dictionary = lt_dictionary, lt_soundchanges = lt_soundchanges))

    LC.compile_document(tex_engine = 'xelatex',
                    bib_engine = 'biber', # Value is not necessary
                    no_bib = True, path = tex_name, # Provide the full path to the file!
                    folder_name = '.aux_files')

    # print log
    with open('.aux_files/%s.log' % get_list_of_stages()[stage].lower(), encoding='utf8') as f:
        auxlogs = f.readlines()
    wd_window['-RENDER-LOGS-'].print("".join(auxlogs))

    # ask if open
    filepath = '%s.pdf' % get_list_of_stages()[stage].lower()
    if sg.popup_ok_cancel("LaTeX render successful! Do you want to open the PDF with your default application?", title="Project π", keep_on_top=True) == "OK":
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filepath))

    # get back on track
    os.chdir(os.path.join(os.getcwd(), os.pardir))
    os.chdir(os.path.join(os.getcwd(), os.pardir))

    # remove dependencies
    if not debug:
        dependencies.append("%s.tex" % get_list_of_stages()[stage].lower())
    for x in dependencies:
        if not '.sty' in x:
            os.remove("%s/%s" % (latex_folder, x))

    # unlock buttons again
    wd_window['-RENDER-LATEX-BUTTON-'].update(disabled=False)

def gatherPhonologicalInventory(stage):
    inv = []
    for entry in dt_vocab['vcb'][stage]:
        out = ""
        for n in [*entry['lemma']]:
            if n in ["̄"]:
                out += n                
            elif not n in ["-", "="]:
                if out != "" and not out in inv:
                    inv.append(out)
                out = n
    if not out in inv:
        inv.append(out)
    return inv

### LEXICON

def loadDetailsOfLexiconEntry(wid, stage, dict):
    wd_window['-LEXICON4-COLUMN-'].update(visible=True)
    wd_window['-LEXICON2-INTERNAL-NAME-'].update("Internal: %s\nOrthography: %s" % (dt_vocab['vcb'][stage][wid]['lemma'], ", ".join(dt_vocab['vcb'][stage][wid]['ortho'])))
    wd_window['-LEXICON2-MEANING-'].update("\n".join(dt_vocab['vcb'][stage][wid]['meaning']))
    wd_window['-LEXICON-FORMATION1-'].update(dt_vocab['vcb'][stage][wid]['pie_formation'])
    wd_window['-LEXICON2-FORMATION-MEANING-'].update("\n".join(dt_vocab['vcb'][stage][wid]['pie_formation_meaning']))
    if dt_vocab['vcb'][stage][wid]['pie_formation'] != dt_vocab['vcb'][stage][wid]['pie_formation2']:
        wd_window['-LEXICON-FORMATION2-'].update(dt_vocab['vcb'][stage][wid]['pie_formation2'], disabled=False)
        wd_window['-LEXICON-TOGGLE-POSTPIE-'].update(value = True)
    else:
        wd_window['-LEXICON-FORMATION2-'].update("", disabled=True)
        wd_window['-LEXICON-TOGGLE-POSTPIE-'].update(value = False)
    if 'pie_root' in dt_vocab['vcb'][stage][wid]:
        wd_window['-LEXICON-ROOT-SELECT-'].update(value=apie_to_pie(dt_vocab['vcb'][stage][wid]['pie_root']))
        lst = [",".join(x) for x in dt_roots[dt_vocab['vcb'][stage][wid]['pie_root']]]
        wd_window['-LEXICON-ROOT-MEANING-SELECT-'].update(visible=True, values=lst, value=lst[dt_vocab['vcb'][stage][wid]['pie_root_index']])
    else:
        wd_window['-LEXICON-ROOT-SELECT-'].update(value="N/A")
        wd_window['-LEXICON-ROOT-MEANING-SELECT-'].update(visible=False)
    # sporadic changes
    for x in sporadic_checkboxes:
        if dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic'] in dt_vocab['vcb'][stage][wid]['sporadics']:
            wd_window[x].update(value=dt_vocab['vcb'][stage][wid]['sporadics'][dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic']], disabled=False)
        else:
            wd_window[x].update(value=False, disabled=True)
    wd_window['-LEXICON-CAPITALISE-TOGGLE-'].update(dt_vocab['vcb'][stage][wid]['capitalise'])
    # extra info
    if 'etymoprose' in dt_vocab['vcb'][stage][wid]:
        wd_window['-LEXICON-ETYMO-PROSE-'].update(dt_vocab['vcb'][stage][wid]['etymoprose'])
        format_text_preview(dt_vocab['vcb'][stage][wid]['etymoprose'], '-LEXICON-ETYMO-PROSE-FORMATTED-')
    else:
        wd_window['-LEXICON-ETYMO-PROSE-'].update("")
        wd_window['-LEXICON-ETYMO-PROSE-FORMATTED-'].update("")
    # morphology stuff
    getCompatibleInflectionCombo(dt_vocab['vcb'][stage][wid], stage, dict)
    # load current morphology data
    if 'declension' in dt_vocab['vcb'][stage][wid]:
        wd_window['-LEXICON-CATEGORY-COMBO-'].update("Noun")
        wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(dt_vocab['vcb'][stage][wid]['declension'], values=get_compatible_declensions(dt_vocab['vcb'][stage][wid], dt_declensions['decl'][stage]), visible=True)
        updateLexiconNounTable(dt_vocab['vcb'][stage][wid]['declension'])
        for x in dt_general['stages'][stage_select]['noun_numbers']:
            if 'missingnums' in dt_vocab['vcb'][stage][wid]:
                if x in dt_vocab['vcb'][stage][wid]['missingnums']:
                    wd_window['-LEXICON-NOUN-NUMBER-%s-' % x].update(value = False)
                else:
                    wd_window['-LEXICON-NOUN-NUMBER-%s-' % x].update(value = True)
            else:
                wd_window['-LEXICON-NOUN-NUMBER-%s-' % x].update(value = True)
        return
    wd_window['-LEXICON-CATEGORY-COMBO-'].update("UNDEFINED!")
    wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(visible=False)

def getCompatibleInflectionCombo(word, stage, dict):
    lst = ["UNDEFINED!"]
    newvl = dict['-LEXICON-CATEGORY-COMBO-']
    if len(get_compatible_declensions(word, dt_declensions['decl'][stage])) > 0:
        lst.append("Noun")
    wd_window['-LEXICON-CATEGORY-COMBO-'].update(newvl, values=lst)
    if newvl not in lst:
        wd_window['-LEXICON-CATEGORY-COMBO-'].update(lst[0])
        return True
    return False

def reevaluateLexiconInflection(dict, cancel):
    if dict['-LEXICON-CATEGORY-COMBO-'] == "UNDEFINED!" or cancel:
        wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(visible=False)
        return
    wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(visible=True)
    # get word dict
    word_dict = {"lemma": ""}
    newvalues = []
    if dict['-LEXICON-TOGGLE-POSTPIE-']:
        word_dict['pie_formation2'] = dict['-LEXICON-FORMATION2-']
    else:
        word_dict['pie_formation2'] = dict['-LEXICON-FORMATION1-']
    # parse
    if dict['-LEXICON-CATEGORY-COMBO-'] == "Noun":
        newvalues = get_compatible_declensions(word_dict, dt_declensions['decl'][stage_select])
    print(newvalues)
    # apply
    wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(values=newvalues)
    if dict['-LEXICON-CATEGORY-SUB-COMBO-'] not in newvalues:
        wd_window['-LEXICON-CATEGORY-SUB-COMBO-'].update(newvalues[0])

def saveLexiconEntry(wid,stage,dict):
    # capitalise
    dt_vocab['vcb'][stage][wid]['capitalise'] = dict['-LEXICON-CAPITALISE-TOGGLE-']
    # meaning of lemma
    lst = dict['-LEXICON2-MEANING-'].split("\n")
    while("" in lst):
        lst.remove("")
    for x in lst:
        x = x.strip()
    dt_vocab['vcb'][stage][wid]['meaning'] = lst
    # PIE root & meaning
    if dict['-LEXICON-ROOT-SELECT-'].lower() != "n/a":
        dt_vocab['vcb'][stage][wid]['pie_root'] = pie_to_apie(dict['-LEXICON-ROOT-SELECT-'])
        dt_vocab['vcb'][stage][wid]['pie_root_index'] = wd_window['-LEXICON-ROOT-MEANING-SELECT-'].widget.current()
    else:
        if 'pie_root' in dt_vocab['vcb'][stage][wid]:
            del dt_vocab['vcb'][stage][wid]['pie_root']
        if 'pie_root_index' in dt_vocab['vcb'][stage][wid]:
            del dt_vocab['vcb'][stage][wid]['pie_root_index']
    # formation2
    if dict['-LEXICON-TOGGLE-POSTPIE-']:
        dt_vocab['vcb'][stage][wid]['pie_formation2'] = dict['-LEXICON-FORMATION2-']
    else:
        dt_vocab['vcb'][stage][wid]['pie_formation2'] = dict['-LEXICON-FORMATION1-']
    # formation 1
    dt_vocab['vcb'][stage][wid]['pie_formation'] = dict['-LEXICON-FORMATION1-']
    # formation meaning
    lst = dict['-LEXICON2-FORMATION-MEANING-'].split("\n")
    while("" in lst):
        lst.remove("")
    for x in lst:
        x = x.strip()
    dt_vocab['vcb'][stage][wid]['pie_formation_meaning'] = lst
    # sporadic changes
    spl = {}
    for x in sporadic_checkboxes:
        if wd_window[x].Widget['state'] != "disabled":
            spl[dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic']] = dict[x]
    dt_vocab['vcb'][stage][wid]['sporadics'] = spl
    # etymoprose
    if dict['-LEXICON-ETYMO-PROSE-'].strip() != "":
        dt_vocab['vcb'][stage][wid]['etymoprose'] = dict['-LEXICON-ETYMO-PROSE-'].strip()
    else:
        if 'etymoprose' in dt_vocab['vcb'][stage][wid]:
            del dt_vocab['vcb'][stage][wid]['etymoprose']
    # inflection information: clean up first
    if 'declension' in dt_vocab['vcb'][stage][wid]:
        del dt_vocab['vcb'][stage][wid]['declension']
    # set according to stuff
    if dict['-LEXICON-CATEGORY-COMBO-'] == "Noun":
        dt_vocab['vcb'][stage][wid]['declension'] = dict['-LEXICON-CATEGORY-SUB-COMBO-']
        missingnums = []
        for x in dt_general['stages'][stage_select]['noun_numbers']:
            if dict['-LEXICON-NOUN-NUMBER-%s-' % x] == False:
                missingnums.append(x)
        if missingnums != []:
            dt_vocab['vcb'][stage][wid]['missingnums'] = missingnums
        elif 'missingnums' in dt_vocab['vcb'][stage][wid]:
            del dt_vocab['vcb'][stage][wid]['missingnums']
    # update lemma & ortho field based on previous changes
    dt_vocab['vcb'][stage][wid]['lemma'] = apply_sc(dt_vocab['vcb'][stage][wid]['pie_formation2'], dt_sound_changes['sc'][stage], dt_vocab['vcb'][stage][wid]['sporadics'])[0]
    dt_vocab['vcb'][stage][wid]['ortho'] = apply_orthography(dt_vocab['vcb'][stage][wid]['lemma'], dt_general['stages'][stage]['orthography'], dict['-LEXICON-CAPITALISE-TOGGLE-'])
    # adapt listbar in case lemma changed
    wd_window['-LEMMA-SELECTION-LIST-'].update([i['lemma'] for i in dt_vocab['vcb'][stage_select]], set_to_index=wd_window['-LEMMA-SELECTION-LIST-'].GetIndexes()[0])
    # save to json
    save_json(dt_vocab, "%s/vocab.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    wd_window.un_hide()
    # reload
    loadDetailsOfLexiconEntry(wid, stage, dict)

def deleteLexiconEntry(wid,stage):
    wd_window.hide()
    if sg.popup_ok_cancel("Are you sure you want to delete the lemma %s? This can not be undone!" % dt_vocab['vcb'][stage_select][wid]['lemma'], title="Project π", keep_on_top=True) == "OK":
        del dt_vocab['vcb'][stage][wid]
        wd_window['-LEXICON4-COLUMN-'].update(visible=False)
        wd_window['-LEMMA-SELECTION-LIST-'].update(values=[i['lemma'] for i in dt_vocab['vcb'][stage_select]])
        wd_window['-LEXICON-LEMMAS-FOUND-'].update("%s lemmas found." % len(dt_vocab['vcb'][stage_select]))
        # save json
        save_json(dt_vocab, "%s/vocab.json" % project_name)
        # notify user
        sg.popup("Entry removed.", title="Project π", keep_on_top=True)
        global lexicon_open_entry
        lexicon_open_entry = 0
    wd_window.un_hide()

def addNewLexiconLemma(dict):
    dt_vocab['vcb'][stage_select].append({"lemma": apply_sc("lorem", dt_sound_changes['sc'][stage_select], {})[0], "meaning": ["ipsum"], "pie_formation": "lorem", "pie_formation2": "lorem", "pie_formation_meaning": ["ipsum"], "sporadics": [], "ortho": apply_orthography("lemma", dt_general['stages'][stage_select]['orthography'], False), "capitalise": False})
    wd_window['-LEXICON4-COLUMN-'].update(visible=False)
    wd_window['-LEMMA-SELECTION-LIST-'].update(values=[i['lemma'] for i in dt_vocab['vcb'][stage_select]], set_to_index=len(dt_vocab['vcb'][stage_select]) - 1, scroll_to_index=len(dt_vocab['vcb'][stage_select]) - 1)
    wd_window['-LEXICON-LEMMAS-FOUND-'].update("%s lemmas found." % len(dt_vocab['vcb'][stage_select]))
    # save json
    save_json(dt_vocab, "%s/vocab.json" % project_name)
    # reload
    global lexicon_open_entry
    lexicon_open_entry = len(dt_vocab['vcb'][stage_select]) - 1
    loadDetailsOfLexiconEntry(lexicon_open_entry, stage_select, dict)

def getSelectablePIERoots():
    lst = list(dt_roots.keys())
    lst.sort()
    lst = [apie_to_pie(x) for x in lst]
    lst = ["N/A"] + lst
    return lst

def updateLexiconPIERootMeanings(value):
    if value.lower() != "n/a":
        lst = [",".join(x) for x in dt_roots[pie_to_apie(value)]]
        wd_window['-LEXICON-ROOT-MEANING-SELECT-'].update(visible=True, values=lst, value=lst[0])
    else:
        wd_window['-LEXICON-ROOT-MEANING-SELECT-'].update(visible=False)

def updatePreviewFromFormation(word, stage, dict):
    word = pie_to_apie(word).strip()
    # get sporadics from boxes

    word2, sporadic_list, prop = apply_sc(word, dt_sound_changes['sc'][stage], {})

    # again with reapplied sporadic checks if relevant
    spl = {}
    for x in sporadic_checkboxes:
        if dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic'] in sporadic_list:
            spl[dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic']] = dict[x]

    if not spl == {}:
        word2, sporadic_list, prop = apply_sc(word, dt_sound_changes['sc'][stage], spl)

    # update sporadic checkboxes
    for x in sporadic_checkboxes:
        if dt_sound_changes['sc'][stage][wd_window[x].metadata]['sporadic'] in sporadic_list:
            wd_window[x].update(disabled=False)
        else:
            wd_window[x].update(disabled=True)

    word_dict = {"lemma": word2}
    if dict['-LEXICON-TOGGLE-POSTPIE-']:
        word_dict['pie_formation2'] = dict['-LEXICON-FORMATION2-']
    else:
        word_dict['pie_formation2'] = dict['-LEXICON-FORMATION1-']

    reevaluateLexiconInflection(dict, getCompatibleInflectionCombo(word_dict, stage, dict))

    orthos = apply_orthography(word2, dt_general['stages'][stage]['orthography'], dict['-LEXICON-CAPITALISE-TOGGLE-'])
    wd_window['-LEXICON2-INTERNAL-NAME-'].update("Internal: %s\nOrthography: %s" % (word2, ", ".join(orthos)))
    return word

def updatePreviewFromFormationNoReturn(values):
    if values['-LEXICON-TOGGLE-POSTPIE-']:
        updatePreviewFromFormation(values['-LEXICON-FORMATION2-'], stage_select, values)
    else:
        updatePreviewFromFormation(values['-LEXICON-FORMATION1-'], stage_select, values)

def toggleLexiconPostPIEField(value, stage):
    if value['-LEXICON-TOGGLE-POSTPIE-']:
        wd_window['-LEXICON-FORMATION2-'].update(value['-LEXICON-FORMATION1-'], disabled=False)
    else:
        wd_window['-LEXICON-FORMATION2-'].update("", disabled=True)
        updatePreviewFromFormation(value['-LEXICON-FORMATION1-'], stage, value)

def updateLexiconNounTable(decltype):
    lst_pie=[]
    lst_expected=[]
    lst_literal=[]
    for i, x in enumerate(dt_general['stages'][stage_select]['cases']):
        lst2_pie = [x]
        lst2_expected = [x]
        lst2_literal = [x]
        for j, prop in enumerate(dt_general['stages'][stage_select]['noun_numbers']):
            go = True
            if 'missingnums' in dt_vocab['vcb'][stage_select][lexicon_open_entry] and prop in dt_vocab['vcb'][stage_select][lexicon_open_entry]['missingnums']:
                go = False
            if go:
                lst2_pie.append(collateStemEnding(dt_vocab['vcb'][stage_select][lexicon_open_entry]['pie_formation2'], dt_declensions['decl'][stage_select][decltype]['identifier'][0], dt_declensions['decl'][stage_select][decltype]['input'][i][j]))
                lst2_expected.append(apply_sc(collateStemEnding(dt_vocab['vcb'][stage_select][lexicon_open_entry]['pie_formation2'], dt_declensions['decl'][stage_select][decltype]['identifier'][0], dt_declensions['decl'][stage_select][decltype]['input'][i][j]), dt_sound_changes['sc'][stage_select], {})[0])
                lst2_literal.append(collateStemEnding(dt_vocab['vcb'][stage_select][lexicon_open_entry]['lemma'], dt_declensions['decl'][stage_select][decltype]['identifier'][1], dt_declensions['decl'][stage_select][decltype]['output'][i][j]))
            else:
                lst2_pie.append("N/A")
                lst2_expected.append("N/A")
                lst2_literal.append("N/A")
        lst_pie.append(lst2_pie)
        lst_expected.append(lst2_expected)
        lst_literal.append(lst2_literal)
    
    if lst_expected == lst_literal:
        print("It works!")
    wd_window['-LEXICON-NOUN-TABLE-'].update(values=lst_pie)
    wd_window['-LEXICON-NOUN-TABLE2-'].update(values=lst_expected)
    wd_window['-LEXICON-NOUN-TABLE3-'].update(values=lst_literal)

def collateStemEnding(stem, stemrule, ending):
    try:
        re.sub("{0\}", re.sub(stemrule, "\\1", stem), ending)
    except:
        return "ERROR"
    return re.sub("{0\}", re.sub(stemrule, "\\1", stem), ending)

# main data

def saveMainData(dict):
    dt_general['stages'][stage_select]['name'] = dict['-GENERAL-STAGE-NAME-'].strip()
    dt_general['stages'][stage_select]['abbreviation'] = dict['-GENERAL-STAGE-ABBREVIATION-'].strip()
    dt_general['stages'][stage_select]['origin'] = dict['-GENERAL-ORIGIN-NAME-'].strip()
    dt_general['stages'][stage_select]['originabbreviation'] = dict['-GENERAL-ORIGIN-ABBREVIATION-'].strip()
    # save json
    save_json(dt_general, "%s/general.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    global refresh_window
    refresh_window = True

def updateRegexPlayground(dict):
    inp = dict['-REGEX-PLAYGROUND-INPUT-']
    r1 = dict['-REGEX-PLAYGROUND-REG1-']
    r2 = dict['-REGEX-PLAYGROUND-REG2-']
    try:
        out = re.sub(r1, r2, inp)
    except:
        out = "Error: invalid regex!"
    else:
        out = re.sub(r1, r2, inp)
    wd_window['-REGEX-PLAYGROUND-OUTPUT-'].update(out)

# ORTHO, PRONUNCIATION AND ALLOPHONY FUNCTIONS
def updateOrthoPronAllophonyTryout(dict, target):
    out = dict['-%s-INPUT-TRYOUT-' % target]
    # grab all regexes
    for x in dict:
        if str(x).startswith("-%s-INPUT-REG1-" % target):
            r1 = dict[x]
            r2 = dict[x.replace("REG1", "REG2")]
            try:
                out = re.sub(r1, r2, out)
            except:
                out = "Regex error in %s > %s" % (r1, r2)
                break
            else:
                out = re.sub(r1, r2, out)
    wd_window['-%s-OUTPUT-' % target].update(out)

def clearOrthographyPronAllophony(dict, target):
    for x in dict:
        if str(x).startswith("-%s-INPUT-REG1-" % target):
            wd_window[x].update("")
            wd_window[x.replace("REG1", "REG2")].update("")

def saveOrthography(dict):
    # make sure all regexes are valid first
    stuffhaschanged = False
    testfailed = ""
    out = ""
    arrayout = []
    for x in dict:
        if str(x).startswith("-ORTHOGRAPHY-INPUT-REG1-"):
            r1 = dict[x]
            r2 = dict[x.replace("REG1", "REG2")]
            try:
                out = re.sub(r1, r2, out)
            except:
                testfailed = "%s > %s" % (r1, r2)
                break
            else:
                if r1!="" and r2!="":
                    arrayout.append([r1, r2])
                    #clean up empty rows
    if testfailed != "":
        wd_window.hide()
        sg.popup("There is still an error in your regexes: %s" % testfailed, title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # loop through orthographies and reload lexicon if not same as before
    if arrayout != dt_general['stages'][stage_select]['orthography'][0]['rules']:
        stuffhaschanged = True
    # save json & hash
    dt_general['stages'][stage_select]['orthography'][0]['rules'] = arrayout
    save_json(dt_general, "%s/general.json" % project_name)
    dt_cache['orthhash'][0] = orthography_to_key(dt_general['stages'][stage_select]['orthography'])
    save_json(dt_cache, "%s/cache.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    # loop through orthographies and reload lexicon if not same as before (this time for real)
    if stuffhaschanged:
        repair_orthography(stage_select)
        # also reload the currently loaded lexicon word to reflect these changes
        loadDetailsOfLexiconEntry(lexicon_open_entry, stage_select, dict)
    wd_window.un_hide()

def savePronunciationAllophony(dict, target):
    # make sure all regexes are valid first
    testfailed = ""
    out = ""
    arrayout = []
    for x in dict:
        if str(x).startswith("-%s-INPUT-REG1-" % target):
            r1 = dict[x]
            r2 = dict[x.replace("REG1", "REG2")]
            try:
                out = re.sub(r1, r2, out)
            except:
                testfailed = "%s > %s" % (r1, r2)
                break
            else:
                if r1!="" and r2!="":
                    arrayout.append([r1, r2])
                    #clean up empty rows
    if testfailed != "":
        wd_window.hide()
        sg.popup("There is still an error in your regexes: %s" % testfailed, title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # save json
    dt_general['stages'][stage_select][target.lower()] = arrayout
    save_json(dt_general, "%s/general.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    wd_window.un_hide()

def insertOrthoRow(rowno, dict, target):
    # get amount of active rows
    i = 0
    for x in dict:
        if str(x).startswith("-%s-INPUT-REG1-" % target):
            i+= 1
    # extend layout
    wd_window.extend_layout(wd_window['-%s-COLUMN-CONTAINER-' % target],[[sg.Column([[sg.Text("In:"),sg.Input(rowno, key='-%s-INPUT-REG1-%s-' % (target, i), enable_events=True),sg.Text("Out:"),sg.Input(i, key='-%s-INPUT-REG2-%s-' % (target, i), enable_events=True),sg.Button('+', enable_events=True, key='-%s-INPUT-BUTTON-ADDROW-%s-' % (target, i), metadata = i)]])]])
    containers_to_update.append("-%s-COLUMN-CONTAINER-" % target)
    # shift values
    while i > rowno:
        wd_window['-%s-INPUT-REG1-%s-' % (target, i)].update(dict['-%s-INPUT-REG1-%s-' % (target, i - 1)])
        wd_window['-%s-INPUT-REG2-%s-' % (target, i)].update(dict['-%s-INPUT-REG2-%s-' % (target, i - 1)])
        i -= 1
    # clean up
    wd_window['-%s-INPUT-REG1-%s-' % (target, rowno + 1)].update("")
    wd_window['-%s-INPUT-REG2-%s-' % (target, rowno + 1)].update("")

def reloadOrthography(dict):
    wd_window.hide()
    if sg.popup_ok_cancel("Are you sure you want to reload your rules? This undoes any unsaved changes!", title="Project π", keep_on_top=True) == "OK":
        clearOrthographyPronAllophony(dict, "ORTHOGRAPHY")
        for i, entry in enumerate(dt_general['stages'][stage_select]['orthography'][0]['rules']):
            wd_window["-ORTHOGRAPHY-INPUT-REG1-%s-" % i].update(entry[0])
            wd_window["-ORTHOGRAPHY-INPUT-REG2-%s-" % i].update(entry[1])
    wd_window.un_hide()

def reloadPronunciationAllophony(dict, target):
    wd_window.hide()
    if sg.popup_ok_cancel("Are you sure you want to reload your rules? This undoes any unsaved changes!", title="Project π", keep_on_top=True) == "OK":
        clearOrthographyPronAllophony(dict, target)
        for i, entry in enumerate(dt_general['stages'][stage_select][target.lower()]):
            wd_window["-%s-INPUT-REG1-%s-" % (target, i)].update(entry[0])
            wd_window["-%s-INPUT-REG2-%s-" % (target, i)].update(entry[1])
    wd_window.un_hide()

# sound change editor

def loadSoundChange(soundchangeid, dict):
    wd_window['-SOUND-CHANGES-PROSE-BEFORE-'].update(dt_sound_changes['sc'][stage_select][soundchangeid]['prose'])
    format_text_preview(dt_sound_changes['sc'][stage_select][soundchangeid]['prose'], '-SOUND-CHANGES-PROSE-BEFORE-FORMATTED-')
    if 'prose_after' in dt_sound_changes['sc'][stage_select][soundchangeid]:
        wd_window['-SOUND-CHANGES-PROSE-AFTER-'].update(dt_sound_changes['sc'][stage_select][soundchangeid]['prose_after'])
        format_text_preview(dt_sound_changes['sc'][stage_select][soundchangeid]['prose_after'], '-SOUND-CHANGES-PROSE-AFTER-FORMATTED-')
    else:
        wd_window['-SOUND-CHANGES-PROSE-AFTER-'].update("")
        wd_window['-SOUND-CHANGES-PROSE-AFTER-FORMATTED-'].update("")
    if 'repeatchanges' in dt_sound_changes['sc'][stage_select][soundchangeid]:
        wd_window['-SOUND-CHANGES-REPEAT-CHANGES-'].update(True)
    else:
        wd_window['-SOUND-CHANGES-REPEAT-CHANGES-'].update(False)
    if 'donotdisplay' in dt_sound_changes['sc'][stage_select][soundchangeid]:
        wd_window['-SOUND-CHANGES-HIDE-FROM-DOCS-'].update(True)
    else:
        wd_window['-SOUND-CHANGES-HIDE-FROM-DOCS-'].update(False)
    if 'newchapter' in dt_sound_changes['sc'][stage_select][soundchangeid]:
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-TOGGLE-'].update(True)
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-'].update(dt_sound_changes['sc'][stage_select][soundchangeid]['newchapter'], disabled=False)
    else:
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-TOGGLE-'].update(False)
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-'].update("", disabled=True)
    if 'sporadic' in dt_sound_changes['sc'][stage_select][soundchangeid]:
        wd_window['-SOUND-CHANGES-MAKE-SPORADIC-'].update(True)
        wd_window['-SOUND-CHANGES-SPORADIC-NAME-'].update(dt_sound_changes['sc'][stage_select][soundchangeid]['sporadic'], disabled=False)
    else:
        wd_window['-SOUND-CHANGES-MAKE-SPORADIC-'].update(False)
        wd_window['-SOUND-CHANGES-SPORADIC-NAME-'].update("", disabled=True)
    if dict != {}:
        global sound_change_open_entry_sub
        sound_change_open_entry_sub = 0
    wd_window['-SOUND-CHANGES-CHANGE-CHOOSE-BOX-'].update(dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['display'], values=[x['display'] for x in dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes']])
    loadSoundChangeRegexes(soundchangeid, sound_change_open_entry_sub, dict)

def toggleSoundChangeNewChapter(val):
    if val:
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-'].update(disabled=False)
    else:
        wd_window['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-'].update("", disabled=True)

def toggleSoundChangeSporadic(val):
    if val:
        wd_window['-SOUND-CHANGES-SPORADIC-NAME-'].update(disabled=False)
    else:
        wd_window['-SOUND-CHANGES-SPORADIC-NAME-'].update("", disabled=True)

def saveSoundChanges(dict):
    if dict['-SOUND-CHANGES-PROSE-BEFORE-'].strip() == "":
        wd_window.hide()
        sg.popup("The Prose field needs to contain some content.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # prose blocks
    dt_sound_changes['sc'][stage_select][sound_change_open_entry]['prose'] = dict['-SOUND-CHANGES-PROSE-BEFORE-']
    if dict['-SOUND-CHANGES-PROSE-AFTER-'].strip() != "":
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['prose_after'] = dict['-SOUND-CHANGES-PROSE-AFTER-']
    else:
        if 'prose_after' in dt_sound_changes['sc'][stage_select][sound_change_open_entry]:
            del dt_sound_changes['sc'][stage_select]['prose_after']
    # repeat changes
    if dict['-SOUND-CHANGES-REPEAT-CHANGES-']:
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['repeatchanges'] = True
    else:
        if 'repeatchanges' in dt_sound_changes['sc'][stage_select][sound_change_open_entry]:
            del dt_sound_changes['sc'][stage_select][sound_change_open_entry]['repeatchanges']
    # do not display
    if dict['-SOUND-CHANGES-HIDE-FROM-DOCS-']:
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['donotdisplay'] = True
    else:
        if 'donotdisplay' in dt_sound_changes['sc'][stage_select][sound_change_open_entry]:
            del dt_sound_changes['sc'][stage_select][sound_change_open_entry]['display']
    # new chapter
    if dict['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-'].strip() != "":
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['newchapter'] = dict['-SOUND-CHANGES-START-NEW-CHAPTER-NAME-']
    else:
        if 'newchapter' in dt_sound_changes['sc'][stage_select][sound_change_open_entry]:
            del dt_sound_changes['sc'][stage_select][sound_change_open_entry]['newchapter']
    # sporadicness
    if dict['-SOUND-CHANGES-SPORADIC-NAME-'].strip() != "":
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['sporadic'] = dict['-SOUND-CHANGES-SPORADIC-NAME-']
    else:
        if 'sporadic' in dt_sound_changes['sc'][stage_select][sound_change_open_entry]:
            del dt_sound_changes['sc'][stage_select][sound_change_open_entry]['sporadic']
    # save json
    save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
    # go through sound changes and reapply them across the lexicon again
    newSporadics = False
    wd_window.hide()
    if sound_changes_to_key(dt_sound_changes['sc'][stage_select]) != dt_cache['schash'][stage_select]:
        repair_vocabulary(stage_select)
        templst = []
        for entry in dt_sound_changes['sc'][stage_select]:
            if "sporadic" in entry:
                templst.append(entry["sporadic"])
        if dt_cache['sporadics'][stage_select] != templst:
            newSporadics = True
        dt_cache['sporadics'][stage_select] = templst
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
    # popup
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    if newSporadics:
        global refresh_window
        refresh_window = True
        return
    wd_window.un_hide()
    # reload
    refreshSoundChangeCombo(dict)
    loadSoundChange(sound_change_open_entry, dict)

def deleteSoundChange():
    wd_window.hide()
    if len(dt_sound_changes['sc'][stage_select]) == 1:
        sg.popup("You need at least one sound change batch!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to delete this batch of sound changes? This can not be undone!", title="Project π", keep_on_top=True) == "OK":
        del dt_sound_changes['sc'][stage_select][sound_change_open_entry]
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Sound change batch removed.", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def moveSoundChangeUp():
    wd_window.hide()
    if sound_change_open_entry == 0:
        sg.popup("This batch is already at the top of the list!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to move this batch of sound changes one up?", title="Project π", keep_on_top=True) == "OK":
        tmp = dt_sound_changes['sc'][stage_select][sound_change_open_entry - 1]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry - 1] = dt_sound_changes['sc'][stage_select][sound_change_open_entry]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry] = tmp
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Done!", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def moveSoundChangeDown():
    wd_window.hide()
    if sound_change_open_entry == (len(dt_sound_changes['sc'][stage_select]) - 1):
        sg.popup("This batch is already at the bottom of the list!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to move this batch of sound changes one down?", title="Project π", keep_on_top=True) == "OK":
        tmp = dt_sound_changes['sc'][stage_select][sound_change_open_entry + 1]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry + 1] = dt_sound_changes['sc'][stage_select][sound_change_open_entry]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry] = tmp
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Done!", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def refreshSoundChangeCombo(dict):
    wd_window['-SOUND-CHANGES-CHOOSE-COMBO-BOX-'].update(values=[x['prose'] for x in dt_sound_changes['sc'][stage_select]])
    if dict['-SOUND-CHANGES-PROSE-BEFORE-'] in [x['prose'] for x in dt_sound_changes['sc'][stage_select]]:
        wd_window['-SOUND-CHANGES-CHOOSE-COMBO-BOX-'].update(dict['-SOUND-CHANGES-PROSE-BEFORE-'])
    else:
        wd_window['-SOUND-CHANGES-CHOOSE-COMBO-BOX-'].update([x['prose'] for x in dt_sound_changes['sc'][stage_select]][0])
        global sound_change_open_entry
        sound_change_open_entry = 0

def updateSoundChangeTryout(target, dict):
    out = pie_to_apie(dict['-SOUND-CHANGES-TRYOUT-%s-' % target])
    if target == "ALL":
        out = apply_sc(out, dt_sound_changes['sc'][stage_select], {})[0]
    else:
        out = apply_sc(out, [dt_sound_changes['sc'][stage_select][sound_change_open_entry]], {})[0]
    wd_window['-SOUND-CHANGES-TRYOUT-%s-OUTPUT-' % target].update(out)

def loadSoundChangeRegexes(batchid, subid, dict):
    wd_window['-SOUND-CHANGES-CHANGE-DISPLAY-'].update(dt_sound_changes['sc'][stage_select][batchid]['changes'][subid]['display'])
    if dict == {}:
        return
    # clean all regex lists
    for x in dict:
        if str(x).startswith("-SOUND-CHANGES-REGEX-INPUT-REG1-"):
            wd_window[x].update("")
            wd_window[x.replace("REG1", "REG2")].update("")
    # load
    for i, x in enumerate(dt_sound_changes['sc'][stage_select][batchid]['changes'][subid]['regex']):
        if '-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i in dict:
            wd_window['-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i].update(x[0])
            wd_window['-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % i].update(x[1])
        else:
            # add new fields
            wd_window.extend_layout(wd_window['-SOUND-CHANGES-REGEX-CONTAINER-'],[[sg.Column([[sg.Text("In:"),sg.Input(x[0], key='-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i, enable_events=True, size=(10,1)),sg.Text("Out:"),sg.Input(x[1], key='-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % i, enable_events=True, size=(10,1)),sg.Button('+', enable_events=True, key='-SOUND-CHANGES-REGEX-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])]])
            if '-SOUND-CHANGES-REGEX-CONTAINER' not in containers_to_update:
                containers_to_update.append("-SOUND-CHANGES-REGEX-CONTAINER-")

def insertSoundChangeRegexRow(rowno, dict):
    # get amount of active rows
    i = 0
    for x in dict:
        if str(x).startswith("-SOUND-CHANGES-REGEX-INPUT-REG1-"):
            i+= 1
    # extend layout
    wd_window.extend_layout(wd_window['-SOUND-CHANGES-REGEX-CONTAINER-'],[[sg.Column([[sg.Text("In:"),sg.Input(rowno, key='-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i, enable_events=True, size=(10,1)),sg.Text("Out:"),sg.Input(i, key='-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % i, enable_events=True, size=(10,1)),sg.Button('+', enable_events=True, key='-SOUND-CHANGES-REGEX-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])]])
    containers_to_update.append("-SOUND-CHANGES-REGEX-CONTAINER-")
    # shift values
    while i > rowno:
        wd_window['-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i].update(dict['-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % (i - 1)])
        wd_window['-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % i].update(dict['-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % (i - 1)])
        i -= 1
    # clean up
    wd_window['-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % (rowno + 1)].update("")
    wd_window['-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % (rowno + 1)].update("")

def saveSoundChangesRegex(dict):
    # make sure all regexes are valid first
    testfailed = ""
    out = ""
    arrayout = []
    repair_vocab = False
    for x in dict:
        if str(x).startswith("-SOUND-CHANGES-REGEX-INPUT-REG1-"):
            r1 = dict[x]
            r2 = dict[x.replace("REG1", "REG2")]
            try:
                out = re.sub(r1, r2, out)
            except:
                testfailed = "%s > %s" % (r1, r2)
                break
            else:
                if r1!="":
                    arrayout.append([r1, r2])
                    #clean up empty rows
    if testfailed != "":
        wd_window.hide()
        sg.popup("There is still an error in your regexes: %s" % testfailed, title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # check if anything changed
    if arrayout != dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['regex']:
        repair_vocab = True
    # save json
    dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['display'] = dict['-SOUND-CHANGES-CHANGE-DISPLAY-']
    dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['regex'] = arrayout
    save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    if repair_vocab:
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def moveSoundChangeRegexUp():
    wd_window.hide()
    if sound_change_open_entry_sub == 0:
        sg.popup("This change is already at the top of the list!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to move this sound change one up?", title="Project π", keep_on_top=True) == "OK":
        tmp = dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub - 1]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub - 1] = dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub] = tmp
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Done!", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def moveSoundChangeRegexDown():
    wd_window.hide()
    if sound_change_open_entry_sub == (len(dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes']) - 1):
        sg.popup("This change is already at the bottom of the list!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to move this sound change one down?", title="Project π", keep_on_top=True) == "OK":
        tmp = dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub + 1]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub + 1] = dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]
        dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub] = tmp
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Done!", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def deleteSoundChangeRegex():
    wd_window.hide()
    if len(dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes']) == 1:
        sg.popup("You need at least one sound change!", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if sg.popup_ok_cancel("Are you sure you want to delete this sound change? This can not be undone!", title="Project π", keep_on_top=True) == "OK":
        del dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]
        # save json
        save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
        # notify user
        sg.popup("Sound change removed.", title="Project π", keep_on_top=True)
        # go through sound changes and reapply them across the lexicon again
        repair_vocabulary(stage_select)
        dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        # refresh window
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def insertSoundChangeRegex():
    global sound_change_open_entry_sub
    sound_change_open_entry_sub += 1
    dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'].insert(sound_change_open_entry_sub,{"display": "SPE goes here", "regex": [["INPUT", "OUTPUT"]]})
    # save json
    save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
    # go through sound changes and reapply them across the lexicon again
    wd_window.hide()
    repair_vocabulary(stage_select)
    dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
    save_json(dt_cache, "%s/cache.json" % project_name)
    # refresh window
    global refresh_window
    refresh_window = True

def insertSoundChange():
    global sound_change_open_entry
    sound_change_open_entry += 1
    global sound_change_open_entry_sub
    sound_change_open_entry_sub = 0
    dt_sound_changes['sc'][stage_select].insert(sound_change_open_entry,{"prose": "Prose goes here", "changes": [{"display": "SPE goes here", "regex": [["INPUT", "OUTPUT"]]}]})
    # save json
    save_json(dt_sound_changes, "%s/sound_changes.json" % project_name)
    # go through sound changes and reapply them across the lexicon again
    wd_window.hide()
    repair_vocabulary(stage_select)
    dt_cache['schash'][stage_select] = sound_changes_to_key(dt_sound_changes['sc'][stage_select])
    save_json(dt_cache, "%s/cache.json" % project_name)
    # refresh window
    global refresh_window
    refresh_window = True

# statistics

def update_statistics():
    # time spent
    arg = int(time.time() - edit_start_time + edit_start_time_extra)
    wd_window['-STATISTICS-TIME-SPENT-'].update("%s hour(s), %s minute(s), %s second(s)" % (int(arg / 3600), int(arg / 60) % 60, arg % 60))

# roots
def loadRoot(rid):
    wd_window['-ROOTS-COLUMN-'].update(visible=True)
    lemmasassociated = 0
    for x in dt_vocab['vcb'][stage_select]:
        if 'pie_root' in x:
            if x['pie_root'] == rid:
                lemmasassociated += 1
    wd_window['-ROOTS-NAME-'].update("Entry opened: %s\nLemmas associated: %s" % (apie_to_pie(rid), lemmasassociated))
    lst = []
    for x in dt_roots[rid]:
        if lst != []:
            lst.append("")
        for y in x:
            lst.append(y)
    wd_window['-ROOTS-MEANINGS-'].update("\n".join(lst))

def deleteRoot(rid):
    wd_window.hide()
    if sg.popup_ok_cancel("Are you sure you want to delete the root %s? This can not be undone!" % apie_to_pie(rid), title="Project π", keep_on_top=True) == "OK":
        del dt_roots[rid]
        wd_window['-ROOTS-COLUMN-'].update(visible=False)
        wd_window['-ROOTS-SELECTION-LIST-'].update(values=[apie_to_pie(i) for i in list(dt_roots.keys())])
        wd_window['-ROOTS-FOUND-'].update("%s lemmas found." % len(dt_roots))
        # clean up root references in lemmas
        for x in dt_vocab['vcb'][stage_select]:
            if 'pie_root' in x:
                if x['pie_root'] == rid:
                    del x['pie_root']
                    del x['pie_root_index']
        # save json
        save_json(dt_roots, "%s/roots.json" % project_name)
        save_json(dt_vocab, "%s/vocab.json" % project_name)
        # notify user
        sg.popup("Root removed.", title="Project π", keep_on_top=True)
    wd_window.un_hide()

def saveRoot(rid, dict):
    lst = []
    lst2 = []
    for x in dict['-ROOTS-MEANINGS-'].split("\n"):
        if x.strip() == "":
            lst.append(lst2)
            lst2 = []
        else:
            lst2.append(x)
    lst.append(lst2)

    for y in lst:
        while("" in y):
            y.remove("")
        for x in y:
            x = x.strip()
    dt_roots[rid] = lst
    # save to json
    save_json(dt_roots, "%s/roots.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    wd_window.un_hide()
    # reload
    loadRoot(root_open_entry)

def newRoot():
    wd_window.hide()
    rid = sg.PopupGetText("Please enter the root.", "Project π", keep_on_top=True)
    if rid == None:
        wd_window.un_hide()
        return
    rid = rid.strip()
    if rid[-1] != "-":
        rid += "-"
    if rid == "":
        wd_window.un_hide()
        return
    if pie_to_apie(rid) in dt_roots:
        sg.popup("%s already exists!" % apie_to_pie(pie_to_apie(rid)), title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    dt_roots[pie_to_apie(rid)]=[["?"]]
    # save to json
    save_json(dt_roots, "%s/roots.json" % project_name)
    global refresh_window
    refresh_window = True
    global root_open_entry
    root_open_entry = pie_to_apie(rid)

# morphology section

def moveMorphoNounsCaseRight(dict):
    if len(dict['-MORPHO-NOUNS-CASES-UNUSED-']) == 0:
        return
    
    lst1 = wd_window['-MORPHO-NOUNS-CASES-UNUSED-'].Values
    lst2 = wd_window['-MORPHO-NOUNS-CASES-USED-'].Values
    for x in dict['-MORPHO-NOUNS-CASES-UNUSED-']:
        lst1.remove(x)
        lst2.append(x)
    wd_window['-MORPHO-NOUNS-CASES-UNUSED-'].update(values=lst1)
    wd_window['-MORPHO-NOUNS-CASES-USED-'].update(values=lst2)

def moveMorphoNounsCaseLeft(dict):
    if len(dict['-MORPHO-NOUNS-CASES-USED-']) == 0:
        return
    
    lst1 = wd_window['-MORPHO-NOUNS-CASES-UNUSED-'].Values
    lst2 = wd_window['-MORPHO-NOUNS-CASES-USED-'].Values
    for x in dict['-MORPHO-NOUNS-CASES-USED-']:
        lst2.remove(x)
        lst1.append(x)
    wd_window['-MORPHO-NOUNS-CASES-UNUSED-'].update(values=lst1)
    wd_window['-MORPHO-NOUNS-CASES-USED-'].update(values=lst2)

def reloadMorphoNounsCase():
    wd_window['-MORPHO-NOUNS-CASES-UNUSED-'].update(values=[x[0] for x in get_list_of_cases() if x[0] not in dt_general['stages'][stage_select]['cases']])
    wd_window['-MORPHO-NOUNS-CASES-USED-'].update(values=[x for x in dt_general['stages'][stage_select]['cases']])
    wd_window['-MORPHO-NOUNS-NUMBER-SG-'].update('SG' in dt_general['stages'][stage_select]['noun_numbers'])
    wd_window['-MORPHO-NOUNS-NUMBER-DU-'].update('DU' in dt_general['stages'][stage_select]['noun_numbers'])
    wd_window['-MORPHO-NOUNS-NUMBER-PL-'].update('PL' in dt_general['stages'][stage_select]['noun_numbers'])
    wd_window['-MORPHO-NOUNS-GENDER-M-'].update('M' in dt_general['stages'][stage_select]['genders'])
    wd_window['-MORPHO-NOUNS-GENDER-F-'].update('F' in dt_general['stages'][stage_select]['genders'])
    wd_window['-MORPHO-NOUNS-GENDER-N-'].update('N' in dt_general['stages'][stage_select]['genders'])

def saveMorphoNounsCase(dict):
    # do a whole bunch of checks
    if len(wd_window['-MORPHO-NOUNS-CASES-USED-'].Values) == 0:
        wd_window.hide()
        sg.popup("You need at least one case. Its name will not be shown if it is the only one.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if not dict['-MORPHO-NOUNS-NUMBER-SG-'] and not dict['-MORPHO-NOUNS-NUMBER-DU-'] and not dict['-MORPHO-NOUNS-NUMBER-PL-']:
        wd_window.hide()
        sg.popup("You need at least one number. Its name will not be shown if it is the only one.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if not dict['-MORPHO-NOUNS-GENDER-M-'] and not dict['-MORPHO-NOUNS-GENDER-F-'] and not dict['-MORPHO-NOUNS-GENDER-N-']:
        wd_window.hide()
        sg.popup("You need at least one gender. Its name will not be shown if it is the only one.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # check if you want to uncheck a gender that is still assigned to something
    gendersinuse = []
    for x in dt_declensions['decl'][stage_select]:
        x = dt_declensions['decl'][stage_select][x]
        if x['gender'] == "M" and not dict['-MORPHO-NOUNS-GENDER-M-'] and "M" not in gendersinuse:
            gendersinuse.append("M")
        if x['gender'] == "F" and not dict['-MORPHO-NOUNS-GENDER-F-'] and "F" not in gendersinuse:
            gendersinuse.append("F")
        if x['gender'] == "N" and not dict['-MORPHO-NOUNS-GENDER-N-'] and "N" not in gendersinuse:
            gendersinuse.append("N")
    if gendersinuse != []:
        wd_window.hide()
        sg.popup("The following genders are still in use: %s. Please remove them from declensions and try again." % ", ".join(gendersinuse), title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # extra warning w/ y/n prompt if you try to remove a case or number
    caseslost = []
    for x in get_list_of_cases():
        if x[0] in dt_general["stages"][stage_select]['cases'] and x[0] not in wd_window['-MORPHO-NOUNS-CASES-USED-'].Values:
            caseslost.append(x[0])
    numberlost = []
    for x in ["SG", "DU", "PL"]:
        if x in dt_general["stages"][stage_select]['noun_numbers'] and not dict['-MORPHO-NOUNS-NUMBER-%s-' % x]:
            numberlost.append(x)
    if caseslost != [] or numberlost != []:
        wd_window.hide()
        if caseslost != [] and numberlost == []:
            if not sg.popup_ok_cancel("You are about to delete the case(s) %s. This action is irreversible. Are you sure you wish to proceed?" % ", ".join(caseslost), title="Project π", keep_on_top=True) == "OK":
                wd_window.un_hide()
                return
        elif caseslost == [] and numberlost != []:
            if not sg.popup_ok_cancel("You are about to delete the number(s) %s. This action is irreversible. Are you sure you wish to proceed?" % ", ".join(numberlost), title="Project π", keep_on_top=True) == "OK":
                wd_window.un_hide()
                return
        else:
            if not sg.popup_ok_cancel("You are about to delete the case(s) %s and the number(s) %s. This action is irreversible. Are you sure you wish to proceed?" % (", ".join(caseslost), ", ".join(numberlost)), title="Project π", keep_on_top=True) == "OK":
                wd_window.un_hide()
                return
    old_cases = dt_general["stages"][stage_select]['cases']
    old_numbers = dt_general["stages"][stage_select]['noun_numbers']
    # actually save
    dt_general["stages"][stage_select]['cases'] = wd_window['-MORPHO-NOUNS-CASES-USED-'].Values
    # number
    lst = []
    if dict['-MORPHO-NOUNS-NUMBER-SG-']:
        lst.append("SG")
    if dict['-MORPHO-NOUNS-NUMBER-DU-']:
        lst.append("DU")
    if dict['-MORPHO-NOUNS-NUMBER-PL-']:
        lst.append("PL")
    dt_general["stages"][stage_select]['noun_numbers'] = lst
    # gender
    lst = []
    if dict['-MORPHO-NOUNS-GENDER-M-']:
        lst.append("M")
    if dict['-MORPHO-NOUNS-GENDER-F-']:
        lst.append("F")
    if dict['-MORPHO-NOUNS-GENDER-N-']:
        lst.append("N")
    dt_general["stages"][stage_select]['genders'] = lst
    # go through declensions in case case/number stuff changed
    if old_cases != dt_general["stages"][stage_select]['cases'] or old_numbers != dt_general["stages"][stage_select]['noun_numbers']:
        for x in dt_declensions['decl'][stage_select]:
            inplist = []
            inpref = dt_declensions['decl'][stage_select][x]['input']
            outlist = []
            outref = dt_declensions['decl'][stage_select][x]['output']
            for case in dt_general["stages"][stage_select]['cases']:
                inplst = []
                outlst = []
                for number in dt_general["stages"][stage_select]['noun_numbers']:
                    if number in old_numbers:
                        if case in old_cases:
                            inplst.append(inpref[old_cases.index(case)][old_numbers.index(number)])
                            outlst.append(outref[old_cases.index(case)][old_numbers.index(number)])
                        else:
                            inplst.append("")
                            outlst.append("")
                    else:
                        inplst.append("")
                        outlst.append("")
                inplist.append(inplst)
                outlist.append(outlst)
            dt_declensions['decl'][stage_select][x]['input'] = inplist
            dt_declensions['decl'][stage_select][x]['output'] = outlist
    # save to json
    save_json(dt_general, "%s/general.json" % project_name)
    save_json(dt_declensions, "%s/declensions.json" % project_name)
    save_json(dt_vocab, "%s/vocab.json" % project_name)
    dt_cache['declhash'][stage_select] = declension_to_key(dt_declensions['decl'][stage_select])
    save_json(dt_cache, "%s/cache.json" % project_name)
    # popup
    wd_window.hide()
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    global refresh_window
    refresh_window = True
    if len(dt_declensions['decl'][stage_select]) == 0:
        addMorphoDeclension()

def loadMorphoDeclension(index):
    wd_window['-MORPHO-NOUNS-NAME-'].update(index)
    wd_window['-MORPHO-NOUNS-ABBREVIATION-'].update(dt_declensions['decl'][stage_select][index]['abbreviation'])
    wd_window['-MORPHO-NOUNS-REGEX-ORIGINAL-'].update(dt_declensions['decl'][stage_select][index]['identifier'][0])
    wd_window['-MORPHO-NOUNS-REGEX-ACTUALWORD-'].update(dt_declensions['decl'][stage_select][index]['identifier'][1])
    wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].update(values=getNounInflectionArray(dt_declensions['decl'][stage_select][index]['input']))
    wd_window['-MORPHO-NOUNS-TABLE-OUTPUT-'].update(values=getNounInflectionArray(dt_declensions['decl'][stage_select][index]['output']))
    wd_window['-MORPHO-NOUNS-DECLENSION-GENDER-'].update(dt_declensions['decl'][stage_select][index]['gender'])
    wd_window['-MORPHO-NOUNS-REGEX-RESULTS-'].update(evaluateMorphoNounRegexes(dt_declensions['decl'][stage_select][index]['identifier'][0], dt_declensions['decl'][stage_select][index]['identifier'][1]))

def saveMorphoDeclension(dict):
    global morpho_noun_open_entry
    wd_window.hide()
    dict['-MORPHO-NOUNS-NAME-'] = dict['-MORPHO-NOUNS-NAME-'].strip()
    # check for errors
    if "CRITICAL:" in evaluateMorphoNounRegexes(dict['-MORPHO-NOUNS-REGEX-ORIGINAL-'], dict['-MORPHO-NOUNS-REGEX-ACTUALWORD-']):
        sg.popup("There is a critical regex error that needs to be resolved first.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    if dict['-MORPHO-NOUNS-NAME-'] != morpho_noun_open_entry:
        if dict['-MORPHO-NOUNS-NAME-'] in dt_declensions['decl'][stage_select]:
            sg.popup("The new name you chose for this declension already exists. Please choose another or delete the other one first.", title="Project π", keep_on_top=True)
            wd_window.un_hide()
            return
    if dict['-MORPHO-NOUNS-ABBREVIATION-'].strip() == "":
        sg.popup("A declension's abbreviation can not be empty.", title="Project π", keep_on_top=True)
        wd_window.un_hide()
        return
    # save bits
    dt_declensions['decl'][stage_select][morpho_noun_open_entry]['abbreviation'] = dict['-MORPHO-NOUNS-ABBREVIATION-'].strip()
    dt_declensions['decl'][stage_select][morpho_noun_open_entry]['identifier'][0] = dict['-MORPHO-NOUNS-REGEX-ORIGINAL-']
    dt_declensions['decl'][stage_select][morpho_noun_open_entry]['identifier'][1] = dict['-MORPHO-NOUNS-REGEX-ACTUALWORD-']
    dt_declensions['decl'][stage_select][morpho_noun_open_entry]['gender'] = dict['-MORPHO-NOUNS-DECLENSION-GENDER-']
    # rename if relevant
    if dict['-MORPHO-NOUNS-NAME-'] != morpho_noun_open_entry:
        # rename key in dt_declensions
        dt_declensions['decl'][stage_select][dict['-MORPHO-NOUNS-NAME-']] = dt_declensions['decl'][stage_select].pop(morpho_noun_open_entry)
        
        # rename key in vocab entries
        for x in dt_vocab['vcb'][stage_select]:
            if 'declension' in x:
                if x['declension'] == morpho_noun_open_entry:
                    x['declension'] = dict['-MORPHO-NOUNS-NAME-']
        # fix local variable
        morpho_noun_open_entry = dict['-MORPHO-NOUNS-NAME-']
    # save files
    save_json(dt_declensions, "%s/declensions.json" % project_name)
    save_json(dt_vocab, "%s/vocab.json" % project_name)
    dt_cache['declhash'][stage_select] = declension_to_key(dt_declensions['decl'][stage_select])
    save_json(dt_cache, "%s/cache.json" % project_name)
    sg.popup("Saved!", title="Project π", keep_on_top=True)
    global refresh_window
    refresh_window = True

def addMorphoDeclension():
    i = 1
    while ('New Declension %s' % i) in dt_declensions['decl'][stage_select]:
        i += 1
    newdict = {"abbreviation": "ND%s" % i, "gender": dt_general['stages'][stage_select]['genders'][0], "identifier": ["", ""], "overrides": []}
    lst = []
    for x in dt_general['stages'][stage_select]['cases']:
        lst2 = []
        for y in dt_general['stages'][stage_select]['noun_numbers']:
            lst2.append("")
        lst.append(lst2)
    newdict["input"] = lst
    newdict["output"] = lst
    dt_declensions['decl'][stage_select]['New Declension %s' % i] = newdict
    save_json(dt_declensions, "%s/declensions.json" % project_name)
    dt_cache['declhash'][stage_select] = declension_to_key(dt_declensions['decl'][stage_select])
    save_json(dt_cache, "%s/cache.json" % project_name)
    global morpho_noun_open_entry
    morpho_noun_open_entry = 'New Declension %s' % i
    global refresh_window
    refresh_window = True

def deleteMorphoDeclension():
    global morpho_noun_open_entry
    wd_window.hide()
    if sg.popup_ok_cancel("Are you sure you want to delete the declension %s? This can not be undone!" % morpho_noun_open_entry, title="Project π", keep_on_top=True) == "OK":
        # remove declension from nominals
        for x in dt_vocab['vcb'][stage_select]:
            if 'declension' in x:
                if x['declension'] == morpho_noun_open_entry:
                    del x['declension']
        del dt_declensions['decl'][stage_select][morpho_noun_open_entry]
        # save json
        save_json(dt_declensions, "%s/declensions.json" % project_name)
        dt_cache['declhash'][stage_select] = declension_to_key(dt_declensions['decl'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
        save_json(dt_vocab, "%s/vocab.json" % project_name)
        # notify user
        sg.popup("Declension removed.", title="Project π", keep_on_top=True)
        morpho_noun_open_entry = list(dt_declensions['decl'][stage_select].keys())[0]
        global refresh_window
        refresh_window = True
    else:
        wd_window.un_hide()

def getNounInflectionArray(arrayin):
    out = []
    for i, x in enumerate(dt_general['stages'][stage_select]['cases']):
        lst = [x]
        for j, y in enumerate(dt_general['stages'][stage_select]['noun_numbers']):
            lst.append(arrayin[i][j])
        out.append(lst)
    return out

def clickMorphoNounsInputTable():
    e = wd_window["-MORPHO-NOUNS-TABLE-INPUT-"].user_bind_event
    if wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].Widget.identify('region', e.x, e.y) != "cell":
        return
    if int(wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].Widget.identify_column(e.x)[1:]) < 2:
        return
    x = int(wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].Widget.identify_row(e.y)) - 1
    y = int(wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].Widget.identify_column(e.x)[1:]) - 2
    wd_window.hide()
    result = sg.PopupGetText("Please enter the form for the %s %s." % (get_list_of_cases()[x][1], get_number_name(dt_general['stages'][stage_select]['noun_numbers'][y])), "Project π", keep_on_top=True, default_text=dt_declensions['decl'][stage_select][morpho_noun_open_entry]['input'][x][y])
    if result != None:
        dt_declensions['decl'][stage_select][morpho_noun_open_entry]['input'][x][y] = pie_to_apie(result)
        dt_declensions['decl'][stage_select][morpho_noun_open_entry]['output'][x][y] = apply_sc(pie_to_apie(result), dt_sound_changes['sc'][stage_select], {})[0]
        wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].update(values=getNounInflectionArray(dt_declensions['decl'][stage_select][morpho_noun_open_entry]['input']))
        wd_window['-MORPHO-NOUNS-TABLE-OUTPUT-'].update(values=getNounInflectionArray(dt_declensions['decl'][stage_select][morpho_noun_open_entry]['output']))
        save_json(dt_declensions, "%s/declensions.json" % project_name)
        dt_cache['declhash'][stage_select] = declension_to_key(dt_declensions['decl'][stage_select])
        save_json(dt_cache, "%s/cache.json" % project_name)
    wd_window.un_hide()

def evaluateMorphoNounRegexes(pieregex, actualregex):
    # check legality of pie regex
    try:
        re.sub(pieregex, "", "")
    except:
        return "CRITICAL: Invalid %s regex!" % dt_general['stages'][stage_select]['originabbreviation']
    # check legality of actual regex
    try:
        re.sub(actualregex, "", "")
    except:
        return "CRITICAL: Invalid %s regex!" % dt_general['stages'][stage_select]['name']
    # check if pieregex includes output
    try:
        re.sub(pieregex, "\\1", "")
    except:
        if pieregex.strip()!="":
            return "CRITICAL: Your %s regex lacks an output group." % dt_general['stages'][stage_select]['originabbreviation']
    # check if actual regex includes output
    try:
        re.sub(actualregex, "\\1", "")
    except:
        if actualregex.strip()!="":
            return "CRITICAL: Your %s regex lacks an output group." % dt_general['stages'][stage_select]['name']
    # default
    if pieregex.strip()=="" and actualregex.strip()=="":
        return "Note: this declension can not be assigned to a lemma, but it can be forcefed a lemma in documentation."
    return ""

# other

def make_new_project():
    wd_window.hide()
    folder = sg.PopupGetText("Please enter a folder name.", "Project π", keep_on_top=True)
    if folder == "" or folder == None:
        wd_window.un_hide()
        return
    while os.path.exists("%s/projects/%s" % (os.getcwd(), folder)):
        folder = sg.PopupGetText("This folder already exists. Please enter a folder name.", "Project π", keep_on_top=True, default_text=folder)
        if folder == "" or folder == None:
            wd_window.un_hide()
            return
    # make new folder here
    os.mkdir("%s/projects/%s" % (os.getcwd(), folder))
    global project_name
    project_name = "projects/%s" % folder
    # make default files
    ### general
    tmp = {"stages": [{"name": "LOREM", "abbreviation": "IPSUM", "origin": "Proto-LOREM", "originabbreviation": "PIPSUM", "orthography": [{"name": "authentic", "rules": [["INPUT", "OUTPUT"]]}], "pronunciation": [["INPUT", "OUTPUT"]], "allophony": [["INPUT", "OUTPUT"]], "cases": [], "noun_numbers": [], "genders": []}], "general_settings": {"timespent": 0, "lastedited": "", "ppi_version": local_version}}
    save_json(tmp, "%s/general.json" % project_name)
    ### roots
    tmp = {}
    save_json(tmp, "%s/roots.json" % project_name)
    ### sound_changes
    tmp = {"sc": [[{"prose": "Prose goes here", "changes": [{"display": "SPE goes here", "regex": [["INPUT", "OUTPUT"]]}]}]]}
    save_json(tmp, "%s/sound_changes.json" % project_name)
    ### sources
    tmp = {}
    save_json(tmp, "%s/sources.json" % project_name)
    ### vocab
    tmp = {"vcb": [[]]}
    save_json(tmp, "%s/vocab.json" % project_name)
    ### declensions
    tmp = {"decl": [{}]}
    save_json(tmp, "%s/declensions.json" % project_name)
    ### cache
    tmp = {}
    save_json(tmp, "%s/cache.json" % project_name)
    wd_window.un_hide()

def update_to_do_list():
    # urgent
    lst = []
    # loop
    # safeguard
    if lst == []:
        lst = ["No urgent warnings! :)"]
    wd_window['-TO-DO-LIST-URGENT-'].update("\n".join(lst))
    # warnings
    lst = []
    # look for orphaned lemmas
    for x in dt_vocab['vcb'][stage_select]:
        if is_orphaned_lemma(x):
            lst.append("%s is not assigned to any word class." % x['lemma'])
    # safeguard
    if lst == []:
        lst = ["No warnings! :)"]
    wd_window['-TO-DO-LIST-WARNING-'].update("\n".join(lst))
    # sourcing
    wd_window['-TO-DO-LIST-SOURCING-'].update("This feature is coming soon!")

def checkTextFormatRightClick(event, values, key):
    if '::' + key in event:
        event = event.split("::")[0].lower()
        if event == "bold" or event == "italic":
            try:
                i = wd_window[key].Widget.index('sel.first')
            except:
                return
            if event == "bold":
                ins = "::"
            elif event == "italic":
                ins = "_"
            newtext = values[key][:int(wd_window[key].Widget.index('sel.first').split(".")[1])] + ins + wd_window[key].Widget.selection_get() + ins + values[key][int(wd_window[key].Widget.index('sel.last').split(".")[1]):]
            wd_window[key].update(newtext)
            format_text_preview(newtext, key + 'FORMATTED-')
    elif "::" in event and "@" + key in event:
        event = (event.split("::")[1]).split("@")[1]
        try:
            i = wd_window[key].Widget.index('insert')
        except:
            return
        i = int(wd_window[key].Widget.index('insert').split(".")[1])
        newtext = values[key][:i] + "§" + event + "§" + values[key][i:]
        wd_window[key].update(newtext)
        format_text_preview(newtext, key + 'FORMATTED-')

# main loop below
project_name = ""
chose_folder = False
brand_new_project = True
source_dict = {}
print("Initiating...")
if not parse_bibliography():
    quit()
# get current project
list_of_folders = next(os.walk("%s/projects" % application_path))[1]
wd_layout = [[sg.Text("Please choose a project to open.")],[sg.Listbox(values=list_of_folders, size=(30, 6), select_mode='LISTBOX_SELECT_MODE_SINGLE', key='-CHOOSE-PROJECT-LIST-BOX-', enable_events=True)],[sg.Button(button_text='Select', disabled=True, key='-CHOOSE-PROJECT-SELECT-BUTTON-'), sg.Button(button_text='New', key='-CHOOSE-PROJECT-NEW-BUTTON-')]]
wd_window = sg.Window('Project π', wd_layout)
while True:
    event, values = wd_window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == "-CHOOSE-PROJECT-LIST-BOX-":
        # enable select button
        wd_window['-CHOOSE-PROJECT-SELECT-BUTTON-'].update(disabled = False)
    if event == "-CHOOSE-PROJECT-SELECT-BUTTON-":
        project_name = "%s/projects/" % application_path + values["-CHOOSE-PROJECT-LIST-BOX-"][0]
        break
    if event == "-CHOOSE-PROJECT-NEW-BUTTON-":
        make_new_project()
        if project_name != "":
            brand_new_project = True
            break
wd_window.close()
if project_name == "":
    quit()

chose_folder = True

f_sound_changes = open("%s/sound_changes.json" % project_name, encoding='utf8')
f_vocab = open("%s/vocab.json" % project_name, encoding='utf8')
f_roots = open("%s/roots.json" % project_name, encoding='utf8')
f_cache = open("%s/cache.json" % project_name, encoding='utf8')
f_general = open("%s/general.json" % project_name, encoding='utf8')
f_declensions = open("%s/declensions.json" % project_name, encoding='utf8')
f_source_manager = open("%s/sources.json" % project_name, encoding='utf8')

dt_sound_changes = json.load(f_sound_changes)
dt_vocab = json.load(f_vocab)
dt_roots = json.load(f_roots)
dt_cache = json.load(f_cache)
dt_general = json.load(f_general)
dt_declensions = json.load(f_declensions)
dt_source_manager = json.load(f_source_manager)

edit_start_time = time.time()
edit_start_time_extra = dt_general['general_settings']['timespent']

# check if an update is necessary
if not 'ppi_version' in dt_general['general_settings']:
    oldversion = None
    # move stem fetchures to the lang regex
    for i, prop in enumerate(get_list_of_stages()):
        for decl in dt_declensions['decl'][i]:
            if dt_declensions['decl'][i][decl]['identifier'][1] == "":
                dt_declensions['decl'][i][decl]['identifier'][1] = dt_declensions['decl'][i][decl]['stemrules']
            del dt_declensions['decl'][i][decl]['stemrules']
        dt_cache['declhash'][i] = declension_to_key(dt_declensions['decl'][i])
    save_json(dt_declensions, "%s/declensions.json" % project_name)
    save_json(dt_cache, "%s/cache.json" % project_name)
    # update general
    dt_general['general_settings']['ppi_version'] = 1
    save_json(dt_general, "%s/general.json" % project_name)
else:
    oldversion = dt_general['general_settings']['ppi_version']

if oldversion < 2:
    # set vocab type to inherited
    for i, prop in enumerate(get_list_of_stages()):
        for lemma in dt_vocab['vcb'][i]:
            lemma['lemma_type'] = "inherited"
    save_json(dt_vocab, "%s/vocab.json" % project_name)

if oldversion != local_version:
    dt_general['general_settings']['ppi_version'] = local_version
    save_json(dt_general, "%s/general.json" % project_name)
    sg.popup("Updated your project files to a newer version!", title="Project π", keep_on_top=True)

# check cache file contents and repair as necessary
if 'schash' in dt_cache:
    schash_fail = False
    i = 0
    for val in dt_sound_changes['sc']:
        if sound_changes_to_key(val) != dt_cache['schash'][i]:
            print("WARNING: Cache not corresponding to stage %s sound changes. Repairing Vocabulary..." % i)
            schash_fail = True
            dt_cache['schash'][i] = sound_changes_to_key(val)
            templst = []
            for entry in val:
                if "sporadic" in entry:
                    templst.append(entry["sporadic"])
            dt_cache['sporadics'][i] = templst
            save_json(dt_cache, "%s/cache.json" % project_name)
        i+= 1
    if schash_fail == False:
        print("Sound Change integrity confirmed.")
    else:
        for key, value in enumerate(get_list_of_stages()):
            repair_vocabulary(key)
else:
    print("WARNING: Sound Change hashes missing from cache file.")
    lst = []
    lst2 = []
    for scarray in dt_sound_changes['sc']:
        templst = []
        for entry in scarray:
            if "sporadic" in entry:
                templst.append(entry["sporadic"])
        lst.append(sound_changes_to_key(scarray))
        lst2.append(templst)
    dt_cache['schash'] = lst
    dt_cache['sporadics'] = lst2
    save_json(dt_cache, "%s/cache.json" % project_name)
    print("WARNING: Sound Change hashes restored. Repairing Vocabulary...")
    for key, value in enumerate(get_list_of_stages()):
        repair_vocabulary(key)

if 'orthhash' in dt_cache:
    orthhash_fail = False
    i = 0
    for val in dt_general['stages']:
        if orthography_to_key(val['orthography']) != dt_cache['orthhash'][i]:
            print("WARNING: Cache not corresponding to stage %s orthography. Repairing orthography..." % i)
            orthhash_fail = True
            dt_cache['orthhash'][i] = orthography_to_key(val['orthography'])
            save_json(dt_cache, "%s/cache.json" % project_name)
        i+= 1
    if orthhash_fail == False:
        print("Orthography integrity confirmed.")
    else:
        for key, value in enumerate(get_list_of_stages()):
            repair_orthography(key)
else:
    print("WARNING: Orthography hashes missing from cache file.")
    lst = []
    for scarray in dt_general['stages']:
        lst.append(orthography_to_key(scarray['orthography']))
    dt_cache['orthhash'] = lst
    save_json(dt_cache, "%s/cache.json" % project_name)
    print("WARNING: Orthography hashes restored. Repairing orthography...")
    for key, value in enumerate(get_list_of_stages()):
        repair_orthography(key)

if 'declhash' in dt_cache:
    declhash_fail = False
    i = 0
    for bunch in dt_declensions['decl']:
        if declension_to_key(bunch) != dt_cache['declhash'][i]:
            print("WARNING: Cache not corresponding to stage %s declensions. Repairing declensions..." % i)
            declhash_fail = True
            dt_cache['declhash'][i] = declension_to_key(dt_declensions['decl'][i])
            save_json(dt_cache, "%s/cache.json" % project_name)
        i+= 1
    if declhash_fail == False:
        print("Declension integrity confirmed.")
    else:
        for key, value in enumerate(get_list_of_stages()):
            repair_declension(key)
else:
    print("WARNING: Declension hashes missing from cache file.")
    lst = []
    for bunch in dt_declensions['decl']:
        lst.append(declension_to_key(bunch))
    dt_cache['declhash'] = lst
    save_json(dt_cache, "%s/cache.json" % project_name)
    print("WARNING: Declension hashes restored. Repairing declensions...")
    for key, value in enumerate(get_list_of_stages()):
        repair_declension(key)

brand_new_project = False

stage_select = 0
lexicon_open_entry = 0
sound_change_open_entry = 0
sound_change_open_entry_sub = 0
if len(dt_declensions['decl'][stage_select]) > 0:
    morpho_noun_open_entry = list(dt_declensions['decl'][stage_select].keys())[0]
else:
    morpho_noun_open_entry = None
if len(dt_roots) > 0:
    root_open_entry = list(dt_roots.keys())[0]
else:
    root_open_entry = None
containers_to_update = []
refresh_window_to = ""

# MAIN WINDOW LOOP
while True:
    refresh_window = False
    sporadic_checkboxes = []

    # GENERAL
    general_window_main = [[sg.Text("Full name: "), sg.Input(default_text=dt_general['stages'][stage_select]['name'], key='-GENERAL-STAGE-NAME-')],[sg.Text("Abbreviation: "), sg.Input(default_text=dt_general['stages'][stage_select]['abbreviation'], key='-GENERAL-STAGE-ABBREVIATION-')],[sg.Text("Origin: "), sg.Input(default_text=dt_general['stages'][stage_select]['origin'], key='-GENERAL-ORIGIN-NAME-')],[sg.Text("Abbreviation: "), sg.Input(default_text=dt_general['stages'][stage_select]['originabbreviation'], key='-GENERAL-ORIGIN-ABBREVIATION-')],[sg.Button('Save', key='-GENERAL-SAVE-MAIN-')]]
    general_window_orthography = []
    general_window_pronunciation = []
    general_window_allophony = []

    for i, x in enumerate(dt_general['stages'][stage_select]['orthography'][0]['rules']):
        general_window_orthography.append([sg.Column([[sg.Text("In:"),sg.Input(x[0], key='-ORTHOGRAPHY-INPUT-REG1-%s-' % i, enable_events=True),sg.Text("Out:"),sg.Input(x[1], key='-ORTHOGRAPHY-INPUT-REG2-%s-' % i, enable_events=True),sg.Button('+', enable_events=True, key='-ORTHOGRAPHY-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])])
    general_window_orthography = [[sg.Column(general_window_orthography, size=(700,375), scrollable=True, vertical_scroll_only=True, key='-ORTHOGRAPHY-COLUMN-CONTAINER-')],[sg.Button('Save', key='-ORTHOGRAPHY-SAVE-'),sg.Button('Clear', key='-ORTHOGRAPHY-CLEAR-FIELDS-'),sg.Button('Reload', key='-ORTHOGRAPHY-RELOAD-')],[sg.Text("Test your changes:"),sg.Input(key='-ORTHOGRAPHY-INPUT-TRYOUT-', enable_events=True),sg.Text(" > "),sg.Text(key='-ORTHOGRAPHY-OUTPUT-')]]

    for i, x in enumerate(dt_general['stages'][stage_select]['pronunciation']):
        general_window_pronunciation.append([sg.Column([[sg.Text("In:"),sg.Input(x[0], key='-PRONUNCIATION-INPUT-REG1-%s-' % i, enable_events=True),sg.Text("Out:"),sg.Input(x[1], key='-PRONUNCIATION-INPUT-REG2-%s-' % i, enable_events=True),sg.Button('+', enable_events=True, key='-PRONUNCIATION-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])])
    general_window_pronunciation = [[sg.Column(general_window_pronunciation, size=(700,375), scrollable=True, vertical_scroll_only=True, key='-PRONUNCIATION-COLUMN-CONTAINER-')],[sg.Button('Save', key='-PRONUNCIATION-SAVE-'),sg.Button('Clear', key='-PRONUNCIATION-CLEAR-FIELDS-'),sg.Button('Reload', key='-PRONUNCIATION-RELOAD-')],[sg.Text("Test your changes:"),sg.Input(key='-PRONUNCIATION-INPUT-TRYOUT-', enable_events=True),sg.Text(" > "),sg.Text(key='-PRONUNCIATION-OUTPUT-')]]

    for i, x in enumerate(dt_general['stages'][stage_select]['allophony']):
        general_window_allophony.append([sg.Column([[sg.Text("In:"),sg.Input(x[0], key='-ALLOPHONY-INPUT-REG1-%s-' % i, enable_events=True),sg.Text("Out:"),sg.Input(x[1], key='-ALLOPHONY-INPUT-REG2-%s-' % i, enable_events=True),sg.Button('+', enable_events=True, key='-ALLOPHONY-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])])
    general_window_allophony = [[sg.Column(general_window_allophony, size=(700,375), scrollable=True, vertical_scroll_only=True, key='-ALLOPHONY-COLUMN-CONTAINER-')],[sg.Button('Save', key='-ALLOPHONY-SAVE-'),sg.Button('Clear', key='-ALLOPHONY-CLEAR-FIELDS-'),sg.Button('Reload', key='-ALLOPHONY-RELOAD-')],[sg.Text("Test your changes:"),sg.Input(key='-ALLOPHONY-INPUT-TRYOUT-', enable_events=True),sg.Text(" > "),sg.Text(key='-ALLOPHONY-OUTPUT-')]]

    regex_playground_layout = [[sg.Text("Input"),sg.Input(expand_x=True, key='-REGEX-PLAYGROUND-INPUT-', enable_events=True)],[sg.Text("Turn"),sg.Input(expand_x=True, key='-REGEX-PLAYGROUND-REG1-', enable_events=True),sg.Text("into"),sg.Input(expand_x=True, key='-REGEX-PLAYGROUND-REG2-', enable_events=True)],[sg.Text("Output:"),sg.Text(key='-REGEX-PLAYGROUND-OUTPUT-')]]

    general_window = [[sg.TabGroup([[   sg.Tab('Main', general_window_main),
                                        sg.Tab('Orthography', general_window_orthography),
                                        sg.Tab('Pronunciation', general_window_pronunciation),
                                        sg.Tab('Allophony', general_window_allophony)]], expand_x=True, expand_y=True)],
                    [sg.Frame("Regex Playground", regex_playground_layout, expand_x=True, expand_y=True)]]
    # SOUND CHANGES
    sound_changes_window_regex = []

    for i, x in enumerate(dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['regex']):
        sound_changes_window_regex.append([sg.Column([[sg.Text("In:"),sg.Input(x[0], key='-SOUND-CHANGES-REGEX-INPUT-REG1-%s-' % i, enable_events=True, size=(10,1)),sg.Text("Out:"),sg.Input(x[1], key='-SOUND-CHANGES-REGEX-INPUT-REG2-%s-' % i, enable_events=True, size=(10,1)),sg.Button('+', enable_events=True, key='-SOUND-CHANGES-REGEX-INPUT-BUTTON-ADDROW-%s-' % i, metadata = i)]])])

    sound_changes_prose_before_tab = [[sg.Multiline(expand_y=True, expand_x=True, key='-SOUND-CHANGES-PROSE-BEFORE-', enable_events=True, right_click_menu=getTextFormattingRightClickMenu("-SOUND-CHANGES-PROSE-BEFORE-"))],[sg.Text("Formatted output:")],[sg.Multiline(expand_y=True, expand_x=True, key='-SOUND-CHANGES-PROSE-BEFORE-FORMATTED-', write_only=True, disabled=True)]]
    sound_changes_prose_after_tab = [[sg.Multiline(expand_y=True, expand_x=True, key='-SOUND-CHANGES-PROSE-AFTER-', enable_events=True, right_click_menu=getTextFormattingRightClickMenu("-SOUND-CHANGES-PROSE-AFTER-"))],[sg.Text("Formatted output:")],[sg.Multiline(expand_y=True, expand_x=True, key='-SOUND-CHANGES-PROSE-AFTER-FORMATTED-', write_only=True, disabled=True)]]

    sound_changes_window_information = [[sg.Checkbox('Start new chapter:', key='-SOUND-CHANGES-START-NEW-CHAPTER-TOGGLE-', enable_events=True),sg.Input(disabled=True, key='-SOUND-CHANGES-START-NEW-CHAPTER-NAME-')],[sg.TabGroup([[sg.Tab("Prose before SPE", sound_changes_prose_before_tab), sg.Tab("Prose after SPE", sound_changes_prose_after_tab)]], expand_x=True, expand_y=True)],[sg.Checkbox("Repeat changes until satisfactory", key='-SOUND-CHANGES-REPEAT-CHANGES-')],[sg.Checkbox("Hide from official documentation", key='-SOUND-CHANGES-HIDE-FROM-DOCS-')],[sg.Checkbox("Make sporadic", key='-SOUND-CHANGES-MAKE-SPORADIC-', enable_events=True), sg.Input(disabled=True, key='-SOUND-CHANGES-SPORADIC-NAME-')],[sg.Button('Save', key='-SOUND-CHANGES-SAVE-'),sg.Button('Move up', key='-SOUND-CHANGES-MOVE-UP-'),sg.Button('Move down', key='-SOUND-CHANGES-MOVE-DOWN-'),sg.Button('Delete', key='-SOUND-CHANGES-DELETE-'),sg.Button("+", key='-SOUND-CHANGES-INSERT-')]]
    sound_changes_window_changes = [[sg.Combo(values=[x['display'] for x in dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes']], default_value=dt_sound_changes['sc'][stage_select][sound_change_open_entry]['changes'][sound_change_open_entry_sub]['display'], readonly=True, enable_events=True, key='-SOUND-CHANGES-CHANGE-CHOOSE-BOX-', expand_x=True)],[sg.Input(key='-SOUND-CHANGES-CHANGE-DISPLAY-', expand_x=True)],[sg.Button("Save", key='-SOUND-CHANGES-REGEX-SAVE-'),sg.Button("Move up", key='-SOUND-CHANGES-REGEX-MOVE-UP-'),sg.Button("Move down", key='-SOUND-CHANGES-REGEX-MOVE-DOWN-'),sg.Button("Delete", key='-SOUND-CHANGES-REGEX-DELETE-'),sg.Button("+", key='-SOUND-CHANGES-REGEX-INSERT-')],[sg.Column(sound_changes_window_regex, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True, key='-SOUND-CHANGES-REGEX-CONTAINER-')]]
    sound_changes_window = [[sg.Combo(values=[x['prose'] for x in dt_sound_changes['sc'][stage_select]], default_value=dt_sound_changes['sc'][stage_select][sound_change_open_entry]['prose'], readonly=True, enable_events=True, expand_x=True, key='-SOUND-CHANGES-CHOOSE-COMBO-BOX-')],
                            [sg.Frame('Information', sound_changes_window_information, expand_y=True, expand_x=True),sg.Frame('Changes', sound_changes_window_changes, expand_y=True, expand_x=True)],
                            [sg.Text('Try this sound change:'),sg.Input(key='-SOUND-CHANGES-TRYOUT-THIS-ONLY-', enable_events=True),sg.Text(" > "),sg.Text(key='-SOUND-CHANGES-TRYOUT-THIS-ONLY-OUTPUT-')],
                            [sg.Text('Try all sound changes:'),sg.Input(key='-SOUND-CHANGES-TRYOUT-ALL-', enable_events=True),sg.Text(" > "),sg.Text(key='-SOUND-CHANGES-TRYOUT-ALL-OUTPUT-')]]
    # LEXICON
    lexicon_window1 = [[sg.Text("%s lemmas found." % len(dt_vocab['vcb'][stage_select]), key='-LEXICON-LEMMAS-FOUND-')],[sg.Listbox(values=[i['lemma'] for i in dt_vocab['vcb'][stage_select]], size=(20, 12), key="-LEMMA-SELECTION-LIST-", enable_events=True, expand_y=True)],[sg.Button('New', key='-LEXICON-ADD-NEW-LEMMA-')]]
    lexicon_window2 = [[sg.Text(key="-LEXICON2-INTERNAL-NAME-", expand_x=True)],[sg.Checkbox("Capitalise word", enable_events=True, key='-LEXICON-CAPITALISE-TOGGLE-')],[sg.Text("Meaning(s) of this lemma:")],[sg.Multiline(key="-LEXICON2-MEANING-", expand_x=True, size=(1,3))],[sg.Text("%s Root:" % dt_general['stages'][0]['originabbreviation']),sg.Combo(values=getSelectablePIERoots(), readonly=True, key='-LEXICON-ROOT-SELECT-', enable_events=True)],[sg.Combo(values=[], readonly=True, key='-LEXICON-ROOT-MEANING-SELECT-', expand_x=True)],[sg.Checkbox("Use Pre-%s reformation:" % dt_general['stages'][stage_select]['name'], key='-LEXICON-TOGGLE-POSTPIE-', enable_events=True),sg.Input(key='-LEXICON-FORMATION2-', disabled=True)],[sg.Text("%s Formation:" % dt_general['stages'][0]['originabbreviation']),sg.Input(key='-LEXICON-FORMATION1-')],[sg.Text("Meaning(s) of this formation (in %s):" % dt_general['stages'][0]['originabbreviation'])],[sg.Multiline(key="-LEXICON2-FORMATION-MEANING-", expand_x=True, size=(1,3))],[sg.Text("Sporadic changes:")]]
    for i, x in enumerate(dt_sound_changes['sc'][stage_select]):
        if 'sporadic' in x:
            lexicon_window2+= [[sg.Checkbox(x['sporadic'], disabled=True, key='-LEXICON-SPORADIC-CHECK%s-' % i, metadata=i, enable_events=True)]]
            sporadic_checkboxes.append('-LEXICON-SPORADIC-CHECK%s-' % i)
    
    lexicon_window3_nouns = [[sg.Checkbox(x, key='-LEXICON-NOUN-NUMBER-%s-' % x, enable_events=True) for x in dt_general['stages'][stage_select]['noun_numbers']],[sg.Text("%s inflection:" % dt_general['stages'][stage_select]['originabbreviation'])],[sg.Table(values=[], headings=([""] + dt_general['stages'][stage_select]['noun_numbers']), key='-LEXICON-NOUN-TABLE-', expand_x=True)],[sg.Text("Sound changed inflection:")],[sg.Table(values=[], headings=([""] + dt_general['stages'][stage_select]['noun_numbers']), key='-LEXICON-NOUN-TABLE2-', expand_x=True)],[sg.Text("Actual inflection:")],[sg.Table(values=[], headings=([""] + dt_general['stages'][stage_select]['noun_numbers']), key='-LEXICON-NOUN-TABLE3-', expand_x=True)]]
    lexicon_window3 = [[sg.Text("Category:"),sg.Combo(values=[], readonly=True, key="-LEXICON-CATEGORY-COMBO-", enable_events=True, size=(15,1))],[sg.Text("Inflection category:"),sg.Combo(values=[], readonly=True, enable_events=True, expand_x=True, key='-LEXICON-CATEGORY-SUB-COMBO-')],[sg.Column(lexicon_window3_nouns, expand_x=True, expand_y=True)]]
    lexicon_window4 = [[sg.Text("Etymological information:")],[sg.Multiline(expand_x=True, expand_y=True, key="-LEXICON-ETYMO-PROSE-", enable_events=True, right_click_menu=getTextFormattingRightClickMenu("-LEXICON-ETYMO-PROSE-"))],[sg.Text("Formatted output:")],[sg.Multiline(expand_x=True, expand_y=True, key="-LEXICON-ETYMO-PROSE-FORMATTED-", write_only=True, disabled=True)]]
    lexicon_window5 = [[sg.Text("sourcing")]]
    lexicon_window6 = [[sg.TabGroup([[  sg.Tab('Phonology', lexicon_window2),
                                        sg.Tab('Morphology', lexicon_window3),
                                        sg.Tab('Information', lexicon_window4),
                                        sg.Tab('Sourcing', lexicon_window5)]], expand_x=True, expand_y=True)],[sg.Button('Save', key='-LEXICON-EDIT-SAVE-'),sg.Button('Delete', key='-LEXICON-EDIT-DELETE-')]]
    lexicon_window = [[sg.Column(lexicon_window1, expand_y=True),sg.Column(lexicon_window6, expand_y=True, expand_x=True, visible=False, key="-LEXICON4-COLUMN-")]]
    # MORPHOLOGY
    ### nouns
    morph_nouns_left = [[sg.Text("Cases:")],[sg.Listbox(values=[x[0] for x in get_list_of_cases() if x[0] not in dt_general['stages'][stage_select]['cases']], size=(10, len(get_list_of_cases())), key='-MORPHO-NOUNS-CASES-UNUSED-'), sg.Listbox(values=[x for x in dt_general['stages'][stage_select]['cases']], size=(10, len(get_list_of_cases())), key='-MORPHO-NOUNS-CASES-USED-')],[sg.Text("Unused"),sg.Button(">", key='-MORPHO-NOUNS-MOVE-CASE-RIGHT-'),sg.Button("<", key='-MORPHO-NOUNS-MOVE-CASE-LEFT-'),sg.Text("Used")],[sg.Text("Noun number:")],[sg.Checkbox("SG", default=("SG" in dt_general['stages'][stage_select]['noun_numbers']), key='-MORPHO-NOUNS-NUMBER-SG-'),sg.Checkbox("DU", default=("DU" in dt_general['stages'][stage_select]['noun_numbers']), key='-MORPHO-NOUNS-NUMBER-DU-'),sg.Checkbox("PL", default=("PL" in dt_general['stages'][stage_select]['noun_numbers']), key='-MORPHO-NOUNS-NUMBER-PL-')],[sg.Text("Nominal gender:")],[sg.Checkbox("M", default=("M" in dt_general['stages'][stage_select]['genders']), key='-MORPHO-NOUNS-GENDER-M-'),sg.Checkbox("F", default=("F" in dt_general['stages'][stage_select]['genders']), key='-MORPHO-NOUNS-GENDER-F-'),sg.Checkbox("N", default=("N" in dt_general['stages'][stage_select]['genders']), key='-MORPHO-NOUNS-GENDER-N-')],[sg.Button("Save", key='-MORPHO-NOUNS-SAVE-DETAILS-'),sg.Button("Reload", key='-MORPHO-NOUNS-RELOAD-DETAILS-')]]
    if len(dt_declensions['decl'][stage_select]) > 0:
        num_headings = [""]
        morph_nouns_right_tab_pie_input = [""]
        for x in dt_general['stages'][stage_select]['noun_numbers']:
            num_headings.append(x)
            morph_nouns_right_tab_pie_input.append("")
        morph_nouns_right_tab_pie_output = [[sg.Table(morph_nouns_right_tab_pie_input, headings=num_headings, expand_x=True, expand_y=True, key='-MORPHO-NOUNS-TABLE-OUTPUT-')]]
        morph_nouns_right_tab_pie_input = [[sg.Table(morph_nouns_right_tab_pie_input, headings=num_headings, expand_x=True, expand_y=True, key='-MORPHO-NOUNS-TABLE-INPUT-')]]
        morph_nouns_right = [[sg.Combo(list(dt_declensions['decl'][stage_select].keys()), default_value=morpho_noun_open_entry, expand_x=True, readonly=True, key='-MORPHO-NOUNS-CHOOSE-DECLENSION-', enable_events=True)],[sg.Text("Name"), sg.Input(key='-MORPHO-NOUNS-NAME-')],[sg.Text('Abbreviation'), sg.Input(key='-MORPHO-NOUNS-ABBREVIATION-')],[sg.Text('%s regex' % dt_general['stages'][stage_select]['originabbreviation']), sg.Input(key='-MORPHO-NOUNS-REGEX-ORIGINAL-')],[sg.Text('%s regex' % dt_general['stages'][stage_select]['name']), sg.Input(key='-MORPHO-NOUNS-REGEX-ACTUALWORD-')],[sg.Text(key='-MORPHO-NOUNS-REGEX-RESULTS-')],[sg.Text("Gender:"), sg.Combo(dt_general['stages'][stage_select]['genders'], key='-MORPHO-NOUNS-DECLENSION-GENDER-'),sg.Button("Save", key='-MORPHO-NOUNS-SAVE-DECLENSION-'),sg.Button("New", key='-MORPHO-NOUNS-ADD-DECLENSION-'),sg.Button("Delete", key='-MORPHO-NOUNS-DELETE-DECLENSION-')],[sg.Frame("%s (Pre-%s) inflection" % (dt_general['stages'][stage_select]['originabbreviation'], dt_general['stages'][stage_select]['name']), morph_nouns_right_tab_pie_input, expand_x=True)],[sg.Frame("%s inflection" % dt_general['stages'][stage_select]['name'], morph_nouns_right_tab_pie_output, expand_x=True)]]
    else:
        morph_nouns_right = [[sg.Text("Please fill out the details on the left.")]]
    morph_nouns_window = [[sg.Frame("Inflection details", morph_nouns_left, expand_y=True), sg.Frame("Declension types", morph_nouns_right, expand_x=True, expand_y=True)]]
    ### everything
    morphology_window = [[sg.TabGroup([[    sg.Tab('Nouns', morph_nouns_window)]], expand_x=True, expand_y=True)]]
    # RENDER
    render_window = [[sg.Button('LaTeX', key='-RENDER-LATEX-BUTTON-')],[sg.Multiline(size=(60,15), font='Courier 8', expand_x=True, expand_y=True, write_only=True, reroute_stdout=(not debug), reroute_stderr=(not debug), reroute_cprint=(not debug), autoscroll=True, auto_refresh=True, disabled=True, echo_stdout_stderr=True, key='-RENDER-LOGS-')]]
    # SOURCES
    sources_window = [[sg.Text("source manager")]]
    # ROOTS
    roots_window1 = [[sg.Text("%s roots found." % len(dt_roots), key='-ROOTS-FOUND-')],[sg.Listbox(values=[apie_to_pie(i) for i in sorted(list(dt_roots.keys()))], size=(20, 12), key='-ROOTS-SELECTION-LIST-', enable_events=True, expand_y=True)],[sg.Button("New", key='-ROOTS-NEW-')]]
    roots_window2 = [[sg.Text(key="-ROOTS-NAME-")],[sg.Text("Please enter the meanings for this root below.\nSeparate them with an extra newline to indicate homonyms with different meanings.")],[sg.Multiline(key='-ROOTS-MEANINGS-', expand_x=True, size=(1,10))],[sg.Button("Save", key='-ROOTS-SAVE-'), sg.Button("Delete", key='-ROOTS-DELETE-')]]

    roots_window = [[sg.Column(roots_window1, expand_y=True),sg.Column(roots_window2, expand_y=True, expand_x=True, visible=False, key="-ROOTS-COLUMN-")]]
    # STATISTICS
    statistics_window = [[sg.Text("Time spent working on this project:"),sg.Text(key='-STATISTICS-TIME-SPENT-')]]
    # TO DO LIST
    todo_window_urgent = [[sg.Text(key='-TO-DO-LIST-URGENT-')]]
    todo_window_warnings = [[sg.Text(key='-TO-DO-LIST-WARNING-')]]
    todo_window_sourcing = [[sg.Text(key='-TO-DO-LIST-SOURCING-')]]
    todo_window = [[sg.TabGroup([[  sg.Tab('Urgent', todo_window_urgent),
                                    sg.Tab('Warnings', todo_window_warnings),
                                    sg.Tab('Sourcing', todo_window_sourcing)]], expand_x=True, expand_y=True)]]

    # ASSEMBLE LAYOUTS INTO WINDOW
    window_layout = [[sg.Text(project_name), sg.Combo(values=get_list_of_stages(), default_value=get_list_of_stages()[stage_select], readonly=True)]]
    window_layout += [[sg.TabGroup([[   sg.Tab('General', general_window, key='-GLOBAL-TABS-GENERAL-'),
                                        sg.Tab('Sound Changes', sound_changes_window, key='-GLOBAL-TABS-SOUND CHANGES-'),
                                        sg.Tab('Lexicon', lexicon_window, key='-GLOBAL-TABS-LEXICON-'),
                                        sg.Tab('Morphology', morphology_window, key='-GLOBAL-TABS-MORPHOLOGY-'),
                                        sg.Tab('%s Roots' % dt_general['stages'][stage_select]['originabbreviation'], roots_window, key='-GLOBAL-TABS-ROOTS-'),
                                        sg.Tab('Render', render_window, key='-GLOBAL-TABS-RENDER-'),
                                        sg.Tab('Source Manager', sources_window, key='-GLOBAL-TABS-SOURCE MANAGER-'),
                                        sg.Tab('Statistics', statistics_window, key='-GLOBAL-TABS-STATISTICS-'),
                                        sg.Tab('To-Do List', todo_window, key='-GLOBAL-TABS-TO-DO-LIST-')]], expand_x=True, expand_y=True, key='-GLOBAL-TABS-')]]

    wd_window = sg.Window('Project π', window_layout, size=(1280,720), finalize=True, resizable=True)

    wd_window['-LEXICON-FORMATION1-'].bind('<FocusOut>','FOCUS-OUT-')
    wd_window['-LEXICON-FORMATION2-'].bind('<FocusOut>','FOCUS-OUT-')

    if len(dt_declensions['decl'][stage_select]) > 0:
        wd_window['-MORPHO-NOUNS-TABLE-INPUT-'].bind('<Button-1>','CLICK-')
        wd_window['-MORPHO-NOUNS-REGEX-ORIGINAL-'].bind('<FocusOut>', 'FOCUS-OUT-')
        wd_window['-MORPHO-NOUNS-REGEX-ACTUALWORD-'].bind('<FocusOut>', 'FOCUS-OUT-')

    # call some loading functions
    if refresh_window_to != "":
        wd_window[refresh_window_to].select()
        refresh_window_to = ""
    loadSoundChange(sound_change_open_entry, {})
    if len(dt_declensions['decl'][stage_select]) > 0:
        loadMorphoDeclension(morpho_noun_open_entry)
    update_statistics()
    update_to_do_list()

    # MAIN SUBLOOP
    while True:
        event, values = wd_window.read(timeout = 100)
        # Update containers
        for x in containers_to_update:
            wd_window[x].contents_changed()
            containers_to_update.remove(x)
        # Update statistics
        update_statistics()
        if debug and event !="__TIMEOUT__":
            print(event, values)
        # EXIT
        if event == sg.WIN_CLOSED:
            wd_window.close()
            quit()
        if refresh_window:
            refresh_window_to = values['-GLOBAL-TABS-']
            break
        # GENERAL EVENTS
        if event == "-GENERAL-SAVE-MAIN-":
            saveMainData(values)
        if event.startswith("-REGEX-PLAYGROUND-"):
            updateRegexPlayground(values)
        # ORTHOGRAPHY EDITOR
        if event.startswith("-ORTHOGRAPHY-INPUT-"):
            updateOrthoPronAllophonyTryout(values, "ORTHOGRAPHY")
        if event.startswith("-ORTHOGRAPHY-INPUT-BUTTON-ADDROW-"):
            insertOrthoRow(wd_window[event].metadata, values, "ORTHOGRAPHY")
        if event == "-ORTHOGRAPHY-SAVE-":
            saveOrthography(values)
        if event == "-ORTHOGRAPHY-CLEAR-FIELDS-":
            clearOrthographyPronAllophony(values, "ORTHOGRAPHY")
            updateOrthoPronAllophonyTryout(values, "ORTHOGRAPHY")
        if event == "-ORTHOGRAPHY-RELOAD-":
            reloadOrthography(values)
            updateOrthoPronAllophonyTryout(values, "ORTHOGRAPHY")
        # PRONUNCIATION EDITOR
        if event.startswith("-PRONUNCIATION-INPUT-"):
            updateOrthoPronAllophonyTryout(values, "PRONUNCIATION")
        if event.startswith("-PRONUNCIATION-INPUT-BUTTON-ADDROW-"):
            insertOrthoRow(wd_window[event].metadata, values, "PRONUNCIATION")
        if event == "-PRONUNCIATION-SAVE-":
            savePronunciationAllophony(values, "PRONUNCIATION")
        if event == "-PRONUNCIATION-CLEAR-FIELDS-":
            clearOrthographyPronAllophony(values, "PRONUNCIATION")
            updateOrthoPronAllophonyTryout(values, "PRONUNCIATION")
        if event == "-PRONUNCIATION-RELOAD-":
            reloadPronunciationAllophony(values, "PRONUNCIATION")
            updateOrthoPronAllophonyTryout(values, "PRONUNCIATION")
        # ALLOPHONY EDITOR
        if event.startswith("-ALLOPHONY-INPUT-"):
            updateOrthoPronAllophonyTryout(values, "ALLOPHONY")
        if event.startswith("-ALLOPHONY-INPUT-BUTTON-ADDROW-"):
            insertOrthoRow(wd_window[event].metadata, values, "ALLOPHONY")
        if event == "-ALLOPHONY-SAVE-":
            savePronunciationAllophony(values, "ALLOPHONY")
        if event == "-ALLOPHONY-CLEAR-FIELDS-":
            clearOrthographyPronAllophony(values, "ALLOPHONY")
            updateOrthoPronAllophonyTryout(values, "ALLOPHONY")
        if event == "-ALLOPHONY-RELOAD-":
            reloadPronunciationAllophony(values, "ALLOPHONY")
            updateOrthoPronAllophonyTryout(values, "ALLOPHONY")
        # SOUND CHANGE EVENTS
        if event == "-SOUND-CHANGES-CHOOSE-COMBO-BOX-":
            if len(dt_sound_changes['sc'][stage_select]) > 0:
                sound_change_open_entry = wd_window["-SOUND-CHANGES-CHOOSE-COMBO-BOX-"].widget.current()
                loadSoundChange(sound_change_open_entry, values)
        if event == "-SOUND-CHANGES-START-NEW-CHAPTER-TOGGLE-":
            toggleSoundChangeNewChapter(values['-SOUND-CHANGES-START-NEW-CHAPTER-TOGGLE-'])
        if event == "-SOUND-CHANGES-SAVE-":
            saveSoundChanges(values)
        if event == "-SOUND-CHANGES-DELETE-":
            deleteSoundChange()
        if event == "-SOUND-CHANGES-MOVE-UP-":
            moveSoundChangeUp()
        if event == "-SOUND-CHANGES-MOVE-DOWN-":
            moveSoundChangeDown()
        if event == "-SOUND-CHANGES-TRYOUT-THIS-ONLY-":
            updateSoundChangeTryout("THIS-ONLY", values)
        if event == "-SOUND-CHANGES-TRYOUT-ALL-":
            updateSoundChangeTryout("ALL", values)
        if event == "-SOUND-CHANGES-CHANGE-CHOOSE-BOX-":
            sound_change_open_entry_sub = wd_window['-SOUND-CHANGES-CHANGE-CHOOSE-BOX-'].widget.current()
            loadSoundChangeRegexes(sound_change_open_entry, sound_change_open_entry_sub, values)
        if event.startswith("-SOUND-CHANGES-REGEX-INPUT-BUTTON-ADDROW-"):
            insertSoundChangeRegexRow(wd_window[event].metadata, values)
        if event == "-SOUND-CHANGES-REGEX-SAVE-":
            saveSoundChangesRegex(values)
        if event == "-SOUND-CHANGES-REGEX-MOVE-UP-":
            moveSoundChangeRegexUp()
        if event == "-SOUND-CHANGES-REGEX-MOVE-DOWN-":
            moveSoundChangeRegexDown()
        if event == "-SOUND-CHANGES-REGEX-DELETE-":
            deleteSoundChangeRegex()
        if event == "-SOUND-CHANGES-REGEX-INSERT-":
            insertSoundChangeRegex()
        if event == "-SOUND-CHANGES-INSERT-":
            insertSoundChange()
        if event == "-SOUND-CHANGES-MAKE-SPORADIC-":
            toggleSoundChangeSporadic(values['-SOUND-CHANGES-MAKE-SPORADIC-'])
        if event == "-SOUND-CHANGES-PROSE-BEFORE-":
            format_text_preview(values['-SOUND-CHANGES-PROSE-BEFORE-'], '-SOUND-CHANGES-PROSE-BEFORE-FORMATTED-')
        if event == "-SOUND-CHANGES-PROSE-AFTER-":
            format_text_preview(values['-SOUND-CHANGES-PROSE-AFTER-'], '-SOUND-CHANGES-PROSE-AFTER-FORMATTED-')
        # LEXICON EVENTS
        if event == "-LEMMA-SELECTION-LIST-":
            if len(dt_vocab['vcb'][stage_select]) > 0:
                lexicon_open_entry = wd_window["-LEMMA-SELECTION-LIST-"].GetIndexes()[0]
                loadDetailsOfLexiconEntry(lexicon_open_entry, stage_select, values)
        if event == "-LEXICON-EDIT-SAVE-":
            saveLexiconEntry(lexicon_open_entry, stage_select, values)
        if event == "-LEXICON-EDIT-DELETE-":
            deleteLexiconEntry(lexicon_open_entry, stage_select)
        if event == "-LEXICON-ROOT-SELECT-":
            updateLexiconPIERootMeanings(values['-LEXICON-ROOT-SELECT-'])
        if event == "-LEXICON-FORMATION1-FOCUS-OUT-" and not values['-LEXICON-TOGGLE-POSTPIE-']:
            wd_window['-LEXICON-FORMATION1-'].update(updatePreviewFromFormation(values['-LEXICON-FORMATION1-'], stage_select, values))
        if event == "-LEXICON-FORMATION2-FOCUS-OUT-":
            wd_window['-LEXICON-FORMATION2-'].update(updatePreviewFromFormation(values['-LEXICON-FORMATION2-'], stage_select, values))
        if event == "-LEXICON-TOGGLE-POSTPIE-":
            toggleLexiconPostPIEField(values, stage_select)
        if event.startswith("-LEXICON-SPORADIC-CHECK") or event == "-LEXICON-CAPITALISE-TOGGLE-":
            updatePreviewFromFormationNoReturn(values)
        if event == "-LEXICON-ADD-NEW-LEMMA-":
            addNewLexiconLemma(values)
        if event == "-LEXICON-CATEGORY-COMBO-":
            reevaluateLexiconInflection(values, False)
        if event == "-LEXICON-ETYMO-PROSE-":
            format_text_preview(values['-LEXICON-ETYMO-PROSE-'], '-LEXICON-ETYMO-PROSE-FORMATTED-')
        # ROOT EVENTS
        if event == "-ROOTS-SELECTION-LIST-":
            root_open_entry = pie_to_apie(values['-ROOTS-SELECTION-LIST-'][0])
            loadRoot(root_open_entry)
        if event == "-ROOTS-DELETE-":
            deleteRoot(root_open_entry)
        if event == "-ROOTS-SAVE-":
            saveRoot(root_open_entry, values)
        if event == "-ROOTS-NEW-":
            newRoot()
        # NOUN MORPHO EVENTS
        if event == "-MORPHO-NOUNS-MOVE-CASE-RIGHT-":
            moveMorphoNounsCaseRight(values)
        if event == "-MORPHO-NOUNS-MOVE-CASE-LEFT-":
            moveMorphoNounsCaseLeft(values)
        if event == "-MORPHO-NOUNS-RELOAD-DETAILS-":
            reloadMorphoNounsCase()
        if event == "-MORPHO-NOUNS-SAVE-DETAILS-":
            saveMorphoNounsCase(values)
        if event == "-MORPHO-NOUNS-CHOOSE-DECLENSION-":
            morpho_noun_open_entry = values['-MORPHO-NOUNS-CHOOSE-DECLENSION-']
            loadMorphoDeclension(morpho_noun_open_entry)
        if event == "-MORPHO-NOUNS-TABLE-INPUT-CLICK-":
            clickMorphoNounsInputTable()
        if event.startswith('-MORPHO-NOUNS-') and event.endswith('FOCUS-OUT-'):
            wd_window['-MORPHO-NOUNS-REGEX-RESULTS-'].update(evaluateMorphoNounRegexes(values['-MORPHO-NOUNS-REGEX-ORIGINAL-'], values['-MORPHO-NOUNS-REGEX-ACTUALWORD-']))
        if event == "-MORPHO-NOUNS-SAVE-DECLENSION-":
            saveMorphoDeclension(values)
        if event == "-MORPHO-NOUNS-ADD-DECLENSION-":
            addMorphoDeclension()
        if event == "-MORPHO-NOUNS-DELETE-DECLENSION-":
            deleteMorphoDeclension()
        # RENDER EVENTS
        if event == "-RENDER-LATEX-BUTTON-":
            for key, value in enumerate(get_list_of_stages()):
                render_latex(key)
        # TEXT FORMATTING EVENTS
        checkTextFormatRightClick(event, values, "-LEXICON-ETYMO-PROSE-")
        checkTextFormatRightClick(event, values, "-SOUND-CHANGES-PROSE-BEFORE-")
        checkTextFormatRightClick(event, values, "-SOUND-CHANGES-PROSE-AFTER-")
    wd_window.close()