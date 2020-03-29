'''
Purpose: quantitative song analysis

Explorations:
- word/syllable count
- POS analysis
- rhyme
  - sequence frequencies
  - Shared points
  - common sounds
- shared vocab
  - percentage of words, look at what's shared
'''

#imports
import os
import csv
import string
from itertools import islice

#some nltk things
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.tag import StanfordPOSTagger
#global setup - not great practice but honestly easier than excessive parameter passing


# set up the french tagger since it's not built into nltk like the english one
jar = './resources/postagger/stanford-postagger-3.9.2.jar'
fr_model = './resources/postagger/french.tagger'
fr_tagger = StanfordPOSTagger(fr_model, jar, encoding='utf8' )

#global vars
vowels = 'aeiouyéèàêùëï'
ipa_vowels = 'iyuwIYoʊeɛɝθaɔəɑæɔ̃ɑ̃ɥ'
punc_table = str.maketrans('', '', '!?,."«»():;')
en_stop = set(stopwords.words('english'))


#pronunciation dictionaries for syllable counts/rhyming
#need external resources so that both languages are in the same format - in this case, ipa
fr_dict = {}
with open('./resources/fr.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        try:
            fr_dict[row[0]] = row[1].replace(" ","")
        except Exception:
            continue

en_dict = {}
with open('./resources/cmudict.ipa', newline='', encoding='utf-8') as f:
    for line in f.readlines():
        l = line.split('\t')
        en_dict[l[0]] = l[1].replace(" ","").rstrip()

#finds the longest rhyming fragment
#a rhyme must include at minimum a vowel
#semi vowels make it a bit iffy but it works pretty well
def soundMatch(phon1, phon2):
    count = 0
    has_vowel = False
    for x in range(min(len(phon1), len(phon2))):
        if(phon1[len(phon1)-1-x]==phon2[len(phon2)-1-x]):
            count +=1
            if(phon1[len(phon1)-1-x] in ipa_vowels):
                has_vowel = True
        else:
            break
    if(has_vowel and count > 0):
        return phon1[(-1*count):]
    return None

#create a rhyme scheme string
def rhymeScheme(lines, lang_dict):
    ends = [y[len(y)-1] for y in [x.replace("-", " ").replace("’", " ").replace("'", " ").translate(punc_table).split() for x in lines]]
    sounds = {}
    labels = ""
    letter = 64
    for l in ends:
        try:
            phon = lang_dict[l.lower()]
        except KeyError:
            phon =  None
        if(phon):
            match = None
            key = None
            for l in list(sounds.keys()):
                match = soundMatch(phon, sounds[l])
                if(match):
                    break
            if(match):
                sounds[l] = match
                labels += l
            else:
                letter += 1
                #skip over non letters to lowercase
                if letter == 91:
                    letter = 97
                labels += chr(letter)
                sounds[chr(letter)] = phon
        else:
            labels+="*"
    label_dict = {}
    for c in labels:
        if label_dict.get(c):
            label_dict[c]+=1
        else:
            label_dict[c] = 1

    return [labels, sounds, sorted(label_dict.items(), key=lambda kv: kv[1], reverse=True)]

def schemeCounter(scheme_str):
    abba_count = 0
    abab_count = 0
    runs = []

    i=0
    while(i< len(scheme_str)-3):
      if(scheme_str[i]==scheme_str[i+3] and scheme_str[i+1]==scheme_str[i+2] and scheme_str[i+1]!=scheme_str[i]):
        abba_count +=1
        i += 4
      elif(scheme_str[i]==scheme_str[i+2] and scheme_str[i+1]==scheme_str[i+3] and scheme_str[i+1]!=scheme_str[i]):
        abab_count+=1
        i+= 4
      else:
        i+=1

    run = 1
    for y in range(len(scheme_str)):
        if(y==len(scheme_str)-1 or scheme_str[y]!=scheme_str[y+1]):
            runs.append(run)
            run =1
        else:
            run +=1
    return [abba_count, abab_count, max(runs)]

def rhymes():
    cols = ["song", "en_scheme", "fr_scheme", "qc_scheme", "en_abab", "fr_abab", "qc_abab", "en_abba", "fr_abba", "qc_abba", "en_run", "fr_run", "qc_run", "en_common", "en_freq", "fr_common", "fr_freq", "qc_common", "qc_freq", "en_diff", "fr_diff", "qc_diff"]
    writer = csv.DictWriter(open("./results/rhymes.csv", 'w'), fieldnames=cols)
    writer.writeheader()

    for folder in os.listdir('./songs'):

        #get the data - yes this is inefficient
        prefix = "./songs/" + folder + "/"
        en_text = open(prefix + "en.txt", 'r')
        en_lines = en_text.readlines()
        fr_text = open(prefix + "fr.txt", 'r')
        fr_lines = fr_text.readlines()
        qc_text = open(prefix + "qc.txt", 'r')
        qc_lines = qc_text.readlines()

        #do the actual processing
        res = dict.fromkeys(cols)
        res["song"] = folder.replace("_", " ")

        #get the scheme info and sounds dictionnaries
        en_data = rhymeScheme(en_lines, en_dict)
        fr_data = rhymeScheme(fr_lines, fr_dict)
        qc_data = rhymeScheme(qc_lines, fr_dict)

        #schemes
        res["en_scheme"] = en_data[0]
        res["fr_scheme"] = fr_data[0]
        res["qc_scheme"] = qc_data[0]

        #sound stats
        res["en_common"] = en_data[1][en_data[2][0][0]]
        res["en_freq"] = en_data[2][0][1]/len(en_lines)
        res["en_diff"] = len(en_data[2])
        res["fr_common"] = fr_data[1][fr_data[2][0][0]]
        res["fr_freq"] = fr_data[2][0][1]/len(fr_lines)
        res["fr_diff"] = len(fr_data[2])
        res["qc_common"] = qc_data[1][qc_data[2][0][0]]
        res["qc_freq"] = qc_data[2][0][1]/len(qc_lines)
        res["qc_diff"] = len(qc_data[2])

        #counts
        en_counts = schemeCounter(en_data[0])
        fr_counts = schemeCounter(fr_data[0])
        qc_counts = schemeCounter(qc_data[0])

        res["en_abba"] = en_counts[0]
        res["en_abab"] = en_counts[1]
        res["en_run"] = en_counts[2]
        res["fr_abba"] = fr_counts[0]
        res["fr_abab"] = fr_counts[1]
        res["fr_run"] = fr_counts[2]
        res["qc_abba"] = qc_counts[0]
        res["qc_abab"] = qc_counts[1]
        res["qc_run"] = qc_counts[2]

        writer.writerow(res)

        en_text.close()
        fr_text.close()
        qc_text.close()



#adjusted from https://datascience.stackexchange.com/questions/23376/how-to-get-the-number-of-syllables-in-a-word
#evidently there are some language issues but it seems to work for the most part
#example of bad: "somehow"
def syllables(word):
    count = 0
    if word[0] in vowels:
        count +=1
    for index in range(1,len(word)):
        if word[index] in vowels and word[index-1] not in vowels:
            count +=1
    if word.endswith('e'):
        count -= 1
    if word.endswith('le'):
        count+=1
    if count == 0:
        count +=1
    return count

#deals with the edge case of words ending in 'bre', 'cre', 'dre' etc.
def syllables_fr(word):
    s = syllables(word)
    if(word.endswith('re') and (word[len(word)-3] not in vowels)) :
        s+=1
    return s


def words_and_syllables():
    #columns: song, then words/syllables/wpl/spl for each type (en, fr, qc)
    cols = ["song", "lines","en_w", "fr_w", "qc_w", "en_s", "fr_s", "qc_s", "en_spl", "fr_spl", "qc_spl","en_spw", "fr_spw", "qc_spw",  "en_wpl", "fr_wpl", "qc_wpl"]
    writer = csv.DictWriter(open("./results/counts.csv", 'w'), fieldnames=cols)
    writer.writeheader()
    for folder in os.listdir('./songs'):

        #get the data - yes this is inefficient
        prefix = "./songs/" + folder + "/"
        en_text = open(prefix + "en.txt", 'r')
        en_lines = en_text.readlines()
        fr_text = open(prefix + "fr.txt", 'r')
        fr_lines = fr_text.readlines()
        qc_text = open(prefix + "qc.txt", 'r')
        qc_lines = qc_text.readlines()

        #do the actual processing
        res = dict.fromkeys(cols, 0)
        res["song"] = folder.replace("_", " ")
        lines = len(en_lines)
        res["lines"] = lines
        for i in range(lines):
            #use split for tokenization because I don't want to count contractions as separate words (because they're not being pronounced as such)
            fr_words = fr_lines[i].lower().split()
            en_words = en_lines[i].lower().split()
            qc_words = qc_lines[i].lower().split()
            res["fr_w"] += len(fr_words)
            res["en_w"] += len(en_words)
            res["qc_w"] += len(qc_words)
            res["en_s"] += sum([syllables(x) for x in en_words ])
            res["fr_s"] += sum([syllables_fr(x) for x in fr_words ])
            res["qc_s"] += sum([syllables_fr(x) for x in qc_words ])
        res["en_wpl"] = res["en_w"]/lines
        res["fr_wpl"] = res["fr_w"]/lines
        res["qc_wpl"] = res["qc_w"]/lines
        res["en_spl"] = res["en_s"]/lines
        res["fr_spl"] = res["fr_s"]/lines
        res["qc_spl"] = res["qc_s"]/lines
        res["en_spw"] = res["en_s"]/res["en_w"]
        res["fr_spw"] = res["fr_s"]/res["fr_w"]
        res["qc_spw"] = res["qc_s"]/res["qc_w"]

        writer.writerow(res)
        #make sure to close the files
        en_text.close()
        fr_text.close()
        qc_text.close()

#english tagset: https://www.clips.uantwerpen.be/pages/mbsp-tags (penn treebank)
#french tagset: http://www.linguist.univ-paris-diderot.fr/~mcandito/Publications/crabbecandi-taln2008-final.pdf (adapted from french treebank)
def mapPos(pos):
    if(pos.startswith("ADJ") or pos.startswith('JJ')):
        return "adjectifs"
    elif(pos.startswith('V')):
        return "verbes"
    elif(pos.startswith('N')):
        return "noms"
    elif(pos.startswith('PR')):
        return "pronoms"
    elif(pos=='CC' or pos=='CS'):
        return 'conjonctions'
    elif(('RB' in pos) or pos.startswith('ADV')):
        return "adverbes"
    elif(pos=='P' or pos=='IN'):
        return "prépositions"
    #catch all for fine grained tags or things we don't care about
    return "autre"

def posTag(text, lang):
    res_dict = {}
    for line in text:
        words = pos_tag(word_tokenize(line.translate(punc_table))) if lang=='en' else fr_tagger.tag(line.translate(punc_table).split())
        for w in words:
            pos = mapPos(w[1])
            if(res_dict.get(pos)):
                res_dict[pos] +=1
            else:
                res_dict[pos] = 1
    return res_dict

#part of speech distribution
def pos():
    pos = ['autre', 'adjectifs', 'verbes', 'prépositions', 'noms', 'adverbes', 'conjonctions', 'pronoms']
    cols = ["song"]
    types = ["en", "fr", "qc"]
    for type in types:
        cols.extend([x + "_" + type for x in pos])
    writer = csv.DictWriter(open("./results/pos.csv", 'w'), fieldnames=cols)
    writer.writeheader()

    for folder in os.listdir('./songs'):

        #get the data - yes this is inefficient
        prefix = "./songs/" + folder + "/"
        en_text = open(prefix + "en.txt", 'r')
        fr_text = open(prefix + "fr.txt", 'r')
        qc_text = open(prefix + "qc.txt", 'r')
        lines = [en_text.readlines(),fr_text.readlines(), qc_text.readlines()]
        #do the actual processing
        res = dict.fromkeys(cols)
        for i in range(len(lines)):
            data = posTag(lines[i], types[i])
            words = sum(data.values())
            for item in pos:
                res[item + "_" + types[i]] = data[item]/words
        res = dict(sorted(res.items(), key=lambda kv: kv[0]))
        res["song"] = folder.replace("_", " ")
        writer.writerow(res)

        en_text.close()
        fr_text.close()
        qc_text.close()

def freq_vector(text):
    vector = {}
    for line in text:
        for word in line.translate(punc_table).lower().split():
            if word not in en_stop:
                if(vector.get(word)):
                    vector[word] +=1
                else:
                    vector[word] = 1
    return vector
#compare the vocabulary
#frankly this is better *not* done in csv format
#for now, just gonna use frequency vectors
def vocab():
    os.chdir("results")
    os.mkdir("content_comp")
    os.chdir("content_comp")
    for folder in os.listdir('../../songs'):
        outfile = open(folder+ ".txt", 'w')
        prefix = "../../songs/" + folder + "/"
        en_text = open(prefix + "en.txt", 'r')
        fr_text = open(prefix + "fr_trans.txt", 'r')
        qc_text = open(prefix + "qc_trans.txt", 'r')

        en_vocab = freq_vector(en_text.readlines())
        fr_vocab = freq_vector(fr_text.readlines())
        qc_vocab = freq_vector(qc_text.readlines())

        #most popular
        outfile.write("Top words in the original: {}\n".format( sorted(en_vocab.items(), key=lambda kv: kv[1], reverse=True)[:10]))
        outfile.write("Top words in the french translation: {}\n".format( sorted(fr_vocab.items(), key=lambda kv: kv[1], reverse=True)[:10]))
        outfile.write("Top words in the québecois translation: {}\n".format( sorted(qc_vocab.items(), key=lambda kv: kv[1], reverse=True)[:10]))

        #shared vocab en_fr, en_qc, fr_qc
        en_fr = [x for x in en_vocab.keys() if x in fr_vocab.keys()]
        en_qc = [x for x in en_vocab.keys() if x in qc_vocab.keys()]
        fr_qc = [x for x in fr_vocab.keys() if x in qc_vocab.keys()]

        outfile.write("\n\n\nShared words en_fr: %d\nPercent wrt english: %.4f\nPercent wrt french: %.4f" % (len(en_fr), len(en_fr)/len(en_vocab), len(en_fr)/len(fr_vocab)))
        outfile.write("\n\n\nShared words en_qc: %d\nPercent wrt english: %.4f\nPercent wrt québec0is: %.4f" % (len(en_qc), len(en_qc)/len(en_vocab), len(en_qc)/len(qc_vocab)))
        outfile.write("\n\n\nShared words fr_qc: %d\nPercent wrt french: %.4f\nPercent wrt québecois: %.4f" % (len(fr_qc), len(fr_qc)/len(fr_vocab), len(fr_qc)/len(qc_vocab)))





#opening and closing filestreams a bunch isn't necessarily efficient but it is less memory intense than reading everything into some sort of nested dictionary
def main():
    os.system("rm -rf results")
    os.mkdir("results")
    words_and_syllables()
    rhymes()
    pos()
    vocab()

main()
