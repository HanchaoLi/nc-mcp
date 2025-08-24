from fastmcp import FastMCP
import netCDF4 as nc
import numpy as np
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

mcp = FastMCP("NetCDF Explorer")

def list_netcdf_files(directory: str = ".") -> List[str]:
    """List all netCDF files in the specified directory.
    
    Args:
        directory: The directory to search in, defaults to current directory
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return [f"error: directory {directory} does not exist"]
        
        netcdf_extensions = ['.nc', '.cdf', '.netcdf', '.nc4']
        netcdf_files = []
        for ext in netcdf_extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                netcdf_files.append(str(file_path))
        if not netcdf_files:
            return ["netCDF files does not exist"]
        
        return netcdf_files if netcdf_files else ["no netCDF files found"]
        
    except Exception as e:
        return [f"error when search netcdf files: {str(e)}"]

def get_netcdf_info(file_path: str) -> Dict[str, Any]:
    """Get basic information and structure of a netCDF file.
    
    Args:
        file_path: The path to the netCDF file
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"file {file_path} does not exist"}
        
        if not path.suffix.lower() in ['.nc', '.cdf', '.netcdf', '.nc4']:
            return {"error": f"file {file_path} is not a netCDF file"} 
        
        with nc.Dataset(file_path, 'r') as dataset:
            # Get file meta info
            info = {
                "file_name": path.name,
                "file_size_MB": path.stat().st_size / (1024 * 1024),
                "format": dataset.data_model,
                "dimensions": {},
                "variables": {},
                "global_attributes": {},
                "groups": list(dataset.groups.keys()) if hasattr(dataset, 'groups') else []
            }
            
            # Get dimension info
            for dim_name, dim in dataset.dimensions.items():
                info["dimensions"][dim_name] = {
                    "size": len(dim),
                    "is_unlimited": dim.isunlimited()
                }
            
            # Get variable info
            for var_name, var in dataset.variables.items():
                info["variables"][var_name] = {
                    "dimensions": var.dimensions,
                    "shape": var.shape,
                    "dtype": str(var.dtype),
                    "attributes": {attr: getattr(var, attr) for attr in var.ncattrs()}
                }
            
            # Get global attributes 
            for attr in dataset.ncattrs():
                info["global_attributes"][attr] = getattr(dataset, attr)
            
            return info
            
    except Exception as e:
        return {"error": f"error when read netCDF file: {str(e)}"}

