"""DAG visualization command implementation.

Generates and displays the Snakemake workflow DAG (Directed Acyclic Graph).
"""

import sys
import subprocess
import tempfile
from pathlib import Path

import click
import yaml
from loguru import logger
from pydantic import ValidationError

from src.domain.catalog import load_catalog
from collections import defaultdict


def generate_execution_graph(results_dir: Path) -> str:
    """Generate DOT graph from actual execution results.

    Args:
        results_dir: Path to Snakemake results directory

    Returns:
        DOT format graph string
    """
    # Count jobs by type
    job_counts = defaultdict(int)
    files_discovered = []
    files_with_matches = []

    # Check manifests
    manifest_dir = results_dir / "manifests"
    if manifest_dir.exists():
        for manifest_file in manifest_dir.glob("*_files.txt"):
            with open(manifest_file) as f:
                files = [line.strip() for line in f if line.strip()]
                files_discovered.extend(files)
                error_id = manifest_file.stem.replace("_files", "")
                job_counts[f"discover_files_{error_id}"] = 1

    # Count fingerprint jobs
    fingerprint_dir = results_dir / "fingerprints"
    if fingerprint_dir.exists():
        for error_dir in fingerprint_dir.iterdir():
            if error_dir.is_dir():
                count = len(list(error_dir.glob("*.json")))
                job_counts[f"fingerprint_file_{error_dir.name}"] = count

    # Count match jobs
    matches_dir = results_dir / "matches"
    if matches_dir.exists():
        for error_dir in matches_dir.iterdir():
            if error_dir.is_dir():
                count = len(list(error_dir.glob("*.json")))
                job_counts[f"match_pattern_{error_dir.name}"] = count

    # Count filtered files
    filtered_dir = results_dir / "filtered"
    if filtered_dir.exists():
        for filtered_file in filtered_dir.glob("*_files_with_matches.txt"):
            with open(filtered_file) as f:
                files = [line.strip() for line in f if line.strip()]
                files_with_matches.extend(files)
                error_id = filtered_file.stem.replace("_files_with_matches", "")
                job_counts[f"filter_matches_{error_id}"] = 1

    # Count extract_context jobs
    results_results_dir = results_dir / "results"
    if results_results_dir.exists():
        for error_dir in results_results_dir.iterdir():
            if error_dir.is_dir():
                count = len(list(error_dir.glob("*_matches.json")))
                job_counts[f"extract_context_{error_dir.name}"] = count

    # Generate DOT graph
    lines = []
    lines.append("digraph execution_dag {")
    lines.append('    graph[bgcolor=white, margin=0, rankdir=TB];')
    lines.append('    node[shape=box, style=rounded, fontname=sans, fontsize=10, penwidth=2];')
    lines.append('    edge[penwidth=2, color=grey];')
    lines.append('')

    node_id = 0
    node_map = {}

    # Create nodes for each job type
    for job_name, count in sorted(job_counts.items()):
        job_type = job_name.split('_')[0]

        if count > 1:
            label = f"{job_name}\\n({count} jobs)"
        else:
            label = job_name

        # Color by job type
        colors = {
            'discover': '0.15 0.6 0.85',
            'fingerprint': '0.30 0.6 0.85',
            'match': '0.45 0.6 0.85',
            'filter': '0.60 0.6 0.85',
            'extract': '0.75 0.6 0.85',
        }
        color = colors.get(job_type, '0.50 0.6 0.85')

        lines.append(f'    {node_id}[label="{label}", color="{color}", style="rounded,filled", fillcolor="white"];')
        node_map[job_name] = node_id
        node_id += 1

    lines.append('')

    # Create edges (simplified workflow)
    for job_name in sorted(job_counts.keys()):
        if job_name.startswith('discover_files_'):
            error_id = job_name.replace('discover_files_', '')
            finger_job = f'fingerprint_file_{error_id}'
            if finger_job in node_map:
                lines.append(f'    {node_map[job_name]} -> {node_map[finger_job]};')

        elif job_name.startswith('fingerprint_file_'):
            error_id = job_name.replace('fingerprint_file_', '')
            match_job = f'match_pattern_{error_id}'
            if match_job in node_map:
                lines.append(f'    {node_map[job_name]} -> {node_map[match_job]};')

        elif job_name.startswith('match_pattern_'):
            error_id = job_name.replace('match_pattern_', '')
            filter_job = f'filter_matches_{error_id}'
            if filter_job in node_map:
                lines.append(f'    {node_map[job_name]} -> {node_map[filter_job]};')

        elif job_name.startswith('filter_matches_'):
            error_id = job_name.replace('filter_matches_', '')
            extract_job = f'extract_context_{error_id}'
            if extract_job in node_map:
                lines.append(f'    {node_map[job_name]} -> {node_map[extract_job]};')

    lines.append("}")

    # Log summary
    logger.info(f"Execution summary: {len(files_discovered)} files discovered, {sum(job_counts.values())} total jobs")

    return "\n".join(lines)


