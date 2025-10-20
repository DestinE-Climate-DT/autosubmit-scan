# Building the Documentation

This guide explains how to build and preview the autosubmit-scan documentation locally.

## Prerequisites

- Python >= 3.12
- pixi (recommended) or pip
- Git

## Option 1: Build with Jupyter Book (Recommended)

### Install Dependencies

```bash
# Using pixi (recommended)
pixi install
pixi run python -m pip install -r docs/requirements.txt

# Or using pip directly
pip install -r docs/requirements.txt

# Install the package in editable mode (required for autodoc)
pip install -e .
```

**Important**: The package must be installed (`pip install -e .`) for autodoc to import and document the source code modules.

### Build the Documentation

```bash
# Build HTML documentation
jupyter-book build docs/

# The output will be in docs/_build/html/
```

### Preview Locally

```bash
# Open in browser
open docs/_build/html/index.html  # macOS
xdg-open docs/_build/html/index.html  # Linux
start docs/_build/html/index.html  # Windows

# Or use Python's built-in HTTP server
cd docs/_build/html
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

### Clean Build

```bash
# Remove build artifacts
jupyter-book clean docs/

# Remove build artifacts and cached outputs
jupyter-book clean docs/ --all
```

## Option 2: Build with Sphinx

If you prefer using Sphinx directly (useful for debugging):

```bash
# Build HTML documentation
cd docs
sphinx-build -b html . _build/html

# Build with verbose output
sphinx-build -v -b html . _build/html

# Build PDF (requires LaTeX)
sphinx-build -b latex . _build/latex
cd _build/latex
make
```

**Note**: When building with `sphinx-build`, you may see warnings about missing toctree entries. These are expected if stub files haven't been created yet.

## Building for Read the Docs

Read the Docs will automatically build the documentation when you push to the repository. The configuration is in `.readthedocs.yml`.

### Local Read the Docs Build

To test the Read the Docs build locally:

```bash
# Install Read the Docs build tools
pip install readthedocs-sphinx-ext

# Build
cd docs
sphinx-build -b html . _build/html
```

## Notebook Execution

Jupyter Book can execute notebooks during the build:

### Execute All Notebooks

```bash
# Execute notebooks and build
jupyter-book build docs/ --execute
```

### Skip Notebook Execution

```bash
# Build without executing notebooks
jupyter-book build docs/ --execute-skip
```

### Configure Execution

Edit `docs/_config.yml`:

```yaml
execute:
  execute_notebooks: auto  # auto, force, off, cache
  timeout: 180  # Execution timeout in seconds
  allow_errors: false  # Stop on errors
```

## Common Issues

### Module Import Errors

If notebooks can't import the `src` module:

```bash
# Install package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Missing Dependencies

```bash
# Install all documentation dependencies
pip install -r docs/requirements.txt

# Install the project with all extras
pip install -e ".[dev,docs,test]"
```

### Notebook Execution Timeouts

Increase timeout in `docs/_config.yml`:

```yaml
execute:
  timeout: 300  # 5 minutes
```

### Memory Issues with Large Notebooks

```bash
# Limit parallel execution
jupyter-book build docs/ --execute --jobs 1
```

## Building Specific Formats

### HTML (default)

```bash
jupyter-book build docs/
```

### PDF (requires LaTeX)

```bash
jupyter-book build docs/ --builder latex
cd docs/_build/latex
make
```

### EPUB

```bash
jupyter-book build docs/ --builder epub
```

## Continuous Integration

The documentation is automatically built on:
- Pull requests to `main` branch
- Pushes to `main` branch
- Tagged releases

See `.github/workflows/docs.yml` for the CI configuration.

## Development Workflow

### Watch for Changes

```bash
# Install sphinx-autobuild
pip install sphinx-autobuild

# Auto-rebuild on changes
sphinx-autobuild docs docs/_build/html --open-browser
```

### Fast Iteration

```bash
# Build only changed files
jupyter-book build docs/ --builder html --path-output _build/html

# Skip notebook execution for speed
jupyter-book build docs/ --execute-skip
```

## Troubleshooting

### Check Configuration

```bash
# Validate _config.yml syntax
jupyter-book config sphinx docs/
```

### Verbose Build

```bash
# Show detailed build information
jupyter-book build docs/ --verbose
```

### Debug Notebook Execution

```bash
# Execute notebooks manually
jupyter nbconvert --to notebook --execute tutorials/01_getting_started.ipynb
```

## See Also

- [Jupyter Book Documentation](https://jupyterbook.org/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Documentation](https://docs.readthedocs.io/)
- [MyST Markdown Syntax](https://myst-parser.readthedocs.io/)
