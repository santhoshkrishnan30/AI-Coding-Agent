import os
import subprocess
import json
from .base import BaseTool
from typing import Dict, Any, List

class RunCommandTool(BaseTool):
    @property
    def name(self) -> str:
        return "run_command"
    
    @property
    def description(self) -> str:
        return "Run a shell command and capture its output"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["command"],
            "optional": {
                "working_directory": {
                    "type": "string",
                    "default": "",
                    "description": "Directory to run the command in"
                }
            }
        }
    
    def execute(self, command: str, working_directory: str = "") -> Dict[str, Any]:
        try:
            # Set working directory
            cwd = working_directory if working_directory else os.getcwd()
            
            # Make sure cwd is a string
            if isinstance(cwd, dict):
                cwd = os.getcwd()
            
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60  # Timeout after 60 seconds
            )
            
            # Prepare output
            output = {
                "success": True,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": f"Command executed with return code {result.returncode}"
            }
            
            # Add command info
            output["command"] = command
            output["working_directory"] = cwd
            
            return output
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 60 seconds",
                "message": "Command execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to run command: {str(e)}"
            }

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
            "required": [],
            "optional": {
                "test_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to tests"
                },
                "test_framework": {
                    "type": "string",
                    "default": "",
                    "description": "Test framework to use"
                }
            }
        }
    
    def execute(self, test_path: str = "", test_framework: str = "") -> Dict[str, Any]:
        try:
            # Detect test framework if not specified
            if not test_framework:
                if os.path.exists("package.json"):
                    with open("package.json", "r") as f:
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
                command = f"pytest {test_path}" if test_path else "pytest"
            elif test_framework == "maven":
                command = "mvn test"
            elif test_framework == "gradle":
                command = "./gradlew test"
            else:
                # Default to a generic test command
                command = f"python -m pytest {test_path}" if test_path else "python -m pytest"
            
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120  # Timeout after 120 seconds for tests
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
                "error": "Tests timed out after 120 seconds",
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
        import re
        
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
        
        return results
    
    def _parse_npm_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        results = {"raw_output": stdout + "\n" + stderr}
        
        # Try to extract Jest results if applicable
        if "Test Suites:" in stdout:
            import re
            
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
        results = {"raw_output": stdout + "\n" + stderr}
        
        # Try to extract test counts
        import re
        
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
        results = {"raw_output": stdout + "\n" + stderr}
        
        # Try to extract test counts
        import re
        
        # Look for test results in the output
        test_pattern = r'(\d+) tests completed, (\d+) failed'
        test_match = re.search(test_pattern, stdout)
        if test_match:
            results["total"] = int(test_match.group(1))
            results["failed"] = int(test_match.group(2))
            results["passed"] = results["total"] - results["failed"]
        
        return results

class BuildProjectTool(BaseTool):
    @property
    def name(self) -> str:
        return "build_project"
    
    @property
    def description(self) -> str:
        return "Build the project using the appropriate build system"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": [],
            "optional": {
                "target": {
                    "type": "string",
                    "default": "",
                    "description": "Build target"
                },
                "configuration": {
                    "type": "string",
                    "default": "release",
                    "description": "Build configuration"
                }
            }
        }
    
    def execute(self, target: str = "", configuration: str = "release") -> Dict[str, Any]:
        try:
            # Determine build system
            build_system = self._detect_build_system()
            
            # Build command based on system
            if build_system == "python":
                command = self._build_python_command(target, configuration)
            elif build_system == "npm":
                command = self._build_npm_command(target, configuration)
            elif build_system == "maven":
                command = self._build_maven_command(target, configuration)
            elif build_system == "gradle":
                command = self._build_gradle_command(target, configuration)
            elif build_system == "make":
                command = self._build_make_command(target, configuration)
            else:
                return {
                    "success": False,
                    "error": "No recognized build system found",
                    "message": "Could not determine how to build this project"
                }
            
            # Show what we're doing
            print(f"Building with {build_system}: {command}")
            
            # Run the build command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # Timeout after 5 minutes
            )
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "build_system": build_system,
                "command": command,
                "message": f"Build completed with {build_system}, return code: {result.returncode}"
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timed out after 5 minutes",
                "message": "Build operation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to build project: {str(e)}"
            }
    
    def _detect_build_system(self) -> str:
        """Detect the build system used by the project"""
        if os.path.exists("setup.py") or os.path.exists("pyproject.toml"):
            return "python"
        elif os.path.exists("package.json"):
            return "npm"
        elif os.path.exists("pom.xml"):
            return "maven"
        elif os.path.exists("build.gradle") or os.path.exists("build.gradle.kts"):
            return "gradle"
        elif os.path.exists("Makefile"):
            return "make"
        else:
            return "unknown"
    
    def _build_python_command(self, target: str, configuration: str) -> str:
        """Generate build command for Python projects"""
        if os.path.exists("setup.py"):
            return f"python setup.py {target if target else 'build'}"
        elif os.path.exists("pyproject.toml"):
            return f"pip install -e . && python -m build {target if target else ''}"
        else:
            return f"pip install -r requirements.txt && python -m pip install -e ."
    
    def _build_npm_command(self, target: str, configuration: str) -> str:
        """Generate build command for Node.js projects"""
        with open("package.json", "r") as f:
            pkg = json.load(f)
        
        if "scripts" in pkg and "build" in pkg["scripts"]:
            # Use the project's build script
            build_script = pkg["scripts"]["build"]
            
            # Add configuration if it's a parameter
            if configuration and configuration != "release":
                return f"npm run build -- --configuration={configuration}"
            else:
                return f"npm run build"
        else:
            # Default build command
            return f"npm install && npm run build"
    
    def _build_maven_command(self, target: str, configuration: str) -> str:
        """Generate build command for Maven projects"""
        config_option = f"-D{configuration}" if configuration and configuration != "release" else ""
        target_option = target if target else "package"
        
        return f"mvn clean {target_option} {config_option}"
    
    def _build_gradle_command(self, target: str, configuration: str) -> str:
        """Generate build command for Gradle projects"""
        config_option = f"-Pconfiguration={configuration}" if configuration and configuration != "release" else ""
        target_option = target if target else "build"
        
        return f"./gradlew clean {target_option} {config_option}"
    
    def _build_make_command(self, target: str, configuration: str) -> str:
        """Generate build command for Make-based projects"""
        config_option = f"CONFIG={configuration}" if configuration and configuration != "release" else ""
        target_option = target if target else "all"
        
        return f"make {config_option} {target_option}"