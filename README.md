# NetCDF Explorer MCP Server

A simple MCP server for exploring and analyzing netCDF files.
## Features

- 📁 List all the nc files in a directory.
- 🔍 Get the structure information of a netCDF file (dimensions, variables, attributes).
- 📊 Read variable data (support slicing and sampling to avoid memory overflow).
- ⏰ Extract time series data.
- 🔎 Search for variables and attributes.
- 📋 Provide variable summaries as resources.

## Installation

### Install dependency

```bash
pip install fastmcp netCDF4 numpy