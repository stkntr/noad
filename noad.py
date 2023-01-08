#!/usr/bin/env python3
#noad.py : get entries from oxford en-us dictionary and
#          print most of them to stdout
#Ommited items:
#“shortDefinitions“, “respell pronunciations which have IPA”

#Documnents of "Oxford Dictionaries API"
#https://developer.oxforddictionaries.com/documentation
#https://developer.oxforddictionaries.com/documentation/languages
#https://developer.oxforddictionaries.com/documentation/glossary
#https://developer.oxforddictionaries.com/faq
#https://developer.oxforddictionaries.com/api-terms-and-conditions
#https://forum.oxforddictionaries.com/api/

#Other references about layout and so on
#https://www.lexico.com/
#macOS's Dictionary.app

import requests
import json
import sys
import string
import re
import os
import shutil
import urllib
import subprocess

import colorful as cf
cf.use_8_ansi_colors()
#https://pypi.org/project/colorful/

import textwrap

import math
import io
from mutagen.mp3 import MP3

from time import sleep
from playsound import playsound
""" Known problem with playsound module on macOS
“playsound” module imports AppKit module of PyObjC on macOS.
So PyObjC and PyObjC-core modules are needed on macOS.
https://pypi.org/project/pyobjc/
Do not install different another AppKit module by pip etc.
If AppKit module has been installed and the error occurred like bellow,
uninstall appkit module and reinstall PyObjC module.
Example of error:
> ImportError: No module named AppKit
Uninstall AppKit:
$ pip3 uninstall appkit
Uninstall and reinstall PyObjC, PyObjC-core:
$ pip3 uninstall PyObjC PyObjC-core
$ pip3 install PyObjC PyObjC-core
or
$ pip3 install --upgrade --force-reinstall PyObjC PyObjC-core
"""

"""fixed values"""
# TODO: replace with your own app_id and app_key
app_id = '<my app_id>'
app_key = '<my app_key>'
language = 'en-us' #en-us
endpoint = 'entries'
filters = ''
#filters = '?pronunciations'

ref_bullet = ''
#ref_bullet = cf.bold_blue('▶ ')

#https://stackoverflow.com/questions/8651361/how-do-you-print-superscript-in-python

superscript_map = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶',
    '7': '⁷', '8': '⁸', '9': '⁹', 'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ',
    'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ᶦ', 'j': 'ʲ', 'k': 'ᵏ',
    'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ', 'q': '۹', 'r': 'ʳ',
    's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ',
    'z': 'ᶻ', 'A': 'ᴬ', 'B': 'ᴮ', 'C': 'ᶜ', 'D': 'ᴰ', 'E': 'ᴱ', 'F': 'ᶠ',
    'G': 'ᴳ', 'H': 'ᴴ', 'I': 'ᴵ', 'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ', 'M': 'ᴹ',
    'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ', 'Q': 'Q', 'R': 'ᴿ', 'S': 'ˢ', 'T': 'ᵀ',
    'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ', 'X': 'ˣ', 'Y': 'ʸ', 'Z': 'ᶻ', '+': '⁺',
    '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾'}

trans_sup = str.maketrans(
    ''.join(superscript_map.keys()),
    ''.join(superscript_map.values()))

"""variable values"""
playlist = []

def print_notation(text):
    print('– ' + text + ' –')

def check_args():
    args = sys.argv
    #language = args[1]
    try:
        #word = args[1]
        word = ' '.join(args[1:])
        #print(word)
        word = urllib.parse.quote(word, safe='')
        return word
    except IndexError:
        print('An argument for word is needed.')
        quit()

def check_dirs(dir_path, message):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print_notation(message)
        print('-> ' + dir_path)

def style(text, obj_type):
    styles = {
        'word':             lambda t: str(cf.bold(t)),
        'synonym':          lambda t: str(cf.blue(t)),
        'reference':        lambda t: str(cf.bold_blue(t)),
        'title':            lambda t: str(cf.red(t)),
        'title_inline':     lambda t: str(cf.red(t)),
        'block_note':       lambda t: str(cf.inversed_cyan(t)),
        'dialects':         lambda t: str(cf.inversed(' ' + t + ' ')),
        'region':           lambda t: str(cf.inversed(' ' + t + ' ')),
        'note_inline':      lambda t: str(cf.underlined(t)),
        'inflected_form':   lambda t: str(cf.bold(t)),
        'body_bold':        lambda t: str(cf.bold(t)),
        'example_body':     lambda t: str(cf.italic(t)),
        'example_bold':     lambda t: str(cf.bold(t)),
    }
    return styles[obj_type](text)

def write_result(result_files_dir, r_json):
    with open(result_files_dir, mode='w') as f:
        f.write(json.dumps(r_json))

def print_obj(d):
    if isinstance(d, dict):
        for k,v in d.items():
            if isinstance(v, dict):
                print_obj(v)
            elif isinstance(v, list):
                print (k,':')
                print_obj(v)
            else:
                print (k,':',v)
    elif isinstance(d, list):
        for v in d:
            if isinstance(v, dict):
                print_obj(v)
            elif isinstance(v, list):
                print_obj(v)
            else:
                print (v)

