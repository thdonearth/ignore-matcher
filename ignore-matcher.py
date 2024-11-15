#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import pathlib
import collections

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

def check_pattern(pattern: str) -> bool:
  # TODO check grammar of given pattern
  if '!' == pattern[0]:
    return False
  else:
    return True

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

      # check patterns and append to the corresponding list
      try:
        pattern_type = check_pattern(line)
        if pattern_type is False:
          include_patterns.append(line[1:])
        else:
          exclude_patterns.append(line)
      except Exception:
        raise

  base_path_abs = os.path.dirname(ignore_file_abs)

  return PathBasedPatterns(base_path_abs, exclude_patterns, include_patterns)

def matcher_impl(file_path_rel, pattern: str) -> bool:
  # TODO parser
  return True

def match_patterns(file_path_abs: str, path_based_patterns: PathBasedPatterns) -> bool:
  file_path_rel: str = os.path.relpath(path_based_patterns.base_path_abs, file_path_abs)
  # TODO
  #   1. use `include_patterns` and then `exclude_patterns`
  #   2. call matcher_impl()
  return True

def yield_matched_files(ignore_file_abs: str):
  path_based_patterns = read_ignore_file(ignore_file)

  for root, dirs, files in os.walk(os.getcwd()):
    for file in files
      file_path_abs = os.path.join(root, file)
      if match_patterns(file_path_abs, path_based_patterns) is True:
        yield file_path_abs

if __name__ == "__main__":
  COMMAND_PREFIX = ["clang-format", "-i"]
  for file in yield_matched_files(".clang-format-ignore"):
    try:
      command = COMMAND_PREFIX + ['file']
      subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
      print(f"Error formatting file {file}: {e}")

