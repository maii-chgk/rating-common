#!/usr/bin/env python3

import argparse
import logging as log
import os
import psycopg2
import pandas as pd
import scipy.stats as stats
import sklearn.metrics as metrics
import warnings


def db_connection():
    conn_str = os.environ.get('DATABASE')
    if conn_str is None:
        raise Exception('DATABASE is not defined')
    return psycopg2.connect(conn_str)


def fetch_tournaments(connection) -> list:
    log.info('Fetching all tournaments')
    tournaments_query = f'''
        SELECT id 
        FROM tournaments 
        WHERE maii_rating = true 
            AND end_datetime between '2021-09-01' and now()
    '''
    tournaments = pd.read_sql(tournaments_query, connection).get('id').tolist()
    log.info('Got %d tournaments', len(tournaments))
    return tournaments


def ndcg_for_tournament(tournament_id, rating, baseline) -> dict:
    log.info('Loading tournament %d', tournament_id)
    row = {'tid': tournament_id}
    for name, rating in {'rating': rating, 'baseline': baseline}.items():
        log.info(f'Computing nDCG for {name} {rating} for tournament {tournament_id}')
        sql = f'''
            SELECT t.team_id, t.total, t.position, rt.mp 
            FROM {rating}.tournament_result rt 
            LEFT JOIN tournament_results t 
                ON rt.tournament_id = t.tournament_id AND rt.team_id = t.team_id 
            WHERE t.tournament_id = {tournament_id} 
        '''
        log.debug('SQL: %s', sql)
        df = pd.read_sql(sql, conn)
        # некоторые турниры могут быть без результатов
        if df.size == 0:
            log.error(f"no results for {tournament_id} in {rating}")
            continue
        y_true = df.get('position').to_numpy()
        y_score = df.get('mp').to_numpy()
        try:
            ndcg = metrics.ndcg_score([y_true], [y_score])
            log.debug('nDCG: %f', ndcg)
            row[name] = ndcg
        except Exception as e:
            log.error(e)
            log.debug(df)
    return row


# Парсер аргументов командной строки
parser = argparse.ArgumentParser(description='Compute quality for specified (or all) tournaments')
parser.add_argument('tournaments', metavar='TID', type=int, nargs='*',
                    help='tournament identifier')
parser.add_argument('--rating', required=True,
                    help='rating to evaluate')
parser.add_argument('--baseline', default='b',
                    help='baseline rating to compare to')

args = parser.parse_args()

# Настройка логирования.
# Убираем warning-и от pandas про использование sql-строк для postgres
log.basicConfig(format='{asctime} | {levelname:8s} | {message}', style='{', level=log.INFO)
warnings.filterwarnings('ignore', category=UserWarning)

conn = db_connection()
tournaments = args.tournaments or fetch_tournaments(conn)

# Получение набора пар nDCG
results = [ndcg for tid in tournaments if (ndcg := ndcg_for_tournament(tid, args.rating, args.baseline))]

# Вывод финального набора пар nDCG
res_df = pd.DataFrame(results, columns=['tid', 'rating', 'baseline'])
print(res_df.query('(rating >= 0) & (baseline >= 0)').sort_values(by='rating'))

# Проверяем: альтернатива d = x - y > 0, т.е. новый рейтинг лучше старого
w = stats.wilcoxon(x=res_df.get('rating'),
                   y=res_df.get('baseline'),
                   alternative='greater',
                   nan_policy='omit')

# Вывод результатов
print()
print('Wilcoxon test:')
print(f'Statistics:\t{w.statistic}')
print(f'p-value:\t{w.pvalue}')
print()
print('Medians:')
print('new:\t', res_df.get('rating').median())
print('old:\t', res_df.get('baseline').median())
print('Means:')
print('new:\t', res_df.get('rating').mean())
print('old:\t', res_df.get('baseline').mean())
