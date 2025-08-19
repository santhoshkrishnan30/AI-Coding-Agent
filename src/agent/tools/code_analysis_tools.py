import os
import subprocess
import ast
import json
import re
from typing import Dict, Any, List, Optional
from ..tools.base import BaseTool

class RunLinterTool(BaseTool):
    @property
    def name(self) -> str:
        return "run_linter"
    
    @property
    def description(self) -> str:
        return "Run a linter on a file or project"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {
                "file_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to the file to lint (if empty, lints the whole project)"
                },
                "linter": {
                    "type": "string",
                    "default": "",
                    "description": "Linter to use (auto-detected if not specified)"
                }
            }
        }
    
    def execute(self, file_path: str = "", linter: str = "") -> Dict[str, Any]:
        try:
            # Handle case where parameters might be dicts
            if isinstance(file_path, dict):
                if "default" in file_path:
                    file_path = file_path["default"]
                elif "value" in file_path:
                    file_path = file_path["value"]
                else:
                    file_path = ""
            
            if isinstance(linter, dict):
                if "default" in linter:
                    linter = linter["default"]
                elif "value" in linter:
                    linter = linter["value"]
                else:
                    linter = ""
            
            # Detect linter if not specified
            if not linter:
                if os.path.exists("requirements.txt") or os.path.exists("setup.py"):
                    linter = "flake8"
                elif os.path.exists("package.json"):
                    linter = "eslint"
                elif os.path.exists("pom.xml"):
                    linter = "checkstyle"
                else:
                    linter = "flake8"  # Default
            
            # Build command based on linter
            if linter == "flake8":
                command = f"flake8 {file_path if file_path else '.'}"
            elif linter == "eslint":
                command = f"npx eslint {file_path if file_path else '.'}"
            elif linter == "checkstyle":
                command = f"mvn checkstyle:check {f'-f {file_path}' if file_path else ''}"
            else:
                return {
                    "success": False,
                    "error": f"Unsupported linter: {linter}",
                    "message": f"Linter {linter} is not supported"
                }
            
            # Run the linter
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": True,
                "linter": linter,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": f"Linted with {linter}, return code: {result.returncode}"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Linter timed out after 30 seconds",
                "message": "Linting operation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to run linter: {str(e)}"
            }

