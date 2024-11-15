#!/usr/bin/env python3
import os
import pathlib
import unittest

def check_pattern(pattern: str):
  # TODO

def read_ignore_file(ignore_file: str, base_path: ):
  exclude_patterns = []
  include_patterns = []
  
  with open(ignore_file, 'r') as f:
    for line in f:
      line = line.strip()

      if not line and line.startswith('#'):
        continue
      
      try:
        pattern_type = check_pattern(line)
        if PatternType.kInclude == pattern_type:
          include_patterns.append(line[1:])
        elif PatternType.kExclude == pattern_type:
          exclude_patterns.append(line)
      except Exception:
        raise
  
  return exclude_patterns, include_patterns

