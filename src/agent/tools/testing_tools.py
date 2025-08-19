import os
import subprocess
import json
import re
from typing import Dict, Any, List
from ..tools.base import BaseTool

class RunTestsTool(BaseTool):
    @property
    def name(self) -> str:
        return "run_tests"
    
    @property
    def description(self) -> str:
        return "Run tests for the project"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {
                "test_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to tests (if empty, runs all tests)"
                },
                "test_framework": {
                    "type": "string",
                    "default": "",
                    "description": "Test framework to use (auto-detected if not specified)"
                }
            }
        }
    
    def execute(self, test_path: str = "", test_framework: str = "") -> Dict[str, Any]:
        try:
            # Ensure parameters are strings (fix for parameter validation issue)
            if not isinstance(test_path, str):
                test_path = str(test_path) if test_path is not None else ""
            if not isinstance(test_framework, str):
                test_framework = str(test_framework) if test_framework is not None else ""
            
            # Detect test framework if not specified
            if not test_framework:
                if os.path.exists("package.json"):
                    with open("package.json", 'r') as f:
                        pkg = json.load(f)
                        if "scripts" in pkg and "test" in pkg["scripts"]:
                            test_framework = "npm"
                elif os.path.exists("requirements.txt") or os.path.exists("setup.py"):
                    test_framework = "pytest"
                elif os.path.exists("pom.xml"):
                    test_framework = "maven"
                elif os.path.exists("build.gradle"):
                    test_framework = "gradle"
            
            # Build command based on framework
            if test_framework == "npm":
                command = "npm test"
            elif test_framework == "pytest":
                command = f"pytest {test_path if test_path else ''}"
            elif test_framework == "maven":
                command = "mvn test"
            elif test_framework == "gradle":
                command = "./gradlew test"
            else:
                # Default to a generic test command
                command = f"python -m pytest {test_path if test_path else ''}"
            
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60  # Timeout after 60 seconds for tests
            )
            
            # Parse test results
            test_results = self._parse_test_results(result.stdout, result.stderr, test_framework)
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_framework": test_framework,
                "test_results": test_results,
                "message": f"Tests executed with return code {result.returncode}"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out after 60 seconds",
                "message": "Test execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to run tests: {str(e)}"
            }
    
    def _parse_test_results(self, stdout: str, stderr: str, framework: str) -> Dict[str, Any]:
        # Parse test results based on framework
        if framework == "pytest":
            return self._parse_pytest_results(stdout, stderr)
        elif framework == "npm":
            return self._parse_npm_test_results(stdout, stderr)
        elif framework == "maven":
            return self._parse_maven_test_results(stdout, stderr)
        elif framework == "gradle":
            return self._parse_gradle_test_results(stdout, stderr)
        else:
            return {"raw_output": stdout + "\n" + stderr}
    
    def _parse_pytest_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        # Simple parsing for pytest results
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "failures": []
        }
        
        # Extract test counts
        total_match = re.search(r'(\d+) tested', stdout)
        if total_match:
            results["total"] = int(total_match.group(1))
        
        passed_match = re.search(r'(\d+) passed', stdout)
        if passed_match:
            results["passed"] = int(passed_match.group(1))
        
        failed_match = re.search(r'(\d+) failed', stdout)
        if failed_match:
            results["failed"] = int(failed_match.group(1))
        
        error_match = re.search(r'(\d+) error', stdout)
        if error_match:
            results["errors"] = int(error_match.group(1))
        
        skipped_match = re.search(r'(\d+) skipped', stdout)
        if skipped_match:
            results["skipped"] = int(skipped_match.group(1))
        
        # Extract failure details
        failure_pattern = r'FAILED (.*?)::(.*?)\n(.*?)(?=\nFAILED|\n=|$)'
        failure_matches = re.findall(failure_pattern, stdout, re.DOTALL)
        
        for file_path, test_name, error_msg in failure_matches:
            results["failures"].append({
                "file": file_path,
                "test": test_name,
                "error": error_msg.strip()
            })
        
        return results
    
    def _parse_npm_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        # Simple parsing for npm test results
        results = {
            "raw_output": stdout + "\n" + stderr
        }
        
        # Try to extract Jest results if applicable
        if "Test Suites:" in stdout:
            # Extract test suite results
            suite_pattern = r'Test Suites: (\d+) passed, (\d+) failed, (\d+) total'
            suite_match = re.search(suite_pattern, stdout)
            if suite_match:
                results["suites_passed"] = int(suite_match.group(1))
                results["suites_failed"] = int(suite_match.group(2))
                results["suites_total"] = int(suite_match.group(3))
            
            # Extract test results
            test_pattern = r'Tests: (\d+) passed, (\d+) failed, (\d+) total'
            test_match = re.search(test_pattern, stdout)
            if test_match:
                results["passed"] = int(test_match.group(1))
                results["failed"] = int(test_match.group(2))
                results["total"] = int(test_match.group(3))
        
        return results
    
    def _parse_maven_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        # Simple parsing for Maven test results
        results = {
            "raw_output": stdout + "\n" + stderr
        }
        
        # Look for test results in the output
        test_pattern = r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)'
        test_match = re.search(test_pattern, stdout)
        if test_match:
            results["total"] = int(test_match.group(1))
            results["failures"] = int(test_match.group(2))
            results["errors"] = int(test_match.group(3))
            results["skipped"] = int(test_match.group(4))
            results["passed"] = results["total"] - results["failures"] - results["errors"] - results["skipped"]
        
        return results
    
    def _parse_gradle_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        # Simple parsing for Gradle test results
        results = {
            "raw_output": stdout + "\n" + stderr
        }
        
        # Look for test results in the output
        test_pattern = r'(\d+) tests completed, (\d+) failed'
        test_match = re.search(test_pattern, stdout)
        if test_match:
            results["total"] = int(test_match.group(1))
            results["failed"] = int(test_match.group(2))
            results["passed"] = results["total"] - results["failed"]
        
        return results

