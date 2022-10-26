import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
import sqlite3

class Processing():
    def __init__(self, q):
        '''
        params:
            q: str - запрос пользователя
        '''
        self.q = q
        self.morph = MorphAnalyzer()
        self.tags = (
            'A', 'ADV', 'ADVPRO', 'ANUM',
            'APRO', 'COM', 'CONJ', 'INTJ',
            'NUM', 'PART', 'PR', 'S',
            'SPRO', 'V'
        )

    def lemmatization(self, word):
        w = self.morph.parse(word)
        l = w[0].normal_form
        return (l)

    def only_one_word(self, phrase):
        to_search = {'token': None, 'lemma': None, 'pos': None}
        if phrase[0].upper() in self.tags:
            phrase = phrase[0].upper()
            to_search['pos'] = phrase
        else:
            phrase = phrase[0].lower()
            if re.search(r'[a-z]', phrase):
                error = 'Латинские символы могут быть использованы только для частеречных тегов!'
                return error
            elif phrase[0] == '"':
                to_search['token'] = phrase[1:-1]
            else:
                l = self.lemmatization(phrase)
                to_search['lemma'] = l
        return to_search

    def token_and_tag(self, phrase):
        if re.search(r'[a-z]', phrase[0].lower()):
            error = 'Формат введенного запроса неверный!'
            return error
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
                error = 'Указан неправильный частеречный тег!'
                return error
            else:
                to_search['pos'] = p
                return to_search

    def main_search(self):
        if re.search(r'[^a-zA-Zа-яА-Я +"]', self.q):
            error = 'В запросе присутствуют некорректные символы!'
            return error
        else:
            request = []
            self.q = self.q.split()
            if len(self.q) > 3:
                error = 'Превышена длина запроса!'
                return error
            elif len(self.q) == 1:    # запрос состоит из одного слова
                q1 = self.q[0].split('+')
                if len(q1) == len(self.q):    # в запросе только слово или только тег
                    result = self.only_one_word(q1)
                    if isinstance(result, dict):
                        request.append(result)
                    else:
                        error = result
                        return error
                else:    # в запросе и токен, и тег
                    result = self.token_and_tag(q1)
                    if isinstance(result, dict):
                        request.append(result)
                    else:
                        error = result
                        return error
            else:    # запрос состоит из 2 или 3 слов
                for element in self.q:
                    q1 = element.split('+')
                    if len(q1) == 1:    # в элементе запроса только слово или только тег
                        result = self.only_one_word(q1)
                        if isinstance(result, dict):
                            request.append(result)
                        elif isinstance(result, str):
                            error = result
                            return error
                        else:
                            request = []
                            break
                    else:    # в элементе запроса и токен, и тег
                        result = self.token_and_tag(q1)
                        if isinstance(result, dict):
                            request.append(result)
                        elif isinstance(result, str):
                            error = result
                            return error
                        else:
                            request = []
                            break
        return request

class GetData():
    def __init__(self, q, conn):
        '''
        params:
            q: str - запрос пользователя
            conn: SQL connection - соединение с БД
        '''
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