@click.command()
@click.option(
    "--catalog",
    required=True,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Path to error catalog YAML file"
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, resolve_path=True),
    help="Save DAG to file (supports .dot, .png, .pdf, .svg)"
)
@click.option(
    "--format",
    type=click.Choice(["dot", "png", "pdf", "svg"], case_sensitive=False),
    default="dot",
    help="Output format [default: dot]"
)
@click.option(
    "--graph-type",
    type=click.Choice(["dag", "rulegraph", "filegraph", "execution", "all"], case_sensitive=False),
    default="rulegraph",
    help="Graph type: dag (all jobs), rulegraph (rules only), filegraph (file flow), execution (from results), all (generate all) [default: rulegraph]"
)
@click.option(
    "--results-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Results directory for execution graph (required for --graph-type execution)"
)
@click.option(
    "--open",
    "open_file",
    is_flag=True,
    help="Open the generated file after creation (requires --output)"
)
def dag(catalog, output, format, graph_type, results_dir, open_file):
    """Visualize workflow DAG (Directed Acyclic Graph).

    Generates a visual representation of the Snakemake workflow graph showing
    all rules, dependencies, and execution order.

    \b
    Graph types:
        rulegraph  - Shows abstract workflow rules and dependencies (default)
        dag        - Shows planned jobs (before checkpoint expansion)
        filegraph  - Shows file flow through the workflow
        execution  - Shows ACTUAL executed jobs with counts (requires --results-dir)
        all        - Generates all four graph types

    \b
    Examples:
        # Show rule graph in terminal
        $ as-scan dag --catalog errors.yaml

        # Show actual execution with job counts (after a scan)
        $ as-scan dag --catalog errors.yaml --graph-type execution --results-dir ./results --output execution.png

        # Save rule graph as PNG
        $ as-scan dag --catalog errors.yaml --output workflow.png --format png

        # Generate all graph types
        $ as-scan dag --catalog errors.yaml --graph-type all --results-dir ./results --output graphs --format png
    """
    try:
        # Load and validate catalog
        logger.info(f"Loading catalog from {catalog}")
        try:
            error_catalog = load_catalog(catalog)
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {catalog}")
            sys.exit(1)
        except ValidationError as e:
            logger.error(f"Invalid catalog format: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            sys.exit(1)

        logger.success(f"Loaded catalog '{error_catalog.metadata.name}'")

        # Create temporary directory for workflow config
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create workflow configuration
            config_data = {
                "catalog_path": str(catalog),
                "output_dirs": {
                    "manifests": str(tmp_path / "manifests"),
                    "fingerprints": str(tmp_path / "fingerprints"),
                    "matches": str(tmp_path / "matches"),
                    "filtered": str(tmp_path / "filtered"),
                    "results": str(tmp_path / "results"),
                    "aggregated": str(tmp_path / "aggregated"),
                    "railway": str(tmp_path / "railway"),
                }
            }

            # Write temporary config file
            config_file = tmp_path / "workflow_config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            # Get Snakefile path
            snakefile_path = Path(__file__).parent.parent.parent / "orchestration" / "Snakefile"
            if not snakefile_path.exists():
                logger.error(f"Snakefile not found at {snakefile_path}")
                sys.exit(1)

            # Determine which graph types to generate
            if graph_type == "all":
                graph_types = ["dag", "rulegraph", "filegraph", "execution"]
            elif graph_type == "execution":
                # Execution graph requires results directory
                if not results_dir:
                    logger.error("--results-dir is required for --graph-type execution")
                    sys.exit(1)
                graph_types = ["execution"]
            else:
                graph_types = [graph_type]

            generated_files = []

            # Generate each graph type
            for gtype in graph_types:
                # Handle execution graph separately (doesn't use Snakemake)
                if gtype == "execution":
                    if not results_dir:
                        if graph_type == "all":
                            logger.warning("Skipping execution graph (no --results-dir specified)")
                            continue
                        else:
                            logger.error("--results-dir is required for execution graph")
                            sys.exit(1)

                    logger.info(f"Generating execution graph from {results_dir}...")
                    try:
                        dot_content = generate_execution_graph(Path(results_dir))
                    except Exception as e:
                        logger.error(f"Failed to generate execution graph: {e}")
                        if graph_type == "all":
                            continue
                        else:
                            sys.exit(1)
                else:
                    # Build Snakemake command for graph generation
                    cmd = [
                        "snakemake",
                        "--snakefile", str(snakefile_path),
                        "--configfile", str(config_file),
                        f"--{gtype}"
                    ]

                    logger.info(f"Generating workflow {gtype}...")
                    logger.debug(f"Executing: {' '.join(cmd)}")

                    # Execute Snakemake to get graph in DOT format
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        logger.error(f"Failed to generate {gtype}")
                        logger.error(result.stderr)
                        if graph_type == "all":
                            continue  # Try next graph type
                        else:
                            sys.exit(1)

                    dot_content = result.stdout

                # Handle output for this graph type
                if output:
                    # Determine output path for this specific graph type
                    if graph_type == "all":
                        # Create separate files for each graph type
                        base_path = Path(output)
                        if base_path.suffix:
                            # Has extension: workflow.png -> workflow_rulegraph.png
                            output_path = base_path.with_stem(f"{base_path.stem}_{gtype}")
                        else:
                            # No extension: assume directory or base name
                            output_path = Path(f"{output}_{gtype}")
                    else:
                        output_path = Path(output)

                    # Determine format from file extension if not specified
                    current_format = format
                    if current_format == "dot" and output_path.suffix in ['.png', '.pdf', '.svg']:
                        current_format = output_path.suffix[1:]  # Remove the dot

                    if current_format == "dot":
                        # Save DOT format directly
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "w") as f:
                            f.write(dot_content)
                        logger.success(f"{gtype.upper()} saved to {output_path}")
                        generated_files.append(output_path)
                    else:
                        # Convert to image format using graphviz
                        try:
                            # Check if graphviz is available
                            subprocess.run(["dot", "-V"], capture_output=True, check=True)

                            # Convert DOT to specified format
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            convert_cmd = [
                                "dot",
                                f"-T{current_format}",
                                "-o", str(output_path)
                            ]

                            convert_result = subprocess.run(
                                convert_cmd,
                                input=dot_content,
                                text=True,
                                capture_output=True
                            )

                            if convert_result.returncode != 0:
                                logger.error(f"Failed to convert {gtype} to {current_format}")
                                logger.error(convert_result.stderr)
                                if graph_type == "all":
                                    continue  # Try next graph type
                                else:
                                    sys.exit(1)

                            logger.success(f"{gtype.upper()} saved to {output_path} ({current_format.upper()} format)")
                            generated_files.append(output_path)

                        except FileNotFoundError:
                            logger.error("Graphviz 'dot' command not found")
                            logger.error("To generate image formats, install graphviz:")
                            logger.error("  - Ubuntu/Debian: sudo apt install graphviz")
                            logger.error("  - macOS: brew install graphviz")
                            logger.error("  - Or save as .dot and use online viewers")
                            if graph_type != "all":
                                sys.exit(1)
                else:
                    # Print DOT format to stdout
                    if graph_type == "all":
                        print(f"\n# {gtype.upper()}\n")
                    print(dot_content)
                    if gtype == graph_types[-1]:  # Last one
                        logger.info("Tip: Pipe to 'dot' or save with --output")
                        logger.info("  Example: as-scan dag --catalog errors.yaml | dot -Tpng > dag.png")

            # Open files if requested (after all are generated)
            if output and open_file and generated_files:
                for file_path in generated_files:
                    logger.info(f"Opening {file_path}...")
                    try:
                        # Try platform-specific open commands
                        if sys.platform == "darwin":
                            subprocess.run(["open", str(file_path)])
                        elif sys.platform == "linux":
                            subprocess.run(["xdg-open", str(file_path)])
                        elif sys.platform == "win32":
                            subprocess.run(["start", str(file_path)], shell=True)
                        else:
                            logger.warning(f"Cannot auto-open file on platform: {sys.platform}")
                    except Exception as e:
                        logger.warning(f"Failed to open file: {e}")

    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