class AnalyzeDependenciesTool(BaseTool):
    @property
    def name(self) -> str:
        return "analyze_dependencies"
    
    @property
    def description(self) -> str:
        return "Analyze project dependencies and their relationships"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {
                "file_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to dependency file (auto-detected if not specified)"
                }
            }
        }
    
    def execute(self, file_path: str = "") -> Dict[str, Any]:
        try:
            # Handle case where file_path might be passed as a dict
            if isinstance(file_path, dict):
                # Extract the actual value from the dict
                if "default" in file_path:
                    file_path = file_path["default"]
                elif "value" in file_path:
                    file_path = file_path["value"]
                else:
                    file_path = ""
            
            # Detect dependency file if not specified
            if not file_path:
                if os.path.exists("requirements.txt"):
                    file_path = "requirements.txt"
                elif os.path.exists("package.json"):
                    file_path = "package.json"
                elif os.path.exists("pom.xml"):
                    file_path = "pom.xml"
                elif os.path.exists("build.gradle"):
                    file_path = "build.gradle"
                else:
                    return {
                        "success": False,
                        "error": "No dependency file found",
                        "message": "Could not find a dependency file to analyze"
                    }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"Dependency file {file_path} does not exist",
                    "message": f"Cannot analyze non-existent dependency file: {file_path}"
                }
            
            # Parse the dependency file
            if file_path.endswith("requirements.txt"):
                with open(file_path, 'r') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                return {
                    "success": True,
                    "dependency_type": "Python",
                    "dependencies": dependencies,
                    "count": len(dependencies),
                    "message": f"Analyzed {len(dependencies)} Python dependencies from {file_path}"
                }
            
            elif file_path.endswith("package.json"):
                with open(file_path, 'r') as f:
                    pkg = json.load(f)
                
                dependencies = []
                if "dependencies" in pkg:
                    dependencies.extend([f"{pkg} {version}" for pkg, version in pkg["dependencies"].items()])
                if "devDependencies" in pkg:
                    dependencies.extend([f"{pkg} {version} (dev)" for pkg, version in pkg["devDependencies"].items()])
                
                return {
                    "success": True,
                    "dependency_type": "Node.js",
                    "dependencies": dependencies,
                    "count": len(dependencies),
                    "message": f"Analyzed {len(dependencies)} Node.js dependencies from {file_path}"
                }
            
            elif file_path.endswith("pom.xml"):
                # Simple parsing for pom.xml (in a real implementation, use a proper XML parser)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract dependencies using regex (simplified)
                pattern = r'<dependency>\s*<groupId>(.*?)</groupId>\s*<artifactId>(.*?)</artifactId>\s*<version>(.*?)</version>'
                matches = re.findall(pattern, content)
                
                dependencies = [f"{group_id}:{artifact_id}:{version}" for group_id, artifact_id, version in matches]
                
                return {
                    "success": True,
                    "dependency_type": "Java/Maven",
                    "dependencies": dependencies,
                    "count": len(dependencies),
                    "message": f"Analyzed {len(dependencies)} Java dependencies from {file_path}"
                }
            
            elif file_path.endswith("build.gradle"):
                # Simple parsing for build.gradle (in a real implementation, use a proper parser)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract dependencies using regex (simplified)
                pattern = r'(implementation|api|compile|runtime)\s+([\'"])(.*?)\2'
                matches = re.findall(pattern, content)
                
                dependencies = [dep[2] for dep in matches]
                
                return {
                    "success": True,
                    "dependency_type": "Java/Gradle",
                    "dependencies": dependencies,
                    "count": len(dependencies),
                    "message": f"Analyzed {len(dependencies)} Java dependencies from {file_path}"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported dependency file format: {file_path}",
                    "message": f"Cannot analyze dependency file: {file_path}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to analyze dependencies: {str(e)}"
            }

class FindReferencesTool(BaseTool):
    @property
    def name(self) -> str:
        return "find_references"
    
    @property
    def description(self) -> str:
        return "Find all references to a function, variable, or class in the codebase"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["name"],
            "optional": {
                "file_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to search in (if empty, searches the whole project)"
                },
                "file_type": {
                    "type": "string",
                    "default": "",
                    "description": "File type to search in (e.g., .py, .js, .java)"
                }
            }
        }
    
    def execute(self, name: str, file_path: str = "", file_type: str = "") -> Dict[str, Any]:
        try:
            import os
            import re
            
            # Handle case where parameters might be dicts
            if isinstance(file_path, dict):
                if "default" in file_path:
                    file_path = file_path["default"]
                elif "value" in file_path:
                    file_path = file_path["value"]
                else:
                    file_path = ""
            
            if isinstance(file_type, dict):
                if "default" in file_type:
                    file_type = file_type["default"]
                elif "value" in file_type:
                    file_type = file_type["value"]
                else:
                    file_type = ""
            
            references = []
            
            # Determine search directory
            search_dir = file_path if file_path else os.getcwd()
            
            # Determine file pattern
            file_pattern = f"*{file_type}" if file_type else "*"
            
            # Walk through directory
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(file_type) if file_type else True:
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Find all occurrences of the name
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if name in line:
                                    # Check if it's a valid reference (not just a substring)
                                    # This is a simplified check - in a real implementation, use proper parsing
                                    pattern = r'\b' + re.escape(name) + r'\b'
                                    if re.search(pattern, line):
                                        references.append({
                                            "file": file_path,
                                            "line": i + 1,
                                            "content": line.strip()
                                        })
                        except Exception as e:
                            # Skip files that can't be read
                            continue
            
            return {
                "success": True,
                "name": name,
                "references": references,
                "count": len(references),
                "message": f"Found {len(references)} references to '{name}'"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to find references: {str(e)}"
            }