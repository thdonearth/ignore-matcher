#!/usr/bin/env python3
import os
import re
import subprocess

class PathBasedPatterns:
  def __init__(self, base_path_abs, exclude_patterns, include_patterns):
    self.base_path_abs = base_path_abs
    self.exclude_patterns = exclude_patterns
    self.include_patterns = include_patterns

  def __repr__(self):
    return f"PathBasedPatterns(base_pat_abs='{self.base_path_abs}', exclude_patterns={self.exclude_patterns}, include_patterns={self.include_patterns})"

  def get_base_path(self):
    return self.base_path_abs

  def get_patterns(self):
    return self.exclude_patterns, self.include_patterns

def compile_pattern(pattern: str):
  if pattern.endswith('/'):
    pattern += '**'

  if '!' == pattern[0]:
    pattern_type = False
  else:
    pattern_type = True

  if pattern_type is False:
    pattern = pattern[1:]

  pattern = pattern.replace('**', '{ANY_DIRS}')
  pattern = pattern.replace('.', '{DOT}')
  pattern = re.escape(pattern)
  pattern = pattern.replace(r'\{ANY_DIRS\}', '.*')
  pattern = pattern.replace(r'\{DOT\}', '\\.')
  pattern = pattern.replace(r'\*', '[^/]*')
  pattern = pattern.replace(r'\?', '.')
  pattern = re.sub(r'\[([^]]+)\]', r'[\1]', pattern)

  compiled_pattern = re.compile('^' + pattern + '$')

  return pattern_type, compiled_pattern

def read_ignore_file(ignore_file_abs: str):
  exclude_patterns = []
  include_patterns = []

  with open(ignore_file_abs, 'r') as f:
    for line in f:
      # remove whitespace
      line = line.strip()

      # jump empty line and commands
      if not line or line.startswith('#'):
        continue

      # support recursion
      if line.endswith('/'):
        line += '**'

      # check patterns and append to the corresponding list
      try:
        pattern_type, compiled_pattern = compile_pattern(line)
        if pattern_type is False:
          include_patterns.append(compiled_pattern)
        else:
          exclude_patterns.append(compiled_pattern)
      except Exception:
        raise

  base_path_abs = os.path.dirname(ignore_file_abs)

  return PathBasedPatterns(base_path_abs, exclude_patterns, include_patterns)

def matcher_impl(pattern, file_path: str) -> bool:
  return bool(pattern.fullmatch(file_path))

def is_match_patterns(file_path_abs: str, path_based_patterns: PathBasedPatterns) -> bool:
  file_path_rel: str = os.path.relpath(file_path_abs, path_based_patterns.base_path_abs)
  #   1. use `include_patterns` and then `exclude_patterns`
  #   2. call matcher_impl()
  for pattern in path_based_patterns.include_patterns:
    if matcher_impl(pattern, file_path_rel) is True:
      return True

  for pattern in path_based_patterns.exclude_patterns:
    if matcher_impl(pattern, file_path_rel) is True:
      return False

  return True

def yield_matched_files(ignore_file_abs: str):
  path_based_patterns = read_ignore_file(ignore_file_abs)

  for root, _, files in os.walk(os.getcwd()):
    for f in files:
      file_path_abs = os.path.join(root, f)
      if is_match_patterns(file_path_abs, path_based_patterns) is True:
        yield file_path_abs

if __name__ == "__main__":
  COMMAND_PREFIX = ["clang-format", "-i"]
  for f in yield_matched_files(os.path.abspath(".clang-format-ignore")):
    try:
      command = COMMAND_PREFIX + [f'{f}']
      subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
      print(f"Error formatting file {f}: {e}")


