# NetCDF Explorer MCP Server

A simple and powerful MCP (Message Communication Protocol) server for exploring, analyzing, and interacting with NetCDF format files. Designed to simplify NetCDF data management with intuitive APIs and efficient data handling.


## Overview

NetCDF (Network Common Data Form) is a widely used format for storing scientific data. This MCP server provides a streamlined interface to work with NetCDF files, offering essential functionalities to list files, inspect structures, extract data, and analyze variables—all while handling large datasets efficiently through smart sampling.


## Features

- 📁 **File Discovery**: List all NetCDF files (`.nc`, `.cdf`, `.netcdf`, `.nc4`) in a specified directory.
- 🔍 **Structure Inspection**: Retrieve detailed metadata of NetCDF files, including dimensions, variables, attributes, and global properties.
- 📊 **Data Extraction**: Read variable data with support for flexible slicing (e.g., `lat: "0:10:2"` to extract subsets).
- 🧠 **Smart Sampling**: Automatically sample large datasets to prevent memory overflow, with configurable element limits.
- ⏰ **Time Series Analysis**: Extract temporal data from spatial variables, with optional custom location coordinates.
- 🔎 **Search Functionality**: Find variables and attributes by keyword, simplifying navigation in complex files.
- 📋 **Variable Summaries**: Generate human-readable summaries of variables, including dimensions, data types, and attributes.


## Installation

### Prerequisites
- Python ≥ 3.13


### Install via pip
```bash
pip install nc-mcp
```

### Install from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/HanchaoLi/nc-mcp.git
   cd nc-mcp
   ```

2. Install dependencies (using `uv` for faster dependency management):
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies
   uv sync --all-groups
   ```


## Quick Start

### Start the Server
```bash
python -m nc_mcp_server.main
```

## API Reference

### Core Functions

| Function               | Description                                                                 | Parameters                                                                 |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `list_netcdf_files`    | Lists all NetCDF files in a directory.                                      | `directory` (str): Path to search (default: `.`).                          |
| `get_netcdf_info`      | Returns metadata and structure of a NetCDF file (dimensions, variables, attributes). | `file_path` (str): Path to the NetCDF file.                                |
| `get_variable_data`    | Extracts data from a specific variable (supports slicing and sampling).     | `file_path` (str), `variable_name` (str), `slices` (dict, optional), `max_elements` (int, default: 1000). |
| `search_variables`     | Searches variables and attributes for a keyword (case-insensitive).         | `file_path` (str), `search_term` (str).                                    |
| `extract_timeseries`   | Extracts time series data from a spatial variable.                          | `file_path` (str), `variable_name` (str), `location` (dict, optional: spatial coordinates like `{"lat": 10, "lon": 20}`). |


## Testing

Run the test suite to verify functionality:
```bash
uv run pytest tests/ -v
```

Tests cover:
- File discovery logic
- NetCDF structure parsing
- Data extraction with slicing
- Sampling for large datasets
- Error handling for invalid inputs


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Links

- **Homepage**: [https://github.com/HanchaoLi/nc-mcp](https://github.com/HanchaoLi/nc-mcp)
- **Repository**: [https://github.com/HanchaoLi/nc-mcp](https://github.com/HanchaoLi/nc-mcp)
- **Issue Tracker**: [https://github.com/HanchaoLi/nc-mcp/issues](https://github.com/HanchaoLi/nc-mcp/issues)
- **PyPI**: [https://pypi.org/project/nc-mcp/](https://pypi.org/project/nc-mcp/)


## Author

John Li