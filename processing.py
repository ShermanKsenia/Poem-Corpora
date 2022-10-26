import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
import sqlite3

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
                        request.append(result)
                else:    # в запросе токен и тег
                    result = self.token_and_tag(q1)
                    if result is not None:
                        request.append(result)
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

class GetData():

    def __init__(self, q, conn):
        self.q = q
        self.conn = conn
        self.cur = conn.cursor()

    def token_and_pos(self, dct):

        query = """
        SELECT token_id, sent_id
        FROM tokens
        WHERE token = ? AND pos = ?
        """
        self.cur.execute(query, (dct['token'], dct['pos']))
        result = self.cur.fetchall()
        return result

    def lemma_and_pos(self, dct):
        query = """
        SELECT token_id, sent_id
        FROM tokens
        WHERE lemma = ? AND pos = ?
        """
        self.cur.execute(query, (dct['lemma'], dct['pos']))
        result = self.cur.fetchall()
        return result

    def only_token(self, dct):
        query = """
        SELECT token_id, sent_id
        FROM tokens
        WHERE token = ?
        """
        self.cur.execute(query, (dct['token'],))
        result = self.cur.fetchall()
        return result

    def only_lemma(self, dct):
        query = """
        SELECT token_id, sent_id
        FROM tokens
        WHERE lemma = ?
        """
        self.cur.execute(query, (dct['lemma'],))
        result = self.cur.fetchall()
        return result

    def only_pos(self, dct):
        query = """
        SELECT token_id, sent_id
        FROM tokens
        WHERE pos = ?
        """
        self.cur.execute(query, (dct['pos'],))
        result = self.cur.fetchall()
        return result

    def get_for_next(self, result, next):
        sentences = []
        if next['token']:
            item = 'token'
            if next['pos']:
                item += ' = ? AND pos'
        elif next['lemma']:
            item = 'lemma'
            if next['pos']:
                item += ' = ? AND pos'
        elif next['pos']:
            item = 'pos'
        t_query = f"""
            SELECT token_id, sent_id
            FROM tokens
            WHERE {item} = ? AND token_id = ? AND sent_id = ?
            """
        for token_id, sent_id in result:
            next_id = token_id + 1
            if ' ' in item:
                items = item.split(' = ? AND ')
                self.cur.execute(t_query, (next[items[0]], next[items[1]], next_id, sent_id))
            else:
                self.cur.execute(t_query, (next[item], next_id, sent_id))
                cur_sent = self.cur.fetchone()
            if cur_sent:
                sentences.append(cur_sent)
        return sentences

    def sort_sentences(self):
        if self.q[0]['token'] and self.q[0]['pos']: # если в словарь токена записывать не пустые строки, а None
            result = self.token_and_pos(self.q[0]) # id токенов и предложений
        elif self.q[0]['lemma'] and self.q[0]['pos']:
            result = self.lemma_and_pos(self.q[0])
        elif self.q[0]['token'] and not self.q[0]['pos']:
            result = self.only_token(self.q[0])
        elif self.q[0]['lemma'] and not self.q[0]['pos']:
            result = self.only_lemma(self.q[0])
        else:
            result = self.only_pos(self.q[0])
        #print(result)
        if result and len(self.q) > 1:
            sentences = self.get_for_next(result, self.q[1])
            #print(sort_sentences)
            if len(self.q) == 3:
                sentences = self.get_for_next(sentences, self.q[2])
                sentences = [obj[1] for obj in sentences]
                #print(sentences)
                return sentences
            else:
                sentences = [obj[1] for obj in sentences]
                return sentences # получаем список айдишников предложений
        if result:
            result = [obj[1] for obj in result]
        return result

    def get_sentences(self, ids):
        if len(ids) == 1:
            ids = f'({ids[0]})'
        else:
            ids = tuple(ids)
        posts_query = f'''
            SELECT poet, title, sent FROM sentences
            JOIN poems_to_info ON sentences.id_sent== poems_to_info.id_sent
            JOIN info ON poems_to_info.id_info == info.id_info
            WHERE sentences.id_sent in {ids}'''
        self.cur.execute(posts_query)
        result = self.cur.fetchall()
        return result