def int_to_roman(num):
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
        ]
    syb = [
        'M', 'CM', 'D', 'CD',
        'C', 'XC', 'L', 'XL',
        'X', 'IX', 'V', 'IV',
        'I'
        ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

"""Custom TextWrapper for colored text"""
#https://docs.python.org/3/library/textwrap.html
#https://note.nkmk.me/python-textwrap-wrap-fill-shorten/
#http://www.freia.jp/taka/blog/python-textwrap-with-japanese/index.html

def len_plain(s):
    """len_plain(s : string) -> int

    This removes color code from an argument as string and
    return length of it.
    """
    p = re.compile(r'\033\[\d+(;\d+)*m')
    s = p.sub(r'', s)
    return len(s)

class ColoredTextWrapper(textwrap.TextWrapper):
    """Custom subclass that uses len_plain() instead of len()."""

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]

        Wrap a sequence of text chunks and return a list of lines of
        length 'self.width' or less.  (If 'break_long_words' is false,
        some lines may be longer than this.)  Chunks correspond roughly
        to words and the whitespace between them: each chunk is
        indivisible (modulo 'break_long_words'), but a line break can
        come between any two chunks.  Chunks should not have internal
        whitespace; ie. a chunk is either all whitespace or a "word".
        Whitespace chunks will be removed from the beginning and end of
        lines, but apart from that whitespace is preserved.
        """
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            if len_plain(indent) + len_plain(self.placeholder.lstrip()) \
                > self.width:
                raise ValueError("placeholder too large for max width")

        # Arrange in reverse order so items can be efficiently popped
        # from a stack of chucks.
        chunks.reverse()

        while chunks:

            # Start the list of chunks that will make up the current line.
            # cur_len is just the length of all the chunks in cur_line.
            cur_line = []
            cur_len = 0

            # Figure out which static string will prefix this line.
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            # Maximum width for this line.
            width = self.width - len_plain(indent)

            # First chunk on line is whitespace -- drop it, unless this
            # is the very beginning of the text (ie. no lines started yet).
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                l = len_plain(chunks[-1])

                # Can at least squeeze this chunk onto the current line.
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                # Nope, this line is full.
                else:
                    break

            # The current line is full, and the next chunk is too big to
            # fit on *any* line (not just this one).
            if chunks and len_plain(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(len_plain, cur_line))

            # If the last chunk on this line is all whitespace, drop it.
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                cur_len -= len_plain(cur_line[-1])
                del cur_line[-1]

            if cur_line:
                if (self.max_lines is None or
                    len(lines) + 1 < self.max_lines or
                    (not chunks or
                     self.drop_whitespace and
                     len(chunks) == 1 and
                     not chunks[0].strip()) and cur_len <= width):
                    # Convert current line back to a string and store it in
                    # list of all lines (return value).
                    lines.append(indent + ''.join(cur_line))
                else:
                    while cur_line:
                        if (cur_line[-1].strip() and
                            cur_len + len_plain(self.placeholder) <= width):
                            cur_line.append(self.placeholder)
                            lines.append(indent + ''.join(cur_line))
                            break
                        cur_len -= len_plain(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            if (len_plain(prev_line) + \
                                    len_plain(self.placeholder) <=
                                    self.width):
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break

        return lines

#https://www.lifewithpython.com/2017/10/python-terminal-size.html
terminal_size = shutil.get_terminal_size()
columns = terminal_size.columns
indent_digit = 4
margin_right = 2
columns_width = int(columns) - margin_right

#https://stackoverflow.com/questions/18756510/printing-with-indentation-in-python
def make_text_wrapper(initial_text, width, level, indent_digit):
    if (level == 0):
        wrapper = ColoredTextWrapper(initial_indent = initial_text, \
                    width = width)
    elif (level == 1):
        wrapper = ColoredTextWrapper(initial_indent = initial_text, \
                    width = width, \
                    subsequent_indent = ' '*indent_digit*level)
    elif (level == 2):
        wrapper = ColoredTextWrapper(initial_indent = ' '*indent_digit + \
                    initial_text, width = width, \
                    subsequent_indent = ' '*indent_digit*level)
    return wrapper

wrapper_0 = make_text_wrapper('', columns_width, 0, indent_digit)
wrapper_1 = make_text_wrapper('', columns_width, 1, indent_digit)
wrapper_2 = make_text_wrapper('', columns_width, 2, indent_digit)

def remove_color_of_indent_space(s):
    target_re_list = [
            r'((?:\033\[\d+(?:;\d+)*m)+)([^\033]+?)(\n +)' + \
            r'([^\033]+?)((?:\033\[(?:27|39|24|0)m)+)', \
        ]
    for e in target_re_list:
        p = re.compile(e)
        m = p.search(s)
        while m != None:
            s = p.sub(r'\1\2\5\3\1\4\5', s)
            m = p.search(s)
    return s

def remove_color(colored_text):
    p = re.compile(r'\033\[\d+(?:;\d+)*m')
    result = p.sub(r'', colored_text)
    return result

def fill_end_of_line(string, filler, width):
    #http://www.medievalcodes.ca/2016/04/line-fillers.html
    #https://www.pinterest.jp/yvianne/line-fillers/
    lines_filled = []
    p = re.compile(r'((\033\[\d+(?:;\d+)*m)*)$')
    for line in string.split('\n'):
        number = width - len_plain(line)
        filler_text = filler*number
        line_filled = p.sub(r'%s\1' % filler_text, line, 1)
        lines_filled.append(line_filled)
    return '\n'.join(lines_filled)

def capitalize_region(region):
    region_modified = ''
    all_caps = ['US', 'SE']
    if ('_' in region):
        region = region.replace('_', ' ')
    region = region.title()
    words = region.split(' ')
    for i, word in enumerate(words):
        if (word.upper() in all_caps):
            words[i] = word.upper()
    region_modified = ' '.join(words)
    return region_modified

block_note_types = ['technicalNote', 'encyclopedicNote', 'editorialNote']

def make_note_text_pre(obj, block_note_types):
    notes_texts = []
    notes_text = ''
    if 'notes' in obj:
        notes = obj['notes']
        for j, note in enumerate(notes):
            note_text = ''
            if (note['type'] == 'grammaticalNote'):
                note_text = '[' + note['text'] + ']'
                note_text = style(note_text, 'note_inline')
                #print(note_text)
            elif (note['type'] == 'wordFormNote'):
                note_text = note['text']
                re_bold = re.compile(r'"([^"]*)"')
                note_text = re_bold.sub(style(r'\1', 'body_bold'), note_text)
                note_text = '(' + note_text + ')'
            elif (note['type'] in block_note_types):
                pass
            else:
                note_text = note['text']
                note_text = style(note_text, 'note_inline')
            if (note_text):
                notes_texts.append(note_text)
    else:
        #print('not found notes')
        pass
    if (len(notes_texts) > 0):
        notes_text = ' '.join(notes_texts)
        #print(notes_text)
    return notes_text

def is_terminated(text):
    text = remove_color(text)
    period_like_characters = ['.', '!', '?']
    if text and text[-1] not in period_like_characters:
        return False
    else:
        return True

def make_note_texts_after(obj, block_note_types):
    notes_texts = []
    if 'notes' in obj:
        notes = obj['notes']
        for j, note in enumerate(notes):
            note_text = ''
            if (note['type'] in block_note_types):
                note_text = note['text']
                if is_terminated(note_text):
                    pass
                else:
                    note_text += '.'
                note_text = style(note_text, 'block_note')
            else:
                pass
            if (note_text):
                notes_texts.append(note_text)
    else:
        #print('not found notes')
        pass
    return notes_texts

def make_regions_text(obj):
    regions_texts = []
    regions_text = ''
    if 'regions' in obj:
        regions = obj['regions']
        for j, region in enumerate(regions):
            region_text = style(capitalize_region(region['text']), 'region')
            regions_texts.append(region_text)
        regions_text = ' '.join(regions_texts)
    else:
        #print('not found regions')
        pass
    return regions_text

def make_registers_text(obj):
    registers_texts = []
    registers_text = ''
    if 'registers' in obj:
        registers = obj['registers']
        for j, register in enumerate(registers):
            registers_texts.append(register['text'].lower().replace('_', ' '))
        registers_text = style(', '.join(registers_texts), 'note_inline')
    else:
        #print('not found registers')
        pass
    return registers_text

def make_domainClasses_text(obj):
    domainClasses_texts = []
    domainClasses_text = ''
    if 'domainClasses' in obj:
        domainClasses = obj['domainClasses']
        for j, domainClass in enumerate(domainClasses):
            domainClasses_texts.append(domainClass['text'].replace('_', ' '))
        domainClasses_text = style(', '.join(domainClasses_texts), \
                                   'note_inline')
    else:
        #print('not found domainClasses')
        pass
    return domainClasses_text

def make_domains_text(obj):
    domains_texts = []
    domains_text = ''
    if 'domains' in obj:
        domains = obj['domains']
        for j, domain in enumerate(domains):
            domains_texts.append(domain['text'].replace('_', ' '))
        domains_text = style(', '.join(domains_texts), 'note_inline')
    else:
        #print('not found domains')
        pass
    return domains_text

def make_semanticClasses_text(obj):
    semanticClasses_texts = []
    semanticClasses_text = ''
    if 'semanticClasses' in obj:
        semanticClasses = obj['semanticClasses']
        for j, semanticClass in enumerate(semanticClasses):
            semanticClasses_texts.append(semanticClass['text'].\
                                         replace('_', ' '))
        semanticClasses_text = style(', '.join(semanticClasses_texts), \
                                     'note_inline')
    else:
        #print('not found semanticClasses')
        pass
    return semanticClasses_text

def make_definitions_text(obj):
    definitions_texts = []
    definitions_text = ''
    if 'definitions' in obj:
        definitions = obj['definitions']
        definitions_text = '/'.join(definitions)
        #print(definitions_text)
    else:
        #print('not found definitions')
        pass
    return definitions_text

def make_constructions_texts(obj):
    constructions_texts = []
    if 'constructions' in obj:
        constructions = obj['constructions']
        constructions_texts = [d.get('text') for d in constructions]
        #print(constructions_texts)
    else:
        #print('not found constructions')
        pass
    return constructions_texts

def make_variantForms_texts(obj):
    variantForms_texts = []
    if 'variantForms' in obj:
        variantForms = obj['variantForms']
        variantForms_texts = [d.get('text') for d in variantForms]
        #print(variantForms_texts)
    else:
        #print('not found variantForms')
        pass
    return variantForms_texts

def make_examples_text(obj, bold_texts_in_examples):
    examples_texts = []
    examples_text = ''
    if 'examples' in obj:
        examples = obj['examples']
        for j, example in enumerate(examples):
            example_text = example['text'].strip()
            example_text = style(example_text, 'example_body')
            if (len(bold_texts_in_examples) > 0):
                for bold_text in bold_texts_in_examples:
                    style_text = style(bold_text, 'example_bold')
                    example_text = \
                        example_text.replace(bold_text, style_text)
                #print(example_text)
            example_note_text = make_note_text_pre(example, block_note_types)
            if (example_note_text):
                example_text = example_note_text + ' ' + example_text
            examples_texts.append(example_text)
        examples_text = ' | '.join(examples_texts)
    else:
        #print('not found examples')
        pass
    return examples_text

def make_crossReferenceMarkers_text(obj):
    crossReferenceMarkers_texts = []
    crossReferenceMarkers_text = ''
    if 'crossReferenceMarkers' in obj:
        crossReferenceMarkers = obj['crossReferenceMarkers']
        for j, crossReferenceMarker in enumerate(crossReferenceMarkers):
            if 'crossReferences' in obj:
                crossReferences = obj['crossReferences']
                for k, crossReference in enumerate(crossReferences):
                    crossReference_text = crossReference['text']
                    crossReference_text_styled = style(crossReference_text, \
                                                       'reference')
                    crossReferenceMarker = crossReferenceMarker.\
                        replace(crossReference_text, \
                        crossReference_text_styled)
                crossReferenceMarker_text = crossReferenceMarker
                crossReferenceMarkers_texts.append(crossReferenceMarker_text)
            else:
                re_bold = re.compile(r'"([^"]*)"')
                if re_bold.search(crossReferenceMarker):
                    # replacement of the text quoted with "" to bold text
                    crossReferenceMarker = re_bold.sub(\
                                                style(r'\1', 'body_bold'), \
                                                crossReferenceMarker)
                    crossReferenceMarker_text = crossReferenceMarker
                    crossReferenceMarkers_texts.append(\
                                                    crossReferenceMarker_text)
                else:
                    crossReferenceMarker_text = crossReferenceMarker
                    crossReferenceMarkers_texts.append(\
                                                crossReferenceMarker_text)
            crossReferenceMarkers_text = ref_bullet + \
                                         ', '.join(crossReferenceMarkers_texts)
    else:
        #print('not found crossReferenceMarkers')
        pass
    return crossReferenceMarkers_text

def make_synonyms_text(obj):
    synonyms_texts = []
    synonyms_text = ''
    if 'synonyms' in obj:
        synonyms = obj['synonyms']
        for j, synonym in enumerate(synonyms):
            synonym_text = synonym['text']
            synonym_text = style(synonym_text, 'synonym')
            synonyms_texts.append(synonym_text)
        synonyms_text = ' | '.join(synonyms_texts)
    else:
        #print('not found synonyms')
        pass
    return synonyms_text

def make_sense_text(i, sense, level):
    sense_texts = []
    sense_text = ''

    pronunciations_text = ''
    notes_text = ''
    notes_texts_after = []

    regions_text = ''
    registers_text = ''
    domainClasses_text = ''
    domains_text = ''
    semanticClasses_text = ''

    definitions_text = ''

    # special words in example
    constructions_texts = []
    variantForms_texts = []
    bold_texts_in_examples = []

    examples_text = ''

    crossReferenceMarkers_text = ''
    synonyms_text = ''

    pronunciations_text = make_pronunciations_text(sense)
    notes_text = make_note_text_pre(sense, block_note_types)
    notes_texts_after = make_note_texts_after(sense, block_note_types)

    regions_text = make_regions_text(sense)
    registers_text = make_registers_text(sense)
    domainClasses_text = make_domainClasses_text(sense)
    domains_text = make_domains_text(sense)
    semanticClasses_text = make_semanticClasses_text(sense)

    definitions_text = make_definitions_text(sense)

    constructions_texts = make_constructions_texts(sense)
    variantForms_texts = make_variantForms_texts(sense)
    bold_texts_in_examples.extend(constructions_texts)
    bold_texts_in_examples.extend(variantForms_texts)
    bold_texts_in_examples = set(bold_texts_in_examples)
    examples_text = make_examples_text(sense, bold_texts_in_examples)

    crossReferenceMarkers_text = make_crossReferenceMarkers_text(sense)
    synonyms_text = make_synonyms_text(sense)

    sense_number = str(i + 1)
    sense_spacer_number = indent_digit - len(sense_number) - 1
    if sense_spacer_number < 0:
        sense_spacer_number = 0
    #print(sense_spacer_number)

    sense_body = ''
    sense_body_pre_list = []
    sense_body_pre = ''

    sense_body_pre_list = [pronunciations_text, notes_text, regions_text, \
                          domainClasses_text, domains_text, \
                          semanticClasses_text, registers_text]
#https://stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings
#https://stackoverflow.com/questions/7961363/removing-duplicates-in-lists
    sense_body_pre_list = list(filter(None, sense_body_pre_list))
    sense_body_pre_list = list(dict.fromkeys(sense_body_pre_list))
    sense_body_pre = ' '.join(sense_body_pre_list).strip()

    if sense_body_pre == '':
        pass
    else:
        sense_body = sense_body_pre

    if definitions_text == '':
        pass
    elif sense_body == '':
        sense_body = definitions_text
    else:
        sense_body += ' ' + definitions_text

    if crossReferenceMarkers_text == '':
        pass
    elif sense_body == '':
        sense_body = crossReferenceMarkers_text
    else:
        sense_body += ' ' + crossReferenceMarkers_text

    if examples_text == '':
        pass
    elif sense_body == '':
        sense_body = examples_text
    else:
        sense_body += ': ' + examples_text

    if len(sense_body) > 0:
        if is_terminated(sense_body):
            pass
        else:
            sense_body += '.'

    sense_foot = ''
    sense_foots = []

    if notes_texts_after:
        sense_foots.extend(notes_texts_after)

    if synonyms_text:
        synonyms_title = style('Synonyms', 'title_inline')
        synonyms_body = synonyms_text
        synonyms_text = synonyms_title + ': ' + \
                         synonyms_body
        sense_foots.append(synonyms_text)

    if (sense_body == '' and sense_foots == []):
        pass
    else:
        if (level == 1):
            sense_texts = {'initial':sense_number + '.' + \
                           ' '*sense_spacer_number, \
                           'body':sense_body, 'foot':sense_foots}
        elif (level == 2):
            sense_texts = {'initial':sense_number + ')' + \
                           ' '*sense_spacer_number, \
                           'body':sense_body, 'foot':sense_foots}
    return sense_texts

def get_grammaticalFeatures(obj):
    grammaticalFeatures_texts = []
    if 'grammaticalFeatures' in obj:
        grammaticalFeatures = obj['grammaticalFeatures']
        for i, grammaticalFeature in enumerate(grammaticalFeatures):
            grammaticalFeatures_texts.append(grammaticalFeature['text'])
    else:
        pass
    #print(grammaticalFeatures_texts)
    return grammaticalFeatures_texts

def make_grammatical_text(entry):
    grammaticalFeatures_texts = []
    grammaticalFeatures_text = ''
    if 'grammaticalFeatures' in entry:
        grammaticalFeatures = entry['grammaticalFeatures']
        for i, grammaticalFeature in enumerate(grammaticalFeatures):
            if (grammaticalFeature['type'] == 'Subcategorization'):
                grammaticalFeature_text = style('[' + \
                                        grammaticalFeature['text'].lower() + \
                                        ']', 'note_inline')
                grammaticalFeatures_texts.append(grammaticalFeature_text)
            else :
                grammaticalFeature_text = style('(' + \
                                        grammaticalFeature['text'] + ')', \
                                        'note_inline')
                grammaticalFeatures_texts.append(grammaticalFeature_text)
        grammaticalFeatures_text = ', '.join(grammaticalFeatures_texts)
    else:
        #print('not found grammaticalFeatures')
        pass
    return grammaticalFeatures_text

def get_order_of_grammatical_features(grammaticalFeature):
    order = ['first', 'second', 'third', \
             'singular', 'plural', \
             'present', 'past', \
             'present participle', 'past participle', \
             'subjunctive']
    if grammaticalFeature in order:
        return order.index(grammaticalFeature)
    else:
        return 0

def make_grammatical_text_in_inflectedForm(inflection, \
                                           grammaticalFeatures_to_omit):
    grammaticalFeatures_texts = []
    grammaticalFeatures_text = ''
    if 'grammaticalFeatures' in inflection:
        grammaticalFeatures = inflection['grammaticalFeatures']
        target_feature_types = ['Person', 'Number', 'Tense', \
                                'Non Finiteness', 'Mood']
        #refer to result of “be”
        grammaticalFeatures_texts = []
        for j, grammaticalFeature in enumerate(grammaticalFeatures):
            if (grammaticalFeature['type'] in target_feature_types):
                grammaticalFeature_text = grammaticalFeature['text'].lower()
                grammaticalFeatures_texts.append(grammaticalFeature_text)
            else:
                if grammaticalFeature['text'] in grammaticalFeatures_to_omit:
                    #omit grammatical features in lexical entry to
                    #avoid duplication
                    #print(grammaticalFeature['text'])
                    pass
                else:
                    #for unexpected type of grammatical features
                    grammaticalFeature_text = grammaticalFeature['text'].lower()
                    grammaticalFeatures_texts.append(grammaticalFeature_text)
        if (len(grammaticalFeatures_texts) > 0):
            grammaticalFeatures_texts.sort(key=lambda d: \
                                        get_order_of_grammatical_features(d))
            grammaticalFeatures_text = ' - '.join(grammaticalFeatures_texts)
        else:
            pass
    else:
        #print('not found grammaticalFeatures')
        pass
    return grammaticalFeatures_text

def set_playlist(pronunciation):
    if 'audioFile' in pronunciation:
        audioFile = pronunciation['audioFile']
        if (audioFile not in playlist):
            playlist.append(audioFile)
    else:
        #print('not found audioFile')
        pass

def make_dialects_text(obj):
    omit_list = ['American English']
    #omit_list = []
    dialects_texts = []
    dialects_text = ''
    if 'dialects' in obj:
        dialects = obj['dialects']
        for dialect in dialects:
            if (dialect not in omit_list):
                dialects_texts.append(dialect)
    if len(dialects_texts) > 0:
        dialects_text = style(' '.join(dialects_texts), 'dialects')
    return dialects_text

def make_pronunciations_text(obj):
    pronunciations_text = ''
    if 'pronunciations' in obj:
        pronunciations = obj['pronunciations']
        pronunciations_texts = []
        for j, pronunciation in enumerate(pronunciations):
            set_playlist(pronunciation)
            if (pronunciation['phoneticNotation'] == 'IPA'):
                pronunciation_text = ''
                dialects_text = make_dialects_text(pronunciation)
                if dialects_text:
                    pronunciation_text = dialects_text + ' ' + \
                                          pronunciation['phoneticSpelling']
                else:
                    pronunciation_text = pronunciation['phoneticSpelling']
                pronunciations_texts.append(pronunciation_text)
            else:
                pass
        if (len(pronunciations_texts) > 0):
            pronunciations_text = ', '.join(pronunciations_texts)
            pronunciations_text = '/' + pronunciations_text + '/'
        else:
            # If IPA pronunciations were not found search
            # respell pronunciations.
            for k, pronunciation in enumerate(pronunciations):
                if (pronunciation['phoneticNotation'] == 'respell'):
                    pronunciation_text = ''
                    dialects_text = make_dialects_text(pronunciation)
                    if dialects_text:
                        pronunciation_text = dialects_text + ' ' + \
                                              pronunciation['phoneticSpelling']
                    else:
                        pronunciation_text = pronunciation['phoneticSpelling']
                    pronunciations_texts.append(pronunciation_text)
                else:
                    pass
            if (len(pronunciations_texts) > 0):
                pronunciations_text = ', '.join(pronunciations_texts)
                pronunciations_text = '|' + pronunciations_text + '|'
                #pronunciations_text += '(respell)'
    else:
        #print('not found pronunciations')
        pass
    return pronunciations_text

def make_inflection_text(entry, grammaticalFeatures_in_lexicalEntry):
    inflections_texts = []
    inflections_text = ''
    if 'inflections' in entry:
        inflections = entry['inflections']
        for i, inflection in enumerate(inflections):
            inflection_texts = []
            inflection_text = ''
            grammaticalFeatures_text = \
                make_grammatical_text_in_inflectedForm(inflection, \
                                            grammaticalFeatures_in_lexicalEntry)
            if (grammaticalFeatures_text):
                inflection_texts.append(grammaticalFeatures_text)
            regions_text = \
                make_regions_text(inflection)
            if (regions_text):
                inflection_texts.append(regions_text)
            inflection_texts.append(style(inflection['inflectedForm'], \
                                    'inflected_form'))
            pronunciations_text = \
                make_pronunciations_text(inflection)
            if pronunciations_text:
                inflection_texts.append(pronunciations_text)

            inflection_text = ' '.join(inflection_texts)
            inflections_texts.append(inflection_text)
        if (len(inflections_texts) > 0):
            #print(inflections_texts)
            inflections_text = '(' + '; '.join(inflections_texts) + ')'
    else:
        #print('not found inflections')
        pass
    return inflections_text

def make_derivativeOf_text(entry):
    derivativeOf_texts = []
    derivativeOf_text = ''
    if 'derivativeOf' in entry:
        derivativeOfList = entry['derivativeOf']
        for i, derivativeOf in enumerate(derivativeOfList):
            derivativeOf_text = style(derivativeOf['text'], 'reference')
            derivativeOf_texts.append(derivativeOf_text)
        derivativeOf_text = '(' + 'derivative of ' + \
            ', '.join(derivativeOf_texts) + ')'
    else:
        #print('not found derivativeOf')
        pass
    return derivativeOf_text

def make_phrases_text(entry, bullet):
    phrases_texts = []
    phrases_text = ''
    if 'phrases' in entry:
        phrases = entry['phrases']
        for i, phrase in enumerate(phrases):
            phraseText = phrase['text']
            phraseText = style(phraseText, 'reference')
            phrases_texts.append(phraseText)
        phrases_body = bullet + ' | '.join(phrases_texts)
        phrases_body = wrapper_0.fill(phrases_body)
        phrases_text = phrases_body
    else:
        #print('not found phrases')
        pass
    return phrases_text

def make_phrasalVerbs_text(entry, bullet):
    phrasalVerbs_texts = []
    phrasalVerbs_text = ''
    if 'phrasalVerbs' in entry:
        phrasalVerbs = entry['phrasalVerbs']
        for i, phrasalVerb in enumerate(phrasalVerbs):
            phrasalVerbText = phrasalVerb['text']
            phrasalVerbText = style(phrasalVerbText, 'reference')
            phrasalVerbs_texts.append(phrasalVerbText)
        phrasalVerbs_body = bullet + ' | '.join(phrasalVerbs_texts)
        phrasalVerbs_body = wrapper_0.fill(phrasalVerbs_body)
        phrasalVerbs_text = phrasalVerbs_body
    else:
        #print('not found phrasalVerbs')
        pass
    return phrasalVerbs_text

def make_compounds_text(entry, bullet):
    compounds_texts = []
    compounds_text = ''
    if 'compounds' in entry:
        compounds = entry['compounds']
        for i, compound in enumerate(compounds):
            compound_text = compound['text']
            compound_text = style(compound_text, 'reference')
            compounds_texts.append(compound_text)
        compounds_body = bullet + ' | '.join(compounds_texts)
        compounds_body = wrapper_0.fill(compounds_body)
        compounds_text = compounds_body
    else:
        #print('not found compounds')
        pass
    return compounds_text

def make_derivatives_text(entry, bullet):
    derivatives_texts = []
    derivatives_text = ''
    if 'derivatives' in entry:
        derivatives = entry['derivatives']
        for i, derivative in enumerate(derivatives):
            derivative_text = derivative['text']
            derivative_text = style(derivative_text, 'reference')
            derivatives_texts.append(derivative_text)
        derivatives_body = bullet + ' | '.join(derivatives_texts)
        derivatives_body = wrapper_0.fill(derivatives_body)
        derivatives_text = derivatives_body
    else:
        #print('not found derivatives')
        pass
    return derivatives_text

def make_etymologies_text(entry):
    etymologies_texts = []
    etymologies_text = ''
    if 'etymologies' in entry:
        etymologies = entry['etymologies']
        for i, etymology in enumerate(etymologies):
            if (is_terminated(etymology)):
                etymology += '.'
            etymologies_texts.append(etymology)
        etymologies_body = '\n'.join(etymologies_texts)
        etymologies_body = wrapper_0.fill(etymologies_body)
        etymologies_text = etymologies_body
    else:
        #print('not found etymologies')
        pass
    return etymologies_text

#https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/

def play_with_mpg123(audioFile, duration):
    command = 'curl -s %s | mpg123 -q -' % (audioFile)
    #print_notation(command)
    try:
        subprocess.call(command, shell=True)
        sleep(duration)
    except:
        print_notation('error on playing')

def play_with_playaudio_local(audioFile, duration, base_path):
    #for termux on android
    played = False
    temp_path = base_path + '/temp'
    check_dirs(temp_path, 'Temporary directory has been made.')
    filename = temp_path + '/local.mp3'
    with open(filename, 'wb') as f:
        f.write(audioFile)
    try:
        command = 'play-audio %s' % (filename)
        subprocess.call(command, shell=True)
        sleep(duration)
        played = True
    except:
        print_notation('error on playing')
        #import traceback
        #traceback.print_exc()
        #print(sys.exc_info())
        played = False
    return played

def play_with_playsound_local(audioFile, duration, base_path):
    temp_path = base_path + '/temp'
    check_dirs(temp_path, 'Temporary directory has been made.')
    filename = temp_path + '/local.mp3'
    with open(filename, 'wb') as f:
        f.write(audioFile)
    try:
        playsound(filename)
        sleep(duration)
    except:
        print_notation('error on playing')
        #import traceback
        #traceback.print_exc()
        #print(sys.exc_info())

def play_with_playsound(audioFile, duration):
    try:
        playsound(audioFile)
        #dulation is implemented in playsound
        #sleep(duration)
        return True
    except:
        print_notation('error on playing')
        #import traceback
        #traceback.print_exc()
        #print(sys.exc_info())
        return False

def play_with_pythonVLC(audioFile, duration):
    #not work properly
    import vlc
    try:
        p = vlc.MediaPlayer(audioFile)
        p.play()
        #sleep(1)
        while p.is_playing():
            sleep(duration)
    except:
        print_notation('error on playing')

def play_with_VLC(audioFile):
    #for macOS using vlc.app
    try:
        os.system('open -ga vlc %s' % audioFile)
    except:
        print_notation('error on playing')

def play_audioFiles(audioFiles, base_path):
    print('Playing...')
    files_length = len(audioFiles)
    for i, audioFile in enumerate(audioFiles):
        duration = 0
        audio_info = ''
        r = requests.get(audioFile)
        status = r.status_code
        if status == 200:
            played = False
            try:
                byte_obj = io.BytesIO(r.content)
                audio = MP3(byte_obj)
                audio_length = audio.info.length
                if i + 1 < files_length:
                    # If current audio is not last one.
                    duration = math.ceil(audio_length)
                #print('duration: ' + str(duration))
                length_approx = round(audio_length, 2)
                audio_info = ' (approx. ' + str(length_approx) + ' sec.)'
            except:
                audio_info = ' (no file information)'
            if sys.platform.startswith('darwin'):
                #for macOS
                #play_with_VLC(audioFile)
                #play_with_playsound_local(r.content, duration, base_path)
                #play_with_mpg123(audioFile, duration)
                #play_with_pythonVLC(audio, duration)
                played = play_with_playsound(audioFile, duration)
                duration = 0
            elif sys.platform.startswith('linux'):
                played = play_with_playsound(audioFile, duration)
                if (played):
                    pass
                else:
                    #for termux on android
                    played = play_with_playaudio_local(r.content, duration, \
                                                       base_path)
                duration = 0
            else:
                #play_with_pythonVLC(audioFile, duration)
                played = play_with_playsound(audioFile, duration)
                duration = 0
            if (played):
                pass
            else:
                print_notation('error on playing')
        else:
            audio_info = ' (status code: ' + str(status) + ')'
        audio_info = audioFile + audio_info
        print(audio_info)
        sleep(duration)

def make_word_numbers(results):
    word_numbers = []
    if (len(results) == 1):
        word_numbers.append('')
    else:
        word_previous = ''
        sub_word_first = results[0]['word']
        sub_word_number = 0
        for i, result in enumerate(results):
            word = result['word']
            if (i == 0):
                word_numbers.append('')
                word_previous = word
                sub_word_first = word
                sub_word_number = 1
            else:
                if (word == sub_word_first):
                    if (sub_word_number == 1):
                        word_numbers[i-1] = str(sub_word_number)
                        #print(word_numbers[i-1])
                    sub_word_number = sub_word_number + 1
                    word_numbers.append(str(sub_word_number))
                else:
                    sub_word_first = word
                    sub_word_number = 1
                    word_numbers.append('')
    return word_numbers

def print_sense_texts(sense_texts):
    if (sense_texts):
        sense_initial = sense_texts['initial']
        sense_body = sense_texts['body']
        sense_foots = sense_texts['foot']
        sense_initial_indent = wrapper_1.initial_indent
        wrapper_1.initial_indent = sense_initial_indent + sense_initial
        sense_body_wrapped = wrapper_1.fill(sense_body)
        if ('\n' in sense_body_wrapped and \
            re.search(r'(\033\[\d+m)', sense_body_wrapped)):
            sense_body_wrapped = \
                remove_color_of_indent_space(sense_body_wrapped)
        print(sense_body_wrapped)
        wrapper_1.initial_indent = sense_initial_indent
        if sense_foots:
            for sense_foot in sense_foots:
                sense_foot = ' '*indent_digit + \
                            sense_foot
                sense_foot_wrapped = wrapper_1.fill(sense_foot)
                if ('\n' in sense_foot_wrapped and \
                    re.search(r'(\033\[\d+m)', sense_foot_wrapped)):
                    #print("'\\n' in sense_foot_wrapped")
                    sense_foot_wrapped = \
                        remove_color_of_indent_space(sense_foot_wrapped)
                sense_foot_wrapped = \
                    fill_end_of_line(sense_foot_wrapped, \
                                  ' ', columns_width)
                print(sense_foot_wrapped)


def print_subsenses(sense):
    if 'subsenses' in sense:
        subsenses = sense['subsenses']
        for m, subsense in enumerate(subsenses):
            subsense_texts = make_sense_text(m, subsense, 2)
            if (subsense_texts):
                subsense_initial = subsense_texts['initial']
                subsense_body = subsense_texts['body']
                subsense_foots = subsense_texts['foot']
                subsense_initial_indent = wrapper_2.initial_indent
                wrapper_2.initial_indent = \
                    subsense_initial_indent + subsense_initial
                subsense_body_wrapped = wrapper_2.fill(subsense_body)
                if ('\n' in subsense_body_wrapped and \
                    re.search(r'(\033\[\d+m)', subsense_body_wrapped)):
                    subsense_body_wrapped = \
                        remove_color_of_indent_space(subsense_body_wrapped)
                print(subsense_body_wrapped)
                wrapper_2.initial_indent = subsense_initial_indent
                if subsense_foots:
                    for subsense_foot in subsense_foots:
                        subsense_foot = ' '*indent_digit + \
                                       subsense_foot
                        subsense_foot_wrapped = \
                            wrapper_2.fill(subsense_foot)
                        if ('\n' in subsense_foot_wrapped and \
                            re.search(r'(\033\[\d+m)', \
                                      subsense_foot_wrapped)):
                            subsense_foot_wrapped = \
                                remove_color_of_indent_space(\
                                    subsense_foot_wrapped)
                        subsense_foot_wrapped = \
                            fill_end_of_line(subsense_foot_wrapped, \
                                          ' ', columns_width)
                        print(subsense_foot_wrapped)
    else:
        #print('not found subsenses')
        pass

def camel_to_title(text):
    upper = re.compile(r'([A-Z])')
    text = upper.sub(' ' + r'\1', text)
    text = text.strip().title()
    return text

def print_result_foot_notes(result_foot_notes):
    single_title_type = ['phrases', 'phrasalVerbs', 'compounds', \
                         'derivatives', 'etymologies',
                        ]
    multi_title_type  = ['notes',]
    # about multi_title_type, refer to “well” entry
    result_foot_notes_texts = []
    for note_name in single_title_type:
        if len(result_foot_notes[note_name]) > 0:
            notes = result_foot_notes[note_name]
            notes_body = '\n'.join(notes)
            notes_title = camel_to_title(note_name)
            notes_title = style(notes_title, 'title')
            notes_text = notes_title + '\n' + notes_body
            result_foot_notes_texts.append(notes_text)
    for note_name in multi_title_type:
        if len(result_foot_notes[note_name]) > 0:
            notes = result_foot_notes[note_name]
            for note in notes:
                note_body = note
                note_title = camel_to_title(note_name)
                note_title = style(note_title, 'title')
                note_text = note_title + '\n' + note_body
                result_foot_notes_texts.append(note_text)

    if (len(result_foot_notes_texts) > 0):
        result_foot_notes_text = '\n'.join(result_foot_notes_texts)
        print(result_foot_notes_text)

def print_results():
    word = check_args()

    word_id = word #'example'
    word_id_lower = word_id.lower()

    base_path = os.path.dirname(os.path.realpath(__file__))
    result_dir = base_path + "/" + language + "/results/"

    check_dirs(result_dir, 'Results directory has been made.')
    result_files_dir = result_dir + word_id_lower + '.json'

    previous_result = False

    previous_pronunciation = ""

    try:
        with open(result_files_dir, mode='r') as f:
            r = f.read()
            r_json = json.loads(r)
            if 'results' in r_json:
                results = r_json['results']
                previous_result = True
                print_notation('Results in cache files')
            else:
                print_notation('No results in cache files')
                pass
    except:
        print_notation('No cache files')
        pass

    if (previous_result == False):
        url = 'https://od-api.oxforddictionaries.com/api/v2/' + endpoint \
                + '/' + language + '/' + word_id_lower + filters
        r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})
        try:
            r_json = r.json()
        except:
            print('error on getting r.json()')
            print('r.status_code: ' + str(r.status_code))
            quit()

        if 'results' in r_json:
            results = r_json['results']
            write_result(result_files_dir, r_json)
        else:
            print('No results')
            write_result(result_files_dir, r_json)
            quit()

    #results.sort(key=lambda x: x['word'].swapcase()) # lower, UPPER
    results.sort(key=lambda x: x['word']) # UPPER, lower
    word_numbers = make_word_numbers(results)
    #print(word_numbers)

    for i, result in enumerate(results):
        print('')
        word = result['word']
        word_str = word
        word_num = word_numbers[i]
        if (len(results) == 1):
            word_str = style(word_str, 'word')
        else:
            if (word_num == ''):
                word_str = style(word_str, 'word')
            else:
                word_num_sup = word_num.translate(trans_sup)
                word_str = style(word_str + word_num_sup, 'word')
        print(word_str)

        result_foot_notes = {'phrases':[], 'phrasalVerbs':[], \
                             'compounds':[], 'derivatives':[], \
                             'etymologies':[], 'notes':[]}

        lexicalEntries = result['lexicalEntries']
        #print(len(lexicalEntries))
        for j, lexicalEntry in enumerate(lexicalEntries):
            # Make lexicalEntry_informations
            lexicalEntry_informations = []
            lexicalCategory = lexicalEntry['lexicalCategory']['text']
            #print(lexicalCategory)
            lexicalCategory_text = style(lexicalCategory.lower(), 'note_inline')
            if (lexicalCategory_text == ''):
                pass
            else:
                lexicalEntry_informations.append(lexicalCategory_text)

            grammaticalFeatures_in_lexicalEntry = []
            grammaticalFeatures_in_lexicalEntry = \
                                        get_grammaticalFeatures(lexicalEntry)
            #print(grammaticalFeatures_in_lexicalEntry)

            grammaticalFeatures_text = make_grammatical_text(lexicalEntry)
            if (grammaticalFeatures_text == ''):
                pass
            else:
                lexicalEntry_informations.append(grammaticalFeatures_text)

            inflections_text = make_inflection_text(lexicalEntry, \
                                 grammaticalFeatures_in_lexicalEntry)
            if (inflections_text == ''):
                pass
            else:
                lexicalEntry_informations.append(inflections_text)

            derivativeOf_text = make_derivativeOf_text(lexicalEntry)
            if (derivativeOf_text == ''):
                pass
            else:
                lexicalEntry_informations.append(derivativeOf_text)

            lexicalEntry_informations_text = ' '.join(lexicalEntry_informations)
            lexicalEntry_informations_text = wrapper_0.fill(
                                                lexicalEntry_informations_text)
            print(lexicalEntry_informations_text)

            # Make foot notes
            phrases_text = make_phrases_text(lexicalEntry, ref_bullet)
            if (phrases_text == ''):
                pass
            elif phrases_text not in result_foot_notes['phrases']:
                result_foot_notes['phrases'].append(phrases_text)

            phrasalVerbs_text = make_phrasalVerbs_text(lexicalEntry, ref_bullet)
            if (phrasalVerbs_text == ''):
                pass
            elif phrasalVerbs_text not in result_foot_notes['phrasalVerbs']:
                result_foot_notes['phrasalVerbs'].append(phrasalVerbs_text)

            derivatives_text = make_derivatives_text(lexicalEntry, ref_bullet)
            if (derivatives_text == ''):
                pass
            elif derivatives_text not in result_foot_notes['derivatives']:
                result_foot_notes['derivatives'].append(derivatives_text)

            compounds_text = make_compounds_text(lexicalEntry, ref_bullet)
            if (compounds_text == ''):
                pass
            elif compounds_text not in result_foot_notes['compounds']:
                result_foot_notes['compounds'].append(compounds_text)

            # Make entries
            entries = lexicalEntry['entries']
            #print(len(entries))
            for k, entry in enumerate(entries):
                pronunciations_text = \
                    make_pronunciations_text(entry)
                if pronunciations_text:
                    if pronunciations_text != previous_pronunciation:
                        print(pronunciations_text)
                    previous_pronunciation = pronunciations_text
                else:
                    #print('not found pronunciations')
                    pass

                sub_head_texts = []
                sub_head_text = ''

                grammaticalFeatures_in_entry = []
                grammaticalFeatures_in_entry = get_grammaticalFeatures(entry)
                #print(grammaticalFeatures_in_entry)

                grammaticalFeatures_text = make_grammatical_text(entry)
                if (grammaticalFeatures_text):
                    sub_head_texts.append(grammaticalFeatures_text)
                inflections_text = make_inflection_text(entry, \
                                                grammaticalFeatures_in_entry)
                if (inflections_text):
                    sub_head_texts.append(inflections_text)
                sub_head_text = ' '.join(sub_head_texts)
                if (sub_head_text):
                    sub_head_text = wrapper_0.fill(sub_head_text)
                    print(sub_head_text)

                senses = entry['senses']
                if (len(senses) > 0):
                    for l, sense in enumerate(senses):
                        sense_texts = make_sense_text(l, sense, 1)
                        print_sense_texts(sense_texts)
                        print_subsenses(sense)

                etymologies_text = make_etymologies_text(entry)
                if (etymologies_text):
                    result_foot_notes['etymologies'].append(etymologies_text)
                    #print(etymologies_text)

                notes_texts_after = make_note_texts_after(entry, \
                                                            block_note_types)
                if (notes_texts_after):
                    for notes_text_after in notes_texts_after:
                        notes_text_after = wrapper_0.fill(notes_text_after)
                        notes_text_after = fill_end_of_line(notes_text_after, \
                                                            ' ', columns_width)
                        if (notes_text_after not in result_foot_notes['notes']):
                            result_foot_notes['notes'].append(notes_text_after)
                            #print(notes_text_after)

        print_result_foot_notes(result_foot_notes)

    print('')

    if len(playlist):
        play_audioFiles(playlist, base_path)

if __name__ == '__main__':
    print_results()

