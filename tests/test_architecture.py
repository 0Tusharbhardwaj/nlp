"""Architectural integrity and configuration validation tests for SecureCode AI.

Compatible with both unittest (standard library) and pytest.
"""

from pathlib import Path
import unittest

from src.utils.config import get_project_root, load_config


class TestProjectArchitecture(unittest.TestCase):
    """Test suite verifying directory structure, files, configurations, and git rules."""

    def setUp(self):
        self.root = get_project_root()

    def test_directory_structure_exists(self):
        """Verify that all core directories defined in the project architecture exist."""
        required_directories = [
            self.root / "datasets" / "raw",
            self.root / "datasets" / "processed",
            self.root / "datasets" / "external",
            self.root / "datasets" / "reports",
            self.root / "notebooks",
            self.root / "src" / "data",
            self.root / "src" / "preprocessing",
            self.root / "src" / "models",
            self.root / "src" / "training",
            self.root / "src" / "evaluation",
            self.root / "src" / "inference",
            self.root / "src" / "utils",
            self.root / "backend" / "app" / "api",
            self.root / "backend" / "app" / "services",
            self.root / "backend" / "app" / "schemas",
            self.root / "backend" / "app" / "core",
            self.root / "frontend",
            self.root / "configs",
            self.root / "scripts",
            self.root / "tests",
            self.root / "results",
            self.root / "docs",
        ]
        
        missing = [str(d.relative_to(self.root)) for d in required_directories if not d.is_dir()]
        self.assertEqual(len(missing), 0, f"Missing required directories: {missing}")

    def test_core_files_exist(self):
        """Verify that all Phase 1 documentation, config, and setup files exist."""
        required_files = [
            self.root / "README.md",
            self.root / "requirements.txt",
            self.root / ".gitignore",
            self.root / ".env.example",
            self.root / "configs" / "base.yaml",
            self.root / "docs" / "PROJECT_ARCHITECTURE.md",
            self.root / "docs" / "EXPERIMENT_PLAN.md",
        ]
        
        missing = [str(f.relative_to(self.root)) for f in required_files if not f.is_file()]
        self.assertEqual(len(missing), 0, f"Missing required files: {missing}")

    def test_config_loader_and_schema(self):
        """Verify that base.yaml is valid YAML and contains required top-level configuration sections."""
        config = load_config()
        required_sections = [
            "project",
            "system",
            "paths",
            "datasets",
            "preprocessing",
            "baselines",
            "codebert",
            "experiments",
            "metrics",
            "backend",
        ]
        
        for section in required_sections:
            self.assertIn(section, config, f"Missing section '{section}' in configs/base.yaml")

        self.assertEqual(config["project"]["name"], "SecureCode-AI")
        self.assertEqual(config["codebert"]["model_name_or_path"], "microsoft/codebert-base")
        self.assertEqual(config["preprocessing"]["max_sequence_length"], 512)

    def test_gitignore_rules(self):
        """Verify that .gitignore safely excludes data, checkpoints, venvs, and secrets."""
        gitignore_path = self.root / ".gitignore"
        self.assertTrue(gitignore_path.is_file(), ".gitignore does not exist")
        
        content = gitignore_path.read_text(encoding="utf-8")
        
        critical_patterns = [
            "datasets/raw/*",
            "datasets/processed/*",
            "checkpoints/",
            "*.pt",
            ".env",
            "venv/",
        ]
        
        for pattern in critical_patterns:
            self.assertIn(pattern, content, f"Pattern '{pattern}' missing from .gitignore")


if __name__ == "__main__":
    unittest.main()