def get_variable_data(file_path: str, variable_name: str, 
                     slices: Optional[Dict[str, Union[int, str]]] = None,
                     max_elements: int = 1000) -> Dict[str, Any]:
    """Get data from a specific variable in a netCDF file (supports slicing).
    
    Args:
        file_path: The path to the netCDF file
        variable_name: The name of the variable to get data from
        slices: Optional slicing dictionary, e.g. {"time": 0, "lat": "0:10"} or {"time": "5", "lat": "0:10:2"}
        max_elements: Maximum number of elements to return, to prevent large data
    """
    try:
        # parse string
        parsed_slices = {}
        if slices:
            for dim, slice_val in slices.items():
                if isinstance(slice_val, int):
                    parsed_slices[dim] = slice_val
                elif isinstance(slice_val, str):
                    # parse "start:stop:step" format string
                    parts = slice_val.split(":")
                    if len(parts) == 1:
                        # single number, like "5"
                        parsed_slices[dim] = int(parts[0])
                    elif len(parts) == 2:
                        # range like: "0:10"
                        start = int(parts[0]) if parts[0] else None
                        stop = int(parts[1]) if parts[1] else None
                        parsed_slices[dim] = slice(start, stop)
                    elif len(parts) == 3:
                        # range with step, like: "0:10:2"
                        start = int(parts[0]) if parts[0] else None
                        stop = int(parts[1]) if parts[1] else None
                        step = int(parts[2]) if parts[2] else None
                        parsed_slices[dim] = slice(start, stop, step)
        
        with nc.Dataset(file_path, 'r') as dataset:
            if variable_name not in dataset.variables:
                return {"error": f"variable '{variable_name}' does not exist"}
            
            var = dataset.variables[variable_name]
            
            # prepare slice params
            if parsed_slices:
                # convert dict to tuple
                slice_params = []
                for dim in var.dimensions:
                    if dim in parsed_slices:
                        slice_params.append(parsed_slices[dim])
                    else:
                        slice_params.append(slice(None))
            else:
                # if not slice, then full slice
                slice_params = [slice(None)] * len(var.dimensions)
            
            # apply slice data
            data = var[tuple(slice_params)]
            
            # check data size，if too large, then sampling
            total_elements = data.size
            if total_elements > max_elements:
                # calculate sample rate
                sample_rate = max(1, total_elements // max_elements)
                
                # sample for multi dimension array
                if data.ndim > 0:
                    sample_slices = []
                    for i in range(data.ndim):
                        size = data.shape[i]
                        if size > 1:
                            sample_indices = np.arange(0, size, sample_rate)
                            sample_slices.append(sample_indices)
                        else:
                            sample_slices.append(slice(None))
                    
                    # apply sampling
                    data = data[tuple(sample_slices)]
                
                sampled = True
            else:
                sampled = False
            
            if hasattr(data, 'tolist'):
                data = data.tolist()
            
            # get property variable
            attributes = {attr: getattr(var, attr) for attr in var.ncattrs()}
            
            return {
                "variable": variable_name,
                "data": data,
                "dimensions": var.dimensions,
                "shape": np.array(data).shape,
                "attributes": attributes,
                "sampled": sampled,
                "total_elements": total_elements,
                "returned_elements": np.array(data).size if hasattr(data, '__len__') else 1
            }
            
    except Exception as e:
        return {"error": f"reading variables: {str(e)}"}

def search_variables(file_path: str, search_term: str) -> Dict[str, Any]:
    """Search for variables or attributes containing a specific keyword in a netCDF file
    
    Args:
        file_path: The path to the netCDF file
        search_term: The keyword to search for
    """
    try:
        with nc.Dataset(file_path, 'r') as dataset:
            results = {
                "variables": {},
                "global_attributes": {}
            }
            
            search_lower = search_term.lower()
            
            # Search global attributes
            for attr_name in dataset.ncattrs():
                attr_value = str(getattr(dataset, attr_name)).lower()
                if search_lower in attr_value:
                    results["global_attributes"][attr_name] = getattr(dataset, attr_name)
            
            # Search variables
            for var_name, var in dataset.variables.items():
                # Check variable name
                if search_lower in var_name.lower():
                    results["variables"][var_name] = {
                        "dimensions": var.dimensions,
                        "shape": var.shape
                    }
                    continue
                
                # Check variable attributes
                var_matched = False
                var_info = {
                    "dimensions": var.dimensions,
                    "shape": var.shape,
                    "matching_attributes": {}
                }
                
                for attr_name in var.ncattrs():
                    attr_value = str(getattr(var, attr_name)).lower()
                    if search_lower in attr_value:
                        var_info["matching_attributes"][attr_name] = getattr(var, attr_name)
                        var_matched = True
                
                if var_matched:
                    results["variables"][var_name] = var_info
            
            return results
            
    except Exception as e:
        return {"error": f"error when search variables: {str(e)}"}

def extract_timeseries(file_path: str, variable_name: str, 
                      location: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """Extract timeseries data from a netCDF file
    
    Args:
        file_path: The path to the netCDF file
        variable_name: The name of the variable to extract timeseries from
        location: Optional dictionary of location coordinates, e.g. {"lat": 10, "lon": 20}
                  If not provided, will use data from the first spatial point
    """
    try:
        with nc.Dataset(file_path, 'r') as dataset:
            if variable_name not in dataset.variables:
                return {"error": f"variable '{variable_name}' does not exist"}
            
            var = dataset.variables[variable_name]
            
            # Find time dimension
            time_dim = None
            for dim in var.dimensions:
                if dim.lower() in ['time', 't']:
                    time_dim = dim
                    break
            
            if not time_dim:
                return {"error": f"variable '{variable_name}' has no time dimension"}
            
            # Prepare slices
            slice_params = []
            spatial_dims = []
            
            for dim in var.dimensions:
                if dim == time_dim:
                    # Time dimension - get all time points
                    slice_params.append(slice(None))
                else:
                    # Spatial dimension - use specified location or first point
                    if location and dim in location:
                        slice_params.append(location[dim])
                    else:
                        slice_params.append(0)
                    spatial_dims.append(dim)
            
            # Get timeseries data
            data = var[tuple(slice_params)]
            
            # Get time variable
            time_var = None
            if time_dim in dataset.variables:
                time_var = dataset.variables[time_dim]
                time_data = time_var[:]
                if hasattr(time_data, 'tolist'):
                    time_data = time_data.tolist()
            else:
                time_data = list(range(len(data)))
            
            # Convert to Python native types
            if hasattr(data, 'tolist'):
                data = data.tolist()
            
            return {
                "variable": variable_name,
                "time_dimension": time_dim,
                "spatial_dimensions": spatial_dims,
                "time_values": time_data,
                "values": data,
                "units": getattr(var, 'units', 'unknown') if hasattr(var, 'units') else 'unknown'
            }
            
    except Exception as e:
        return {"error": f"error when extract timeseries: {str(e)}"}

@mcp.resource("netcdf://{file_path}/{variable_name}")
def get_netcdf_variable_resource(file_path: str, variable_name: str) -> str:
    return get_netcdf_variable_resource_impl(file_path, variable_name)

def get_netcdf_variable_resource_impl(file_path: str, variable_name: str) -> str:
    """Provide summary information of a netCDF variable as a resource"""
    try:
        info = get_netcdf_info(file_path)
        if "error" in info:
            return f"error: {info['error']}"
        
        if variable_name not in info["variables"]:
            return f"error: variable '{variable_name}' not exist"
        
        var_info = info["variables"][variable_name]
        result = f"variable: {variable_name}\n"
        result += f"dimensions: {var_info['dimensions']}\n"
        result += f"shape: {var_info['shape']}\n"
        result += "attributes:\n"
        
        for attr_name, attr_value in var_info["attributes"].items():
            result += f"  {attr_name}: {attr_value}\n"
        
        return result
        
    except Exception as e:
        return f"error: get variable info failed: {str(e)}"

mcp.tool(list_netcdf_files, name="list_netcdf_files")
mcp.tool(get_netcdf_info, name="list_netcdf_files")
mcp.tool(get_variable_data, name="list_netcdf_files")
mcp.tool(search_variables, name="list_netcdf_files")
mcp.tool(extract_timeseries, name="list_netcdf_files")
if __name__ == "__main__":
    # Run server
    mcp.run(transport='stdio')