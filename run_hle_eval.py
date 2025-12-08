Run python run_hle_eval.py
  python run_hle_eval.py
  shell: /usr/bin/bash -e {0}
  env:
    VIREON_BACKEND: dummy
    pythonLocation: /opt/hostedtoolcache/Python/3.11.14/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib
Traceback (most recent call last):
  File "/home/runner/work/Vireon-HLE-Engine/Vireon-HLE-Engine/run_hle_eval.py", line 118, in <module>
    main()
  File "/home/runner/work/Vireon-HLE-Engine/Vireon-HLE-Engine/run_hle_eval.py", line 37, in main
    questions = load_hle_questions(hle_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Vireon-HLE-Engine/Vireon-HLE-Engine/run_hle_eval.py", line 21, in load_hle_questions
    data.append(json.loads(line))
                ^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/json/decoder.py", line 353, in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 10 (char 9)
Error: Process completed with exit code 1.
