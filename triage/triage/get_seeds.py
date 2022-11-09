import os
import re
import logging

from common.confighelper import ConfigHelper
from utils.common import CORPUS_QUEUE_STORE, CORPUS_CRASH_STORE


# Returns seeds organized by trial.
def get_seeds(benchmark: str, fuzzer: str, seed_type: str, helper: ConfigHelper) -> dict:
    logging.info('extracting seeds from FuzzBench results')
    seeds = {t: [] for t in helper.trials(benchmark, fuzzer)}
    # TODO: Make `corpus_store` configurable to ease the trouble of extending more fuzzers.
    corpus_store = CORPUS_QUEUE_STORE if seed_type == 'queue' else CORPUS_CRASH_STORE
    for trial in helper.trials(benchmark, fuzzer):
        trial_data_dir = helper.trial_data_dir(benchmark, fuzzer, trial)
        queues = corpus_store[fuzzer]
        for queue in queues:
            queue_dir = os.path.join(helper.trial_data_dir(benchmark, fuzzer, trial), queue)
            if not os.path.exists(queue_dir):
                logging.warning(f'{fuzzer}-{benchmark}-{trial}: queue directory does not exist {queue_dir}')
                continue
            for seed_name in os.listdir(queue_dir):
                file_path = os.path.join(queue_dir, seed_name)
                # TODO: Make following checks configurable.
                if seed_name == 'README.txt' or os.path.isdir(file_path):
                    continue
                if fuzzer == 'libfuzzer' and seed_type == 'crash' \
                        and not seed_name.startswith('oom') and not seed_name.startswith('crash'):
                    continue

                seed = {'path': file_path, 'type': seed_type, 'benchmark': benchmark, 'fuzzer': fuzzer}
                seeds[trial].append(seed)
                time_match = re.search(fr'time:(\d+)', seed_name)
                if time_match:
                    if fuzzer == 'aflplusplus':
                        seed['time'] = int(time_match.group(1)) / 1000
                    else:
                        logging.error(f'unsupported time in seed name with fuzzer {fuzzer}')
                        exit(0)
                else:
                    # Using mtime to represent the seed generation time. Sometimes it's inaccurate.
                    seed['mtime'] = os.path.getmtime(file_path) / 1000
                id_match = re.search(fr'id:(\d+)', seed_name)
                # Re-index seeds generated by fuzzers with multiple queues.
                if id_match and len(queues) == 1:
                    seed['id'] = int(id_match.group(1))
        if len(seeds[trial]) > 0 and ('id' not in seeds[trial][0] or 'mtime' in seeds[trial][0]):
            seeds[trial].sort(key=lambda x: x['time'])
            if 'id' not in seeds[trial][0]:
                for i in range(len(seeds[trial])):
                    seeds[trial][i]['id'] = i
            if 'mtime' in seeds[trial][0]:
                init_time = seeds[trial][0]['mtime']
                for seed in seeds[trial]:
                    seed['time'] = seed['mtime'] - init_time
                    seed.pop('mtime')
    return seeds
