# RevBugBench
**RevBugBench** is a fuzzing benchmark based on [FuzzBench](https://github.com/google/fuzzbench). Target programs in **RevBugBench** are generated by [FixReverter](https://github.com/SlaterLatiao/FixReverter). **RevBugBench** is part of the artifact of paper [FIXREVERTER: A Realistic Bug Injection Methodology for Benchmarking Fuzz Testing](https://www.usenix.org/conference/usenixsecurity22/presentation/zhang-zenong). To cite FixReverter and/or RebBugBench, please use [this bibtex](/cite.bib).
## fuzzbench
**RevBugBench** was developed on _FuzzBench_ commit 65297c4c76e63cbe4025f1ce7abc1e89b7a1566c. This [diff file](/fuzzbench/revbugbench.patch) shows the modifications needed by **RevBugBench**. Run the following command on _FuzzBench_ root directory to apply the changes.

`git checkout 65297c4c76e63cbe4025f1ce7abc1e89b7a1566c`

`git apply [path/to/the/diff/file]`

The changes in the diff file can also be manually ported the the lastest verion of _FuzzBench_.

## benchmarks
Target programs in this directory consist of 8 fuzzing targets from _FuzzBench_ and 2 commonly fuzzed _Binutils_ utilities, injected with bugs by _FixReverter_. The version of each program can be found in the _Dockerfile_ in each program's directory. The target programs are formatted as _FuzzBench_ benchmarks, and can be directly added to _FuzzBench_ by copying to _benchmarks_ directory of _FuzzBench_. To fuzz with **RevBugBench**, run FuzzBench [local experiments](https://google.github.io/fuzzbench/running-a-local-experiment) on benchmark programs of **RevBugBench**.
## triage
This folder contains scripts for triage. See [here](/triage/README.md) for instructions.
