import os
import sys
from pathlib import Path

# Check pathspec availability
try:
    import pathspec
    PATHSPEC_AVAILABLE = True
except ImportError:
    PATHSPEC_AVAILABLE = False
    print("Warning: pathspec library not available. Using simple .gitignore patterns.", file=sys.stderr)


class FileFilter:
    """
    Handles file filtering based on .gitignore patterns.
    """
    
    def __init__(self, directory_path: str, use_gitignore: bool = True):
        """
        Initialize file filter.
        
        Args:
            directory_path: Path to the directory to filter files in
            use_gitignore: Whether to use .gitignore patterns for filtering
        """
        self.directory = Path(directory_path)
        self.use_gitignore = use_gitignore
        self.gitignore_specs = {}  # {directory_path: GitIgnoreSpec}
        
        if self.use_gitignore:
            self._load_gitignore_patterns()
    
    def should_ignore(self, file_path: Path) -> bool:
        """
        Check if a file should be ignored based on .gitignore patterns.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file should be ignored, False otherwise
        """
        # Check hidden files (starting with dot)
        if file_path.name.startswith('.'):
            return True
        
        if not self.use_gitignore:
            return False
        
        if PATHSPEC_AVAILABLE:
            return self._should_ignore_pathspec(file_path)
        else:
            return self._should_ignore_simple(file_path)
    
    def _load_gitignore_patterns(self):
        """
        Load all .gitignore files in the project recursively.
        """
        try:
            # Find all .gitignore files recursively
            gitignore_files = list(self.directory.rglob('.gitignore'))
            
            for gitignore_file in gitignore_files:
                try:
                    gitignore_dir = gitignore_file.parent
                    if PATHSPEC_AVAILABLE:
                        # Use pathspec for correct pattern processing
                        with open(gitignore_file, 'r', encoding='utf-8') as f:
                            patterns = f.read().splitlines()
                        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
                        self.gitignore_specs[str(gitignore_dir)] = spec
                    else:
                        # Simple implementation without pathspec
                        patterns = self._load_simple_gitignore_patterns(gitignore_file)
                        self.gitignore_specs[str(gitignore_dir)] = patterns
                except Exception as e:
                    print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
                    continue
        except Exception as e:
            print(f"Warning: Error loading .gitignore patterns: {e}", file=sys.stderr)
    
    def _load_simple_gitignore_patterns(self, gitignore_file):
        """
        Simple implementation for .gitignore patterns without pathspec.
        """
        try:
            patterns = []
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            return patterns
        except Exception as e:
            print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
            return []
    
    def _should_ignore_pathspec(self, file_path: Path) -> bool:
        """
        Check if file should be ignored using pathspec library.
        """
        try:
            relative_path = file_path.relative_to(self.directory)
            
            # Check all .gitignore files that may affect this file
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    # Check relative to the .gitignore file directory
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        if spec.match_file(relative_to_gitignore):
                            return True
                    except ValueError:
                        # File is not in .gitignore subdirectory
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False
    
    def _should_ignore_simple(self, file_path: Path) -> bool:
        """
        Simple implementation for checking .gitignore patterns.
        """
        try:
            relative_path = file_path.relative_to(self.directory)
            
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        relative_str = str(relative_to_gitignore).replace('\\', '/')
                        
                        # Check spec type - if it's a PathSpec object, skip
                        if hasattr(spec, 'match_file'):
                            # This is a PathSpec object, skip for fallback
                            continue
                        
                        # This is a list of patterns for fallback
                        for pattern in spec:
                            if self._match_simple_pattern(relative_str, pattern):
                                return True
                    except ValueError:
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False
    
    def _match_simple_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Simple pattern matching for .gitignore patterns.
        """
        import fnmatch
        
        # Remove leading slash if present
        if pattern.startswith('/'):
            pattern = pattern[1:]
        
        # Handle patterns with **
        if '**' in pattern:
            # Simple implementation for **
            pattern = pattern.replace('**', '*')
        
        # Handle patterns with leading !
        if pattern.startswith('!'):
            return False  # Simplified handling
        
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            # Check if path starts with this directory
            return file_path.startswith(pattern)
        
        # Use fnmatch for basic matching
        return fnmatch.fnmatch(file_path, pattern) 