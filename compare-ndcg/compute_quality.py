#!/usr/bin/env python3

import argparse
import logging as log
import os
import psycopg2
import pandas as pd
import scipy.stats as stats
import sklearn.metrics as metrics
import warnings

# Парсер аргументов командной строки
parser = argparse.ArgumentParser(description = 'Compute quality for specified (or all) tournaments')
parser.add_argument('tournaments', metavar='TID', type=int, nargs='*',
                    help = 'tournament identifier')
parser.add_argument('--rating', required=True,
                    help = 'rating to evaluate')
parser.add_argument('--baseline', default='b',
                    help = 'baseline rating to compare to')

args = parser.parse_args()

# Настройка логирования.
# Убираем warning-и от pandas про использование sql-строк для postgres
log.basicConfig(format='{asctime} | {levelname:8s} | {message}', style='{', level=log.INFO)
warnings.filterwarnings('ignore', category=UserWarning)

# Подключение к БД
conn_str = os.environ.get('DATABASE')
if conn_str is None:
    raise Exception('DATABASE is not defined')

conn = psycopg2.connect(conn_str)

# Получение списка турниров
tournaments = args.tournaments
if tournaments == []:
    log.info('Get all tournaments')
    tournaments = pd.read_sql("SELECT id FROM tournaments WHERE maii_rating AND end_datetime > '2022-01-01'", conn).get('id').tolist()
    log.info('Got %d tournaments', len(tournaments))

# Получение набора пар nDCG
results = list()
for tid in tournaments:
    log.info('Loading tournament %d', tid)
    row = {'tid': tid}
    for name, rating in {'rating': args.rating, 'baseline': args.baseline}.items():
        log.info('Computing nDCG for %s %s for tournament %d', name, rating, tid)
        sql = 'SELECT t.team_id, t.total, t.position, rt.mp FROM {r}.tournament_result rt LEFT JOIN tournament_results t ON rt.tournament_id = t.tournament_id AND rt.team_id = t.team_id WHERE t.tournament_id = {t}'.format(t = tid, r = rating)
        log.debug('SQL: %s', sql)
        df = pd.read_sql(sql, conn)
        # некоторые турниры могут быть без результатов
        if df.size > 0:
            y_true = df.get('position').to_numpy()
            y_score = df.get('mp').to_numpy()
            try:
                ndcg = metrics.ndcg_score([y_true], [y_score])
                log.debug('nDCG: %f', ndcg)
                row[name] = ndcg
            except Exception as e:
                log.warning(e)
                log.debug(df)
                pass
    log.debug(row)
    results.append(row)

# Вывод финального набора пар nDCG
res_df = pd.DataFrame(results, columns = ['tid', 'rating', 'baseline'])
print(res_df.query('(rating >= 0) & (baseline >= 0)'))

# Проверяем: альтернатива d = x - y > 0, т.е. новый рейтинг лучше старого
w = stats.wilcoxon(x = res_df.get('rating'), y = res_df.get('baseline'),
                     alternative = 'greater',
                     nan_policy = 'omit')

# Вывод результатов
print()
print('Wilcoxon test:')
print(f'Statistics:\t{w.statistic}')
print(f'p-value:\t{w.pvalue}')
print()
print('Medians:')
print('new:\t', res_df.get('rating').median())
print('old:\t', res_df.get('baseline').median())
