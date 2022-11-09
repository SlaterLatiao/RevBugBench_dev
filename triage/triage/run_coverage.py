import sys
import os

import shutil
import logging
import itertools
import multiprocessing
import time
import numpy as np

from utils.common import dump_to_pickle
from utils import sanitizer, new_process
from setup.setup import get_exp_config
from triage.get_seeds import get_seeds
from triage.run_crashes import parseFixReverterLog, UNIT_TIMEOUT, RSS_LIMIT_MB

def run_coverage(seeds_by_trial, cov_bin, work_dir, target_out_dir, cores):
  start_time = time.time()
  triage_dir = os.path.join(work_dir, 'triage')
  if os.path.exists(triage_dir):
    shutil.rmtree(triage_dir)
  os.mkdir(triage_dir)

  all_seeds = []
  for trial_name, seeds in seeds_by_trial.items():
    for seed in seeds:
      all_seeds.append((trial_name, seed))

  logging.info(f'going to triage {len(all_seeds)} seeds')
  seed_chucks = np.array_split(all_seeds, 100)

  multiprocessing.freeze_support()

  accum_count = 0
  with multiprocessing.Pool(processes=cores) as pool:
    processed_seeds_by_trial = {name: [] for name in seeds_by_trial}
    for chunck in seed_chucks:
      logging.info(f'triage has reached {accum_count/len(all_seeds)*100}% progress [{accum_count}/{len(all_seeds)}]')
      results = pool.starmap(run_coverage_worker, zip(chunck, 
                    itertools.repeat(cov_bin), itertools.repeat(triage_dir)))
      for res in results:
        processed_seeds_by_trial[res[0]].append(res[1])
      accum_count += len(chunck)
  end_time = time.time()
  with open(os.path.join(target_out_dir, 'coverage_time'), 'w+') as f:
    f.write(str(end_time - start_time))
    
  dump_to_pickle(target_out_dir, processed_seeds_by_trial, 'queue_seeds')
  logging.info('dumped queue seeds info to pickle')

def run_coverage_worker(seed_pair, cov_bin, triage_dir):
  worker_name = multiprocessing.current_process().name
  worker_triage_dir = os.path.join(triage_dir, worker_name)
  if not os.path.exists(worker_triage_dir):
    os.mkdir(worker_triage_dir)

  trial_name, seed = seed_pair
  seed_env = os.environ.copy()
  sanitizer.set_sanitizer_options(seed_env)

  args = [
    cov_bin,
    f'-timeout={UNIT_TIMEOUT}',
    f'-rss_limit_mb={RSS_LIMIT_MB}',
    seed['path']
   ]

  res = new_process.execute(args,
                               env=seed_env,
                               cwd=worker_triage_dir,
                               expect_zero=False,
                               kill_children=True,
                               timeout=UNIT_TIMEOUT + 5)

  reaches, triggers = parseFixReverterLog(res.output)

  seed['reach'] = reaches
  seed['trigger'] = triggers

  return trial_name, seed

def run_coverage_main(analysis):
  seeds_by_trial = get_seeds(analysis.trial_dirs, analysis.program, analysis.fuzzer, 'queue')
  run_coverage(seeds_by_trial, analysis.cov_bin, analysis.work_dir, analysis.target_out, analysis.cores)

def main():
  logging.basicConfig(level = logging.INFO)
  analysis = get_exp_config()

  seeds_by_trial = get_seeds(analysis.trial_dirs, analysis.program, analysis.fuzzer, 'queue')
  run_coverage(seeds_by_trial, analysis.cov_bin, analysis.work_dir, analysis.target_out, analysis.cores)


if __name__ == '__main__':
  sys.exit(main())
