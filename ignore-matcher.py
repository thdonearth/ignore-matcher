#!/usr/bin/env python3
import os
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

def matcher_impl(file_path: str, pattern: str) -> bool:
  # ref: https://github.com/llvm/llvm-project/blob/main/clang/lib/Format/MatchFilePath.cpp
  assert pattern, "Pattern cannot be empty"
  assert file_path, "File path cannot be empty"

  # No match if `Pattern` ends with a non-meta character not equal to the last
  # character of `FilePath`.
  c = pattern[-1]
  if c not in '?*]' and c != file_path[-1]:
    return False

  separator = '/'
  eop = len(pattern) # End of `Pattern`.
  end = len(file_path) # End of `FilePath`.
  i = 0 # Index to `Pattern`.

  for j in range(end):
    if i == eop:
      return False

    f = file_path[j]
    if pattern[i] == '\\':
      i += 1
      if i == eop or f != pattern[i]:
        return False
    elif pattern[i] == '?':
      if f == separator:
        return False
    elif pattern[i] == '*':
      if i + 1 < eop and pattern[i + 1] == '*':
        while i < eop and pattern[i] == '*':
          i += 1
        if i == eop:
          return True # '**' at the end matches everything
        if pattern[i] == separator:
          # Try to match the rest of the pattern without consuming the
          # separator for the case where we want to match "zero" directories
          # e.g. "a/**/b" matches "a/b"
          if match_file_path(pattern[i + 1:], file_path[j:]):
            return True
        while j < end:
          if match_file_path(pattern[i:], file_path[j:]):
            return True
          j += 1
        return False
      k = file_path.find(separator, j) # Index of next `Separator`.
      no_more_separators_in_file_path = k == -1
      if i == eop: # `Pattern` ends with a star.
        return no_more_separators_in_file_path
      # `Pattern` ends with a lone backslash.
      if pattern[i] == '\\':
        i += 1
        if i == eop:
          return False
      # The star is followed by a (possibly escaped) `Separator`.
      if pattern[i] == separator:
        if no_more_separators_in_file_path:
          return False
        j = k # Skip to next `Separator` in `FilePath`.
      else:
        # Recurse.
        pat = pattern[i:]
        for j in range(j, end):
          if file_path[j] == separator:
            break
          if match_file_path(pat, file_path[j:]):
            return True
        return False
    elif pattern[i] == '[':
      # Skip e.g. `[!]`.
      if i + 3 < eop or (i + 3 == eop and pattern[i + 1] != '!'):
        # Skip unpaired `[`, brackets containing slashes, and `[]`.
        k = pattern.find_first_of("]/", i + 1)
        if k != -1 and pattern[k] == ']' and k > i + 1:
          if f == separator:
            return False
          i += 1 # After the `[`.
          negated = False
          if pattern[i] == '!':
            negated = True
            i += 1 # After the `!`.
          match = False
          while not match and i < k:
            if i + 2 < k and pattern[i + 1] == '-':
              match = pattern[i] <= f <= pattern[i + 2]
              i += 3 # After the range, e.g. `A-Z`.
            else:
              match = f == pattern[i]
              i += 1
          if negated == match:
            return False
          i = k + 1 # After the `]`.
          continue
      # Match `[` literally.
    else:
      if f != pattern[i]:
        return False

    i += 1

  # Match trailing stars with null strings.
  while i < eop and pattern[i] == '*':
    i += 1

  return i == eop

def is_match_patterns(file_path_abs: str, path_based_patterns: PathBasedPatterns) -> bool:
  file_path_rel: str = os.path.relpath(path_based_patterns.base_path_abs, file_path_abs)
  #   1. use `include_patterns` and then `exclude_patterns`
  #   2. call matcher_impl()
  for pattern in path_based_patterns.include_patterns:
    if matcher_impl(file_path_rel, pattern) is True:
      return True

  for pattern in path_based_patterns.exclude_patterns:
    if matcher_impl(file_path_rel, pattern) is True:
      return False

  return True

def yield_matched_files(ignore_file_abs: str):
  path_based_patterns = read_ignore_file(ignore_file_abs)

  for root, _, files in os.walk(os.getcwd()):
    for file in files:
      file_path_abs = os.path.join(root, file)
      if is_match_patterns(file_path_abs, path_based_patterns) is True:
        yield file_path_abs

if __name__ == "__main__":
  COMMAND_PREFIX = ["clang-format", "-i"]
  for file in yield_matched_files(os.path.abspath(".clang-format-ignore")):
    try:
      command = COMMAND_PREFIX + ['file']
      subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
      print(f"Error formatting file {file}: {e}")

