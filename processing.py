import re
import pymorphy2
from pymorphy2 import MorphAnalyzer

class Processing():

    def __init__(self, q):
        self.q = q
        self.morph = MorphAnalyzer()
        self.tags = (
            'NOUN', 'ADJ', 'COMP', 'VERB', 
            'INFN', 'PRT', 'GRND', 'NUMR', 
            'ADVB', 'NPRO', 'PRED', 'PREP', 
            'CONJ', 'PRCL', 'INTJ')

    def lemmatization(self, word):
        w = self.morph.parse(word)
        l = w[0].normal_form
        return (l)

    def only_one_word(self, phrase):
        to_search = {'token': None, 'lemma': None, 'pos': None}
        if phrase[0].upper() in self.tags:
            phrase = phrase[0].upper()
            to_search['pos'] = phrase
            #print('ищем в столбце pos')
        else:
            phrase = phrase[0].lower()
            if re.search(r'[a-z]', phrase):
                print('Латинские символы могут быть использованы только для частеречных тегов')
                return None
            elif phrase[0] == '"':
                to_search['token'] = phrase[1:-1]
                #print('ищем в столбце token')
            else:
                l = self.lemmatization(phrase)
                to_search['lemma'] = l
        return to_search

    def token_and_tag(self, phrase):
        if re.search(r'[a-z]', phrase[0].lower()):
            print('Формат введенного запроса неверный')
            return None
        else:
            to_search = {'token': None, 'lemma': None, 'pos': None}
            w = phrase[0].lower() #слово
            if w[0] == '"':
                to_search['token'] = w[1:-1]
            else:
                l = self.lemmatization(w)
                to_search['lemma'] = l
            p = phrase[1].upper()
            if p not in self.tags:
                print('Указан неправильный частеречный тег')
                return None
            else:
                to_search['pos'] = p
                return to_search

    def main_search(self):#, q):
        if re.search(r'[^a-zA-Zа-яА-Я +"]', self.q):
            print('В запросе присутствуют некорректные символы')
            return None
        else:
            request = []
            self.q = self.q.split()
            if len(self.q) > 3:
                print('Превышена длина запроса')
            elif len(self.q) == 1:    # значит в запросе одно слово
                q1 = self.q[0].split('+')
                if len(q1) == len(self.q):    # либо только токен, либо только тег
                    result = self.only_one_word(q1)
                    if result is not None:
                        request = result
                else:    # в запросе токен и тег
                    result = self.token_and_tag(q1)
                    if result is not None:
                        request = result
            else:    # в запросе не одно слово
                for element in self.q:
                    q1 = element.split('+')
                    if len(q1) == 1:    # либо только токен, либо только тег
                        result = self.only_one_word(q1)
                        if result is not None:
                            request.append(result)
                        else:
                            request = []
                            break
                    else:    # в запросе токен и тег
                        result = self.token_and_tag(q1)
                        if result is not None:
                            request.append(result)
                        else:
                            request = []
                            break
        return request

