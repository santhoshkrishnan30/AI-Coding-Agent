import os
import subprocess
import json
from typing import Dict, Any
from ..tools.base import BaseTool

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
        with open("package.json", 'r') as f:
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