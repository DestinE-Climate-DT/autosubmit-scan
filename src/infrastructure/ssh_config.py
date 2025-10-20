"""SSH configuration parsing utilities.

Provides centralized SSH config parsing for host aliases.
"""

import os
from pathlib import Path
from typing import Dict


class SSHConfigParser:
    """Parse SSH configuration files for host details."""

    @staticmethod
    def parse_host(alias: str, config_path: Path | None = None) -> Dict[str, str | int | None]:
        """Parse SSH config to get connection details for a host alias.

        Reads ~/.ssh/config and extracts connection parameters for the given
        host alias. Falls back to sensible defaults if config doesn't exist
        or host is not found.

        Parameters
        ----------
        alias : str
            SSH host alias (e.g., 'mn5', 'lumi', 'climatedt-wf')
        config_path : Path | None, optional
            Path to SSH config file. If None, defaults to ~/.ssh/config

        Returns
        -------
        Dict[str, str | int | None]
            Dictionary with keys:
                - hostname : str
                    Real hostname or IP address (defaults to alias if not found)
                - user : str
                    Username for SSH connection (defaults to $USER)
                - port : int
                    Port number (defaults to 22)
                - identity_file : str | None
                    Path to SSH key file (None if not specified)

        Examples
        --------
        >>> config = SSHConfigParser.parse_host('myserver')
        >>> print(config['hostname'])
        'myserver.example.com'
        >>> print(config['user'])
        'myusername'
        >>> print(config['port'])
        22

        Notes
        -----
        This method is designed to be fault-tolerant:
        - Returns defaults if config file doesn't exist
        - Returns defaults if host alias not found
        - Continues parsing even if individual lines fail
        """
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        # Default configuration
        config = {
            "hostname": alias,  # Default to alias if not found
            "user": os.getenv("USER"),
            "port": 22,
            "identity_file": None,
        }

        # If config file doesn't exist, return defaults
        if not config_path.exists():
            return config

        try:
            in_target_host = False

            with open(config_path) as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # New Host section
                    if line.startswith("Host "):
                        host_line = line[5:].strip()
                        # Check if this is our target host
                        hosts_in_line = host_line.split()
                        in_target_host = alias in hosts_in_line
                        continue

                    # Parse config options for our target host
                    if in_target_host and line:
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            key, value = parts
                            key_lower = key.lower()

                            if key_lower == "hostname":
                                config["hostname"] = value
                            elif key_lower == "user":
                                config["user"] = value
                            elif key_lower == "port":
                                try:
                                    config["port"] = int(value)
                                except ValueError:
                                    pass
                            elif key_lower == "identityfile":
                                # Expand ~ in identity file path
                                identity_path = os.path.expanduser(value)
                                config["identity_file"] = identity_path

        except Exception:
            # If parsing fails, return defaults
            pass

        return config

    @staticmethod
    def get_hosts(config_path: Path | None = None) -> list[str]:
        """Get list of host aliases from SSH config.

        Extracts all Host entries from SSH config, excluding wildcards.
        Useful for autocompletion and host discovery.

        Parameters
        ----------
        config_path : Path | None, optional
            Path to SSH config file. If None, defaults to ~/.ssh/config

        Returns
        -------
        list[str]
            List of host aliases (excluding wildcards like * or ?)

        Examples
        --------
        >>> hosts = SSHConfigParser.get_hosts()
        >>> print(hosts)
        ['server1', 'server2', 'myhost']

        Notes
        -----
        - Skips entries with wildcards (* or ?)
        - Returns empty list if config doesn't exist
        - Handles multiple hosts on single line
        """
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        hosts = []

        if not config_path.exists():
            return hosts

        try:
            with open(config_path) as f:
                for line in f:
                    line = line.strip()

                    # Match "Host <hostname>" or "Host <pattern>"
                    if line.startswith("Host ") and not line.startswith("Host *"):
                        host_line = line[5:].strip()
                        # Skip patterns with wildcards
                        if "*" not in host_line and "?" not in host_line:
                            # Can have multiple hosts on one line
                            for host in host_line.split():
                                if host and host not in hosts:
                                    hosts.append(host)
        except Exception:
            pass

        return hosts
