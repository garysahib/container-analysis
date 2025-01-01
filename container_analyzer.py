#!/usr/bin/env python3



"""

Container Security Analysis Suite

A comprehensive tool for container image analysis, security scanning, and compliance checking.

"""



import subprocess

import json

import os

import sys

import datetime

import requests

import argparse

import logging

import hashlib

import yaml

import threading

import queue

import tempfile

import socket

import nmap

from typing import Dict, List, Tuple

from concurrent.futures import ThreadPoolExecutor

from dataclasses import dataclass

from rich.console import Console

from rich.table import Table

from rich.progress import Progress, SpinnerColumn, TextColumn

from prometheus_client import start_http_server, Gauge, Counter

from kubernetes import client, config

from jenkins import Jenkins

from ruamel.yaml import YAML



# Data Classes for storing results

@dataclass

class ScanResult:

    tool_name: str

    image_name: str

    vulnerabilities: List[Dict]

    metadata: Dict

    timestamp: datetime.datetime



@dataclass

class ComplianceResult:

    framework: str

    checks: List[Dict]

    score: float

    passed_rules: int

    total_rules: int

    timestamp: datetime.datetime



@dataclass

class RuntimeAnalysis:

    falco_events: List[Dict]

    start_time: datetime.datetime

    end_time: datetime.datetime

    critical_events: int

    total_events: int



@dataclass

class NetworkScanResult:

    open_ports: List[int]

    vulnerabilities: List[Dict]

    timestamp: datetime.datetime

    scan_duration: float



@dataclass

class SBOMData:

    components: List[Dict]

    licenses: List[str]

    dependencies: Dict

    timestamp: datetime.datetime



class ContainerAnalyzer:

    """Main class for container image analysis and security scanning."""



    def __init__(self, args=None):

        self.setup_base_configuration(args)

        self.setup_logging()

        self.setup_metrics()

        self.setup_additional_services()



    def setup_base_configuration(self, args):

        """Initialize base configuration."""

        self.image = args.image if args and args.image else "nginx:latest"

        self.slim_image = f"{self.image.split(':')[0]}-slim:latest"

        self.distroless_image = f"{self.image.split(':')[0]}-distroless:latest"

        self.results_dir = "scan_results"

        self.images_dir = "saved_images"

        self.config = self.load_config()

        self.console = Console()



    def setup_logging(self):

        """Configure logging."""

        logging.basicConfig(

            level=logging.INFO,

            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

            handlers=[

                logging.FileHandler('container_analyzer.log'),

                logging.StreamHandler()

            ]

        )

        self.logger = logging.getLogger(__name__)



    def setup_metrics(self):

        """Initialize Prometheus metrics."""

        self.vuln_gauge = Gauge('container_vulnerabilities_total', 

                               'Total vulnerabilities', ['image', 'severity'])

        self.compliance_score = Gauge('compliance_score', 

                                    'Compliance score', ['framework'])

        self.scan_duration = Gauge('scan_duration_seconds', 

                                 'Scan duration', ['tool'])



    def setup_additional_services(self):

        """Setup additional services based on configuration."""

        if self.config.get("kubernetes", {}).get("enabled"):

            self.setup_kubernetes()

        if self.config.get("jenkins", {}).get("enabled"):

            self.setup_jenkins()



    def run_analysis(self):

        """Main analysis workflow."""

        try:

            self.logger.info(f"Starting analysis for image: {self.image}")

            

            # Core Analysis

            self.pull_image()

            security_results = self.run_security_scans()

            sbom_data = self.generate_sbom(self.image)

            

            # Additional Analysis

            if self.config.get("runtime_analysis", {}).get("enabled"):

                runtime_results = self.run_falco_analysis(self.image)

            

            if self.config.get("network_scan", {}).get("enabled"):

                network_results = self.scan_network_vulnerabilities(self.image)

            

            # Compliance

            if self.config.get("compliance", {}).get("enabled"):

                compliance_results = self.run_compliance_checks(self.image)

            

            # Generate Reports

            self.generate_reports(locals())

            

            # Notify

            if self.config.get("notification", {}).get("enabled"):

                self.send_notifications(locals())

            

            self.logger.info("Analysis completed successfully")

            

        except Exception as e:

            self.logger.error(f"Analysis failed: {str(e)}")

            raise



    def run_security_scans(self) -> List[ScanResult]:

        """Run all security scans in parallel."""

        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:

            futures = []

            for scanner in ['dive', 'trivy', 'grype']:

                futures.append(executor.submit(

                    getattr(self, f'scan_with_{scanner}'),

                    self.image,

                    os.path.join(self.results_dir, f'{scanner}_results.json')

                ))

            return [f.result() for f in futures]



    def generate_reports(self, results: Dict):

        """Generate analysis reports in configured formats."""

        for format_type in self.config["export_formats"]:

            self.export_results(results, format_type)



    # ... [Previous methods remain the same]



def main():

    parser = argparse.ArgumentParser(description='Container Security Analysis Suite')

    parser.add_argument('--image', required=True, help='Docker image to analyze')

    parser.add_argument('--config', help='Path to config file')

    parser.add_argument('--ci-mode', action='store_true', help='Run in CI mode')

    parser.add_argument('--export-format', 

                       choices=['json', 'html', 'pdf'],

                       default='all')

    args = parser.parse_args()



    try:

        analyzer = ContainerAnalyzer(args)

        analyzer.run_analysis()

    except Exception as e:

        logging.error(f"Analysis failed: {str(e)}")

        sys.exit(1)



if __name__ == "__main__":

    main()