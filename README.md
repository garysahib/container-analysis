# container-analysis

This is what this script does:

1. **Core Container Analysis**
   - Pulls and analyzes Docker images
   - Uses dive for layer analysis
   - Creates optimized versions (slim and distroless)
   - Saves images with versioning and hash verification

2. **Security Scanning**
   - Trivy vulnerability scanning
   - Grype vulnerability analysis
   - Compares findings with CISA KEV database
   - Runtime security analysis using Falco

3. **SBOM Generation**
   - Uses Syft to generate Software Bill of Materials
   - Lists all components and dependencies
   - Identifies and tracks licenses
   - Creates dependency tree

4. **Policy Enforcement**
   - OPA (Open Policy Agent) integration
   - Custom policy definitions
   - Security policy validation
   - Compliance checking

5. **Kubernetes Analysis**
   - Manifest security analysis
   - RBAC permission checking
   - Resource limits validation
   - Network policy verification

6. **Compliance Checking**
   - CIS Docker Benchmark
   - NIST SP 800-190 framework
   - Compliance scoring
   - Best practices validation

7. **Network Security**
   - Port scanning
   - Service enumeration
   - Vulnerability assessment
   - Network policy validation

8. **Monitoring & Metrics**
   - Prometheus metrics integration
   - Custom metrics for vulnerabilities
   - Runtime analytics
   - Performance monitoring

9. **CI/CD Integration**
   - Jenkins pipeline integration
   - Automated scanning
   - Results reporting
   - Pipeline triggers

10. **Reporting & Notifications**
    - Multiple export formats (JSON, HTML, PDF)
    - Slack notifications
    - Email alerts
    - Rich console output
11. **Keverno policy**
12. **Java runtime dependency analysis**






# Container Security Analysis Suite

## Prerequisites Installation

```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y docker.io nmap python3-venv python3-pip

# Install security tools
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh
curl -sfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh
curl -sfL https://raw.githubusercontent.com/wagoodman/dive/master/install.sh | sh
curl -sfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
curl -sfL https://falco.org/get | sh

# Install docker-slim
curl -sL https://raw.githubusercontent.com/docker-slim/docker-slim/master/scripts/install-dockerslim.sh | sh

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## Requirements.txt
```text
kubernetes
jenkins-python
prometheus_client
rich
pyyaml
ruamel.yaml
python-nmap
requests
dataclasses
```

## Configuration File (container_analyzer_config.yaml)
```yaml
parallel_scans: true
max_workers: 3
severity_threshold: MEDIUM
export_formats:
  - json
  - html
  - pdf
notification:
  slack_webhook: ""
  email: ""
metrics:
  enabled: true
  port: 9090
kubernetes:
  enabled: false
  context: ""
jenkins:
  enabled: false
  url: ""
  username: ""
  token: ""
compliance:
  frameworks:
    - cis
    - nist
runtime_analysis:
  enabled: true
  duration: 300
network_scan:
  enabled: true
  ports: "1-65535"
```

## Directory Structure
```
.
├── container_analyzer.py
├── requirements.txt
├── container_analyzer_config.yaml
├── opa_policies/
│   ├── security.rego
│   └── compliance.rego
├── k8s_manifests/
│   └── deployment.yaml
├── scan_results/
└── saved_images/
```

## Usage Examples

1. Basic Scan:
```bash
python container_analyzer.py --image nginx:latest
```

2. Complete Analysis:
```bash
python container_analyzer.py \
  --image nginx:latest \
  --parallel \
  --export-format html \
  --metrics-port 9090 \
  --severity-threshold HIGH
```

3. CI/CD Integration:
```bash
python container_analyzer.py \
  --image your-image:tag \
  --ci-mode \
  --jenkins-job security-scan
```

4. Kubernetes Analysis:
```bash
python container_analyzer.py \
  --image your-image:tag \
  --k8s-manifests ./k8s_manifests \
  --check-compliance
```

</antArtifact>​​​​​​​​​​​​​​​​

To use this complete script:

1. **Setup the Environment**
```bash
# Create project directory
mkdir container-security-suite
cd container-security-suite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Install Required Tools**
```bash
# Install security tools
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh
curl -sfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh
curl -sfL https://raw.githubusercontent.com/wagoodman/dive/master/install.sh | sh
curl -sfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
curl -sfL https://falco.org/get | sh
```

3. **Create Configuration**
```bash
# Create required directories
mkdir opa_policies k8s_manifests scan_results saved_images

# Create config file (container_analyzer_config.yaml)
```

4. **Run the Analysis**
```bash
# Basic run
python container_analyzer.py --image nginx:latest

# Complete analysis with all features
python container_analyzer.py \
  --image nginx:latest \
  --export-format html \
  --ci-mode
```

5. **Jenkins Integration**
Add this to your Jenkinsfile:
```groovy
pipeline {
    agent any
    stages {
        stage('Security Scan') {
            steps {
                sh 'python container_analyzer.py --image ${IMAGE_NAME} --ci-mode'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'scan_results/**'
                }
            }
        }
    }
}
```