class GenerateTestTool(BaseTool):
    @property
    def name(self) -> str:
        return "generate_test"
    
    @property
    def description(self) -> str:
        return "Generate unit tests for a function or class"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["file_path", "function_name"],
            "optional": {
                "test_framework": {
                    "type": "string",
                    "default": "",
                    "description": "Test framework to use (auto-detected if not specified)"
                }
            }
        }
    
    def execute(self, file_path: str = "", function_name: str = "", test_framework: str = "") -> Dict[str, Any]:
        try:
            # Ensure parameters are strings (fix for parameter validation issue)
            if not isinstance(file_path, str):
                file_path = str(file_path) if file_path is not None else ""
            if not isinstance(function_name, str):
                function_name = str(function_name) if function_name is not None else ""
            if not isinstance(test_framework, str):
                test_framework = str(test_framework) if test_framework is not None else ""
            
            # Read the source file
            with open(file_path, 'r') as f:
                source_code = f.read()
            
            # Detect test framework if not specified
            if not test_framework:
                if file_path.endswith('.py'):
                    test_framework = "pytest"
                elif file_path.endswith('.js') or file_path.endswith('.ts'):
                    test_framework = "jest"
                elif file_path.endswith('.java'):
                    test_framework = "junit"
                else:
                    test_framework = "generic"
            
            # Extract the function or class code
            function_code = self._extract_function_code(source_code, function_name)
            
            if not function_code:
                return {
                    "success": False,
                    "error": f"Function or class '{function_name}' not found in {file_path}",
                    "message": f"Could not find '{function_name}' in the specified file"
                }
            
            # Generate test code using LLM
            test_code = self._generate_test_code(function_code, function_name, test_framework)
            
            # Determine test file path
            test_file_path = self._get_test_file_path(file_path, test_framework)
            
            return {
                "success": True,
                "test_code": test_code,
                "test_file_path": test_file_path,
                "test_framework": test_framework,
                "message": f"Generated {test_framework} tests for {function_name}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate tests: {str(e)}"
            }
    
    def _extract_function_code(self, source_code: str, function_name: str) -> str:
        # Extract function or class code from source
        # This is a simplified implementation - in a real implementation, use proper AST parsing
        
        if source_code.endswith('.py'):
            # For Python files
            import ast
            try:
                tree = ast.parse(source_code)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        # Get the function code
                        lines = source_code.split('\n')
                        start_line = node.lineno - 1  # Convert to 0-based indexing
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                        
                        return '\n'.join(lines[start_line:end_line])
                    
                    elif isinstance(node, ast.ClassDef) and node.name == function_name:
                        # Get the class code
                        lines = source_code.split('\n')
                        start_line = node.lineno - 1  # Convert to 0-based indexing
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                        
                        return '\n'.join(lines[start_line:end_line])
            except:
                # Fall back to regex if AST parsing fails
                pass
        
        # Fallback to regex for other languages or if AST parsing fails
        # Try to find function definition
        function_pattern = rf'(def|function|class)\s+{re.escape(function_name)}\s*[\(=:][^{{]*{{?'
        match = re.search(function_pattern, source_code)
        
        if not match:
            return None
        
        # Find the start and end of the function
        start_pos = match.start()
        lines = source_code[start_pos:].split('\n')
        
        # Simple heuristic to find the end of the function
        indent_level = len(lines[0]) - len(lines[0].lstrip())
        end_pos = start_pos
        
        for line in lines[1:]:
            current_indent = len(line) - len(line.lstrip())
            if line.strip() and current_indent <= indent_level and not line.strip().startswith('#'):
                break
            end_pos += len(line) + 1  # +1 for newline
        
        return source_code[start_pos:end_pos]
    
    def _generate_test_code(self, function_code: str, function_name: str, test_framework: str) -> str:
        # Generate test code using LLM
        # For now, return a placeholder
        if test_framework == "pytest":
            return f"""
import pytest
from {function_name.split('.')[0]} import {function_name.split('.')[-1]}

def test_{function_name}():
    # TODO: Implement test
    assert True
"""
        elif test_framework == "jest":
            return f"""
const {{ {function_name} }} = require('./{function_name.split('.')[0]}');

test('{function_name}', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
}});
"""
        elif test_framework == "junit":
            return f"""
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class {function_name}Test {{
    @Test
    public void test{function_name}() {{
        // TODO: Implement test
        assertTrue(true);
    }}
}}
"""
        else:
            return f"""
// Test for {function_name}
// TODO: Implement test
assert(true);
"""
    
    def _get_test_file_path(self, source_file_path: str, test_framework: str) -> str:
        # Determine the test file path based on conventions
        import os
        
        directory = os.path.dirname(source_file_path)
        filename = os.path.basename(source_file_path)
        name, ext = os.path.splitext(filename)
        
        if test_framework == "pytest":
            # Python convention: test_<module>.py or <module>_test.py
            test_dir = os.path.join(directory, "tests")
            if not os.path.exists(test_dir):
                test_dir = directory
            
            test_filename = f"test_{name}.py"
            return os.path.join(test_dir, test_filename)
        
        elif test_framework == "jest":
            # JavaScript convention: <module>.test.js or <module>.spec.js
            test_dir = os.path.join(directory, "__tests__")
            if not os.path.exists(test_dir):
                test_dir = directory
            
            test_filename = f"{name}.test.js"
            return os.path.join(test_dir, test_filename)
        
        elif test_framework == "junit":
            # Java convention: <name>Test.java in test directory
            src_index = directory.rfind("src")
            if src_index != -1:
                base_path = directory[:src_index]
                test_dir = os.path.join(base_path, "src", "test", "java", directory[src_index+4:])
            else:
                test_dir = os.path.join(directory, "test")
            
            test_filename = f"{name}Test.java"
            return os.path.join(test_dir, test_filename)
        
        else:
            # Generic convention: test_<name>.<ext>
            test_dir = os.path.join(directory, "test")
            if not os.path.exists(test_dir):
                test_dir = directory
            
            test_filename = f"test_{name}{ext}"
            return os.path.join(test_dir, test_filename)