import os
import subprocess
import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JavaDependencyAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dependencies: Set[str] = set()
        self.runtime_dependencies: Set[str] = set()
        self.is_maven = self._is_maven_project()
        self.is_gradle = self._is_gradle_project()
        
    def _is_maven_project(self) -> bool:
        """Check if project uses Maven."""
        return (self.project_path / "pom.xml").exists()
        
    def _is_gradle_project(self) -> bool:
        """Check if project uses Gradle."""
        return (self.project_path / "build.gradle").exists() or \
               (self.project_path / "build.gradle.kts").exists()

    def analyze_maven_dependencies(self) -> Set[str]:
        """Analyze Maven project dependencies using dependency:tree."""
        try:
            result = subprocess.run(
                ["mvn", "dependency:tree", "-DoutputType=dot"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            dependencies = set()
            for line in result.stdout.split('\n'):
                if ' -> ' in line:  # Dependency relationship in DOT format
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        dep = match.group(1)
                        if ':compile' in dep or ':runtime' in dep:
                            # Remove scope and clean up dependency string
                            clean_dep = dep.split(':')[0:3]  # group:artifact:version
                            dependencies.add(':'.join(clean_dep))
            
            return dependencies
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error analyzing Maven dependencies: {e}")
            return set()

    def analyze_gradle_dependencies(self) -> Set[str]:
        """Analyze Gradle project dependencies."""
        try:
            # Create temporary dependency report task
            with open(self.project_path / "build.gradle", "a") as f:
                f.write("""
task printRuntimeDependencies {
    doLast {
        configurations.runtimeClasspath.resolvedConfiguration.resolvedArtifacts.each { 
            println "${it.moduleVersion.id.group}:${it.moduleVersion.id.name}:${it.moduleVersion.id.version}"
        }
    }
}
""")

            # Run Gradle dependency analysis
            result = subprocess.run(
                ["gradle", "printRuntimeDependencies", "--quiet"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            dependencies = set()
            for line in result.stdout.split('\n'):
                if line.strip():
                    dependencies.add(line.strip())
            
            return dependencies
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error analyzing Gradle dependencies: {e}")
            return set()

    def analyze_imports(self) -> Set[str]:
        """Analyze Java imports in source files."""
        imports = set()
        for java_file in self.project_path.rglob("*.java"):
            try:
                with open(java_file, 'r') as f:
                    content = f.read()
                    # Find all import statements
                    for line in content.split('\n'):
                        if line.strip().startswith('import '):
                            # Extract package name
                            package = line.split()[1].split('.')[0]
                            imports.add(package)
            except Exception as e:
                logger.error(f"Error analyzing {java_file}: {e}")
        return imports

    def analyze_runtime_dependencies(self):
        """Analyze runtime dependencies using JDeps."""
        try:
            # Find the compiled classes directory
            classes_dir = None
            if self.is_maven:
                classes_dir = self.project_path / "target" / "classes"
            elif self.is_gradle:
                classes_dir = self.project_path / "build" / "classes" / "java" / "main"

            if not classes_dir or not classes_dir.exists():
                logger.error("Compiled classes directory not found. Please build the project first.")
                return set()

            result = subprocess.run(
                ["jdeps", "--class-path", str(classes_dir), "-R", "-summary", str(classes_dir)],
                capture_output=True,
                text=True
            )
            
            dependencies = set()
            for line in result.stdout.split('\n'):
                if ' -> ' in line and 'not found' not in line:
                    dep = line.split('->')[1].strip()
                    if not dep.startswith('java.') and not dep.startswith('jdk.'):
                        dependencies.add(dep)
                        
            return dependencies
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error analyzing runtime dependencies: {e}")
            return set()

    def generate_minimal_dockerfile(self, java_version: str = "17") -> str:
        """Generate optimized Dockerfile for Java application."""
        if self.is_maven:
            build_tool = "maven"
            build_file = "pom.xml"
            build_command = "mvn clean package -DskipTests"
            jar_path = "target/*.jar"
        else:
            build_tool = "gradle"
            build_file = "build.gradle"
            build_command = "gradle build -x test"
            jar_path = "build/libs/*.jar"

        dockerfile = f"""# Build stage
FROM eclipse-temurin:{java_version}-jdk-jammy as builder

WORKDIR /app
COPY . .
RUN {build_command}

# Create slim JRE using jlink
RUN $JAVA_HOME/bin/jlink \\
    --add-modules $(jdeps --ignore-missing-deps --list-deps {jar_path}) \\
    --strip-debug \\
    --no-man-pages \\
    --no-header-files \\
    --compress=2 \\
    --output /customjre

# Final stage
FROM debian:slim-bookworm

ENV JAVA_HOME=/jre
ENV PATH="${{JAVA_HOME}}/bin:$PATH"

COPY --from=builder /customjre /jre
COPY --from=builder /app/{jar_path} /app/application.jar

# Create non-root user
RUN useradd -r -u 1000 -U javauser && \\
    chown -R javauser:javauser /app

USER javauser

ENTRYPOINT ["java", "-jar", "/app/application.jar"]
"""
        return dockerfile

def main(project_path: str):
    analyzer = JavaDependencyAnalyzer(project_path)
    
    logger.info("Analyzing project structure...")
    if not (analyzer.is_maven or analyzer.is_gradle):
        logger.error("No Maven or Gradle configuration found!")
        return

    logger.info("Analyzing dependencies...")
    if analyzer.is_maven:
        dependencies = analyzer.analyze_maven_dependencies()
    else:
        dependencies = analyzer.analyze_gradle_dependencies()
    
    logger.info("Analyzing Java imports...")
    imports = analyzer.analyze_imports()
    
    logger.info("Analyzing runtime dependencies...")
    runtime_deps = analyzer.analyze_runtime_dependencies()
    
    # Generate Dockerfile
    dockerfile = analyzer.generate_minimal_dockerfile()
    with open(analyzer.project_path / 'Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    # Print summary
    logger.info("\nSummary:")
    logger.info(f"Build system: {'Maven' if analyzer.is_maven else 'Gradle'}")
    logger.info(f"Total dependencies found: {len(dependencies)}")
    logger.info(f"Java imports found: {len(imports)}")
    logger.info(f"Runtime dependencies: {len(runtime_deps)}")
    logger.info(f"\nDockerfile generated with:")
    logger.info("- Multi-stage build")
    logger.info("- Custom minimal JRE using jlink")
    logger.info("- Non-root user")
    logger.info("- Debian slim base image")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python java_dependency_analyzer.py /path/to/java/project")
        sys.exit(1)
    
    main(sys.argv[1])
