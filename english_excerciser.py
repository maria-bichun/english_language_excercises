import spacy
import pandas as pd
import numpy as np
from spacy.lang.en import English
import random
import gensim.downloader as api
from pyinflect import getInflection

word_vectors = api.load('glove-wiki-gigaword-100')

sentzer = English()
sentzer.add_pipe('sentencizer')

nlp = spacy.load("en_core_web_sm")

class EnglishExcerciser():

  def __init__(self, text):
    """(self, str) -> (self)
    builds df out of a str text
    initiates an empty list of sentences already used in excercises (not to produce excercises based on the same sentences)
    """
    self.df = self.build_df(text)
    self.vocab_selection_options_to_df()
    self.verbs_to_df()
    self.be_to_df()
    self.prep_to_df()
    self.used_rows = []

  ###################
  # utils
  def get_pos(self, x):
    """(str) -> (str)
    returns part of speech. use for found similar words to filter parts of speech
    """
    words = nlp(x)
    for word in words:
      return spacy.explain(word.pos_)
    
  def get_num(self, x):
    """(str) -> (str)
    returns Sing or Plur
    """
    words = nlp(x)
    for word in words:
      return word.morph.get('Number')
    
  def get_form(self, x):
    """(str) -> (str)
    returns verb form
    """
    words = nlp(x)
    for word in words:
      return word.morph.get('VerbForm')

  ###################
  # functions
  def find_main_pos(self, row_number, pos):
    """(int, str) -> (str list, str list, int list) list
    finds only meaningful POS (noun, adv, adj, verb) by row number.
    returns list of all words of the given POS in the sentence, list of POS and list of indices,
    so that the resultng words could be found in the sentence
    """
    all_words = np.array([str(word).lower() for word in self.df['wordlist'][row_number]])
    values = np.array(self.df['pos'][row_number])
    sent = self.df['raw'][row_number]

    searchval = pos
    idx = np.where(values == searchval)[0]
    return([(all_words[i], values[i], [word for word in self.df['wordlist'][row_number]][i].i - sent.start) for i in sorted(idx) if str(all_words[i]).isalpha() and len(str(all_words[i])) > 1])

  def get_options(self, original_word, pos, num_options=2):   
      """(str, str, int) -> (str, list, float) tuple
      generates similar options out of the given word of a given part of speech.
      returns the original word, list of similar words with the original added and shuffled 
      along with the calculated quality so that different sets of similar words could be later compared and the best one chosen.
      """ 
      
      # A: find similar by word
      result = word_vectors.similar_by_word(original_word)
      a = {x[0] for x in result[:15]}

      # B: find similar using pairs
      pairs = [('good', 'bad')]
      result = []
      for pair in pairs:
        wordlist = word_vectors.most_similar(positive=[original_word, pair[0]], negative=pair[1])[:5]
        result.extend(wordlist)
      b = set([x[0] for x in result])
      total = a|b

      # filter
      if pos == 'noun':
        filtered = {word for word in total if pos in self.get_pos(word) and 'Sing' in self.get_num(word)}
      elif pos == 'verb':
        filtered = {word for word in total if pos in self.get_pos(word) and self.get_form(original_word) == self.get_form(word)}
      else: filtered = {word for word in total if pos == self.get_pos(word)}

      # find closest
      distances = {word: word_vectors.distance('girl', word) for word in filtered}
      dist_sorted = sorted(distances.items(), key=lambda x:x[1])

      # add original word and shuffle
      alts = [x[0] for x in dist_sorted[:num_options]]
      alts.append(original_word)
      random.shuffle(alts)
      quality = num_options + 1 - sum([x[1] for x in dist_sorted[:num_options]])
      return original_word, alts, quality

  def get_vocab_selection(self, pos, num_options=2):
    """(str, int) -> (str list, (str list) list, int list) tuple
    returns lists of corrects and options of a given POS for the whole dataframe.
    first gets lists of options for all the words of the desired POS then chooses best one by quality.
    index of the correct word is added so that it could be found within the original sentence
    """

    # get list of a given pos for every sentence
    wordsets = [self.find_main_pos(row, pos) for row in range(self.df.shape[0])]

    bests = []

    for wordset in wordsets:
      opt_list = []
      for word in wordset:
        text, pos, idx = word
        text = str(text)
        try:
          options = self.get_options(text, pos, num_options)
        except:
          options=(word, [], 0)
        if len(options[1]) == 3:
          original_word, alts, quality = options
          options = original_word, alts, quality, [idx]
          opt_list.append(options)
      if len(opt_list) > 0:
        best = max(opt_list, key=lambda x:x[2])
        bests.append(best)
      else: bests.append((np.nan, np.nan, np.nan, np.nan))
    corrects = [x[0] for x in bests]
    options = [x[1] for x in bests]
    indices = [x[3] for x in bests]
    return corrects, options, indices
  
  def vocab_selection_options_to_df(self):
    """(self) -> (self)
    adds columns with vocabulary selection corrects, options and indices to the df
    """

    for pos in ['noun', 'verb', 'adverb', 'adjective']:

      selector = self.get_vocab_selection(pos)
      self.df[pos+'_vocab_selection_correct'] = selector[0]
      self.df[pos+'_vocab_selection_options'] = selector[1]
      self.df[pos+'_vocab_selection_idx'] = selector[2]
  
  def find_verbs(self, row_number):
    """(int) -> (str list, int, int list)
    finds verbs and combinations auxiliary-verb in a given row of the dataframe.
    returns list of verbs, 1 for analytic verb form or 0 for synthetic and list of indices
    used to find the verbs in the sentence
    """
    all_words = np.array([str(word).lower() for word in self.df['wordlist'][row_number]])
    values = np.array(self.df['pos'][row_number])
    lemmas = np.array(self.df['lemma'][row_number])

    # A. search aux + verbs. Higher priority cause they're less numerous
    idx = []
    for i in range(len(values)-1):
      if [lemmas[i], np.roll(values, -1)[i]] in [['be', 'verb'], ['have', 'verb']]:
        idx.append(i)

    # B. search for plain verbs
    idx2 = []
    for pos in ['auxiliary', 'verb']:
      searchval = pos
      idx2.extend(np.where(values == searchval)[0].tolist())
    idx2 = [i for i in idx2 if (i not in idx and i-1 not in idx)]
    total_idx = sorted(idx + idx2)
    
    # put mark 1 for analytic form of verb
    result = [[all_words[i]+' '+all_words[i+1] if (i in idx) else all_words[i] for i in total_idx ], [1 for i in sorted(idx)] + [0 for i in sorted(idx2)], [i for i in total_idx]]
    
    if 1 in result[1]:
      result[1] = 1
    else: result[1] = 0
    if len(result[0]) == 0:
      result = [np.nan, np.nan, np.nan]

    return result
  
  def verbs_to_df(self):
    """(self) -> (self)
    adds columns with verbs to the df
    """
    verb_finder = [self.find_verbs(row) for row in range(self.df.shape[0])]
    self.df['verbs'] = [x[0] for x in verb_finder]
    self.df['analytic_verb_form'] = [x[1] for x in verb_finder]
    self.df['verbs_idx'] = [x[2] for x in verb_finder]
  
  def find_verbs_lemma(self, verb, num_row):
    """(str, int) -> (str)
    finds lemma of a verb listed in column 'verbs'. not to use with nan values in 'verbs'
    """
    verblist = self.df['verbs'][num_row]
    order_num = verblist.index(verb)
    if num_row in self.df[self.df['analytic_verb_form'] == 1].index.to_list() and len(verb.split()) > 1:
      sentence_idx = self.df['verbs_idx'][num_row][order_num] + 1
    else: sentence_idx = self.df['verbs_idx'][num_row][order_num]
    return self.df['lemma'][num_row][sentence_idx].lower()

  def find_be(self, row_number):
    """(int) -> ((str) list, (int) list) tuple
    finds forms of the verb BE
    """
    all_words = np.array([str(word).lower() for word in self.df['wordlist'][row_number]])
    lemmas = np.array(self.df['lemma'][row_number])
    sent = self.df['raw'][row_number]

    searchval = 'be'
    idx = np.where(lemmas == searchval)[0]
    result = ([all_words[i] for i in sorted(idx) if all_words[i] not in ["'s", "'re", "'m"]],
              [np.array([word for word in self.df['wordlist'][row_number]])[i].i - sent.start for i in sorted(idx) if all_words[i] not in ["'s", "'re", "'m"]])
    return( result if len(result[0]) > 0 else (np.nan, np.nan))

  def be_to_df(self):
    """(self) -> (self)
    adds columns with be to the df
    """
    be_finder = [self.find_be(row) for row in range(self.df.shape[0])]
    self.df['be'] = [x[0] for x in be_finder]
    self.df['be_idx'] = [x[1] for x in be_finder]

  def find_prep(self, row_number):
    """(int) -> ((str) list, (int) list) tuple
    finds prepositions
    """
    all_words = np.array([str(word).lower() for word in self.df['wordlist'][row_number]])
    poses = np.array(self.df['pos'][row_number])
    sent = self.df['raw'][row_number]

    searchval = 'adposition'
    idx = np.where(poses == searchval)[0]
    result = ([all_words[i] for i in sorted(idx) if all_words[i] in ['on', 'in', 'of', 'to', 'at', 'for', 'from', 'under', 'with']],
    [np.array([word for word in self.df['wordlist'][row_number]])[i].i - sent.start for i in sorted(idx) if all_words[i] in ['on', 'in', 'of', 'to', 'at', 'for', 'from', 'under', 'with']])
    return( result if len(result[0]) > 0 else (np.nan, np.nan))

  def prep_to_df(self):
    """(self) -> (self)
    adds columns with prepositions to the df
    """
    prep_finder = [self.find_prep(row) for row in range(self.df.shape[0])]
    self.df['prepositions'] = [x[0] for x in prep_finder]
    self.df['prepositions_idx'] = [x[1] for x in prep_finder]

  def build_df(self, text):    
    """(str) -> (pd.dataframe)
    initiates dataframe from str text
    """

    sentences = sentzer(text)

    df = pd.DataFrame({'raw': [sent for sent in sentences.sents],
                    'wordlist': [[word for word in sent] for sent in sentences.sents],
                    'pos': [[spacy.explain(token.pos_) for token in nlp(str(sent))] for sent in sentences.sents],
                    'lemma': [[token.lemma_ for token in nlp(str(sent))] for sent in sentences.sents],
                    'dependencies': [[token.dep_ for token in nlp(str(sent))] for sent in sentences.sents]
                    })
    return df

  ###################
  # excercise generators
  def get_vocab_selection_excercises(self, num_ex=6):
    """(int) -> (dict)
    getting vocabulary selection excercises
    """
    excercises = []
    used_words = []
    main_pos = {'noun': 0.35, 'verb': 0.35, 'adjective': 0.2, 'adverb': 0.1}

    while len(excercises) < num_ex:
      rows_to_check = set(range(0, self.df.shape[0])) - set(self.used_rows)
      found = False
      pos = np.random.choice(list(main_pos.keys()), size=1, p=list(main_pos.values())).item()
      
      while not found:
        
        if len(rows_to_check) == 0:
            weight_to_share = main_pos[pos] / (len(main_pos) - 1)
            main_pos.pop(pos)
            for p in main_pos:
              main_pos[p] += weight_to_share
            break
        
        num_row = random.choice(list(rows_to_check))
        rows_to_check.discard(num_row)

        if (len(self.df['raw'][num_row]) > 8) and \
        not (self.df[pos+'_vocab_selection_correct'][num_row] in used_words) and \
        not (self.df[pos+'_vocab_selection_correct'][num_row] is np.nan):

          correct = self.df[pos+'_vocab_selection_correct'][num_row]
          options = self.df[pos+'_vocab_selection_options'][num_row]
          random.shuffle(options)
          index = self.df[pos+'_vocab_selection_idx'][num_row][0]

          raw = self.df['raw'][num_row]
          sentence = str(raw[:index]).strip()+' _____ '+str(raw[index+1:])
          
          ex = {'sentence': sentence,
                'options' : [options], 
                'answers' : correct,
                'result'  : [''],
                'total'   : 0
              }
          excercises.append(ex)
          self.used_rows.append(num_row)
          used_words.append(correct)
          found = True

    return excercises

  def get_past_tenses_excercises(self, num_ex=6):
    """(int) -> (dict)
    getting past tenses excercises
    """
    excercises = []
    tenses = {'past_simple': 0.4, 'past_cont': 0.35, 'past_perf': 0.25}

    while len(excercises) < num_ex:
      rows_to_check = set(range(0, self.df.shape[0])) - set(self.used_rows)
      found = False
      tense = np.random.choice(list(tenses.keys()), size=1, p=list(tenses.values())).item()

      if tense == 'past_cont':
        search = rows_to_check & set(self.df[self.df['analytic_verb_form'] == 1].index)        
        while not found:
          if len(search) == 0:
            weight_to_share = tenses[tense] / (len(tenses) - 1)
            tenses.pop(tense)
            for t in tenses:
              tenses[t] += weight_to_share
            break
          num_row = random.choice(list(search))
          search.discard(num_row)
          for verb in self.df['verbs'][num_row]:
            if (len(verb.split()) > 1) and \
            (verb.split()[0] in ['was', 'were']) and \
            (verb.endswith('ing')):
              found = True

      elif tense == 'past_perf':
        search = rows_to_check & set(self.df[self.df['analytic_verb_form'] == 1].index)
        while not found:
          if len(search) == 0:
            weight_to_share = tenses[tense] / (len(tenses) - 1)
            tenses.pop(tense)
            for t in tenses:
              tenses[t] += weight_to_share
            break
          num_row = random.choice(list(search))
          search.discard(num_row)
          for verb in self.df['verbs'][num_row]:
            if (len(verb.split()) > 1) and \
            (verb.split()[0] == 'had'):
              found = True
        
      else:      # past_simple
        search = rows_to_check & set(self.df[(self.df['analytic_verb_form'] == 0) & (self.df['verbs'] is not np.nan)].index)
        while not found:
          if len(search) == 0:
            weight_to_share = tenses[tense] / (len(tenses) - 1)
            tenses.pop(tense)
            for t in tenses:
              tenses[t] += weight_to_share
            break
          num_row = random.choice(list(search))
          search.discard(num_row)
          for verb in self.df['verbs'][num_row]: 
            try:
              pastform = getInflection(self.find_verbs_lemma(verb, num_row), 'VBD')[0]
            except:
              pastform = 0
            if verb == pastform:
              found = True

      all_verbs = self.df['verbs'][num_row]
      corrects = []
      options = []
      indices = []
      for i in range(len(all_verbs)):
        verb = all_verbs[i]
        try:
          pastform = getInflection(self.find_verbs_lemma(verb, num_row), 'VBD')[0]
        except:
          pastform = 0
        if (len(verb.split()) > 1) and \
            (verb.split()[0] in ['was', 'were']) and \
            (verb.endswith('ing')):
            main_verb = self.find_verbs_lemma(verb, num_row)
            opts = [getInflection(main_verb, 'VBD')[0], 'had ' + getInflection(main_verb, 'VBN')[0], verb]
            random.shuffle(opts)
            corrects.append(verb)
            options.append(opts)
            indices.append(self.df['verbs_idx'][num_row][i])
          
        elif (len(verb.split()) > 1) and (verb.split()[0] == 'had'):
            main_verb = self.find_verbs_lemma(verb, num_row)
            opts = [getInflection(main_verb, 'VBD')[0], 'was ' + getInflection(main_verb, 'VBG')[0], verb]
            random.shuffle(opts)
            corrects.append(verb)
            options.append(opts)
            indices.append(self.df['verbs_idx'][num_row][i])

        elif verb == pastform:
            main_verb = self.find_verbs_lemma(verb, num_row)
            opts = ['was ' + getInflection(main_verb, 'VBG')[0], 'had ' + getInflection(main_verb, 'VBN')[0], verb]
            random.shuffle(opts)
            corrects.append(verb)
            options.append(opts)
            indices.append(self.df['verbs_idx'][num_row][i])

      raw = self.df['raw'][num_row]

      pieces = []
      pieces.append(raw[:indices[0]])
      for i in range(len(corrects)-1):
        if len(corrects[i].split()) > 1:
          pieces.append(raw[indices[i]+2:indices[i+1]])
        else: pieces.append(raw[indices[i]+1:indices[i+1]])
      if len(corrects[-1].split()) > 1:
        pieces.append(raw[indices[-1]+2:])
      else: pieces.append(raw[indices[-1]+1:])

      sentence = ' _____ '.join([str(piece).strip() for piece in pieces])

      ex = {'sentence': sentence,
            'options' : options,
            'answers' : corrects,
            'result'  : ['' for _ in corrects],
            'total'   : 0
            }
      excercises.append(ex)
      self.used_rows.append(num_row)

    return excercises

  def get_active_passive_excercises(self, num_ex=6):
    """(int) -> (dict)
    getting active/passive excercises
    """
    excercises = []
    voices = {'active': 0.6, 'passive': 0.4}

    while len(excercises) < num_ex:
      rows_to_check = set(range(0, self.df.shape[0])) - set(self.used_rows)
      found = False
      voice = np.random.choice(list(voices.keys()), size=1, p=list(voices.values())).item()
      num = None

      if voice == 'passive':
        search = rows_to_check & set(self.df[self.df['analytic_verb_form'] == 1].index)
        while not found:
          if len(search) == 0:
            weight_to_share = voices[voice] / (len(voices) - 1)
            voices.pop(voice)
            for v in voices:
              voices[v] += weight_to_share
            break
          num_row = random.choice(list(search))
          search.discard(num_row)
          for verb in self.df['verbs'][num_row]:
            if (len(verb.split()) > 1) and \
              (verb.split()[0] in ['was', 'were', 'be', 'is', 'are', 'am']) and \
              (verb.split()[1] == getInflection(self.find_verbs_lemma(verb, num_row), 'VBN')[0]):
              found = True
              num = num_row

      else:      # active
        search = rows_to_check & set(self.df[(self.df['analytic_verb_form'] == 0) & (self.df['verbs'] is not np.nan)].index)
        while not found:
          if len(search) == 0:
            weight_to_share = voices[voice] / (len(voices) - 1)
            voices.pop(voice)
            for v in voices:
              voices[v] += weight_to_share
            break
          num_row = random.choice(list(search))
          search.discard(num_row)
          for verb in self.df['verbs'][num_row]:
            try:
              pastform = getInflection(self.find_verbs_lemma(verb, num_row), 'VBD')[0]
            except:
              pastform = 0
            if verb == pastform:
              found = True
              num = num_row

      if not num:
        continue
      all_verbs = self.df['verbs'][num]
      corrects = []
      options = []
      indices = []
      for i in range(len(all_verbs)):
        verb = all_verbs[i]
        try:
          pastform = getInflection(self.find_verbs_lemma(verb, num), 'VBD')[0]
        except:
          pastform = 0
        if (len(verb.split()) > 1) and \
          (verb.split()[0] in ['was', 'were', 'be', 'is', 'are', 'am']) and \
          (verb.split()[1] == getInflection(self.find_verbs_lemma(verb, num), 'VBN')[0]):
            main_verb = self.find_verbs_lemma(verb, num)
            opts = [getInflection(main_verb, 'VBD')[0], verb]
            random.shuffle(opts)
            corrects.append(verb)
            options.append(opts)
            indices.append(self.df['verbs_idx'][num][i])

        elif verb == pastform:
            main_verb = self.find_verbs_lemma(verb, num)
            opts = ['was ' + getInflection(main_verb, 'VBN')[0], verb]
            random.shuffle(opts)
            corrects.append(verb)
            options.append(opts)
            indices.append(self.df['verbs_idx'][num][i])

      raw = self.df['raw'][num]
      pieces = []
      pieces.append(raw[:indices[0]])
      for i in range(len(corrects)-1):
        if len(corrects[i].split()) > 1:
          pieces.append(raw[indices[i]+2:indices[i+1]])
        else: pieces.append(raw[indices[i]+1:indices[i+1]])
      if len(corrects[-1].split()) > 1:
        pieces.append(raw[indices[-1]+2:])
      else: pieces.append(raw[indices[-1]+1:])

      sentence = ' _____ '.join([str(piece).strip() for piece in pieces])

      ex = {'sentence': sentence,
                'options' : options,
                'answers' : corrects,
                'result'  : ['' for _ in corrects],
                'total'   : 0
              }
      excercises.append(ex)
      self.used_rows.append(num_row)

    return excercises

  def get_be_excercises(self, num_ex=6):
    """(int) -> (dict)
    getting be form excercises
    """
    excercises = []

    while len(excercises) < num_ex:
      rows_to_check = set(range(0, self.df.shape[0])) - set(self.used_rows)
      num_row = random.choice(list(rows_to_check))
      rows_to_check.discard(num_row)

      if self.df['be'][num_row] is not np.nan:      
        corrects = self.df['be'][num_row]
        indices = self.df['be_idx'][num_row]
        
        raw = self.df['raw'][num_row]
        pieces = []
        pieces.append(raw[:indices[0]])
        for i in range(len(corrects)-1):
          pieces.append(raw[indices[i]+1:indices[i+1]])
        pieces.append(raw[indices[-1]+1:])

        sentence = ' _____ '.join([str(piece).strip() for piece in pieces])
        
        ex = {'sentence': sentence,
                    'options' : [],
                    'answers' : corrects,
                    'result'  : ['' for _ in corrects],
                    'total'   : 0
                  }
        excercises.append(ex)
        self.used_rows.append(num_row)

    return excercises

  def get_prep_excercises(self, num_ex=6):
    """(int) -> (dict)
    getting prepositions excercises
    """
    excercises = []

    while len(excercises) < num_ex:
      rows_to_check = set(range(0, self.df.shape[0])) - set(self.used_rows)
      num_row = random.choice(list(rows_to_check))
      rows_to_check.discard(num_row)

      if (self.df['prepositions'][num_row] is not np.nan):
        corrects = self.df['prepositions'][num_row]
        indices = self.df['prepositions_idx'][num_row]

        raw = self.df['raw'][num_row]
        pieces = []
        pieces.append(raw[:indices[0]])
        for i in range(len(corrects)-1):
          pieces.append(raw[indices[i]+1:indices[i+1]])
        pieces.append(raw[indices[-1]+1:])

        sentence = ' _____ '.join([str(piece).strip() for piece in pieces])

        ex = {'sentence': sentence,
                    'options' : [],
                    'answers' : corrects,
                    'result'  : ['' for _ in corrects],
                    'total'   : 0
                  }
        excercises.append(ex)
        self.used_rows.append(num_row)

    return excercises
  
  def reset_used_rows(self):
    """(self) -> (self)
    reset self.used_rows to start generating excercises again
    """
    self.used_rows = []