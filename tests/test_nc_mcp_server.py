# test_netcdf_mcp_server.py
import pytest
import tempfile
import os
import numpy as np
import netCDF4 as nc
from unittest.mock import patch, MagicMock

from nc_mcp_server.main import (
    list_netcdf_files,
    get_netcdf_info,
    get_variable_data,
    search_variables,
    extract_timeseries,
    get_netcdf_variable_resource_impl
)

@pytest.fixture(scope="module")
def create_test_netcdf_file():
    """Create test netCDF file for testing"""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "test_data.nc")
    
    with nc.Dataset(file_path, 'w') as ds:
        # add dimension
        ds.createDimension('time', 10)
        ds.createDimension('lat', 5)
        ds.createDimension('lon', 5)
        
        times = ds.createVariable('time', 'f8', ('time',))
        lats = ds.createVariable('lat', 'f4', ('lat',))
        lons = ds.createVariable('lon', 'f4', ('lon',))
        temp = ds.createVariable('temperature', 'f4', ('time', 'lat', 'lon'))
        precip = ds.createVariable('precipitation', 'f4', ('time', 'lat', 'lon'))
        
        # add property
        ds.description = "Test netCDF file for unit testing"
        ds.history = "Created for MCP server tests"
        
        times.units = "hours since 2023-01-01 00:00:00"
        lats.units = "degrees_north"
        lons.units = "degrees_east"
        temp.units = "celsius"
        temp.long_name = "Surface temperature"
        precip.units = "mm/h"
        precip.long_name = "Precipitation rate"
        
        # add data
        times[:] = np.arange(10) * 6  # 每6小时一次
        lats[:] = np.linspace(40.0, 44.0, 5)
        lons[:] = np.linspace(-80.0, -76.0, 5)
        
        temp_data = np.random.randn(10, 5, 5) * 5 + 20  # 20°C ± 5°C
        precip_data = np.random.rand(10, 5, 5) * 10  # 0-10 mm/h
        
        temp[:] = temp_data
        precip[:] = precip_data
    
    yield file_path
    
    # clean up
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)

@pytest.fixture
def mock_netcdf_dataset():
    """创建一个模拟的 NetCDF 数据集"""
    mock_ds = MagicMock()
    
    mock_ds.dimensions = {
        'time': MagicMock(isunlimited=lambda: True, __len__=lambda: 10),
        'lat': MagicMock(isunlimited=lambda: False, __len__=lambda: 5),
        'lon': MagicMock(isunlimited=lambda: False, __len__=lambda: 5)
    }
    
    mock_time = MagicMock()
    mock_time.dimensions = ('time',)
    mock_time.shape = (10,)
    mock_time.dtype = np.dtype('float64')
    mock_time.ncattrs.return_value = ['units']
    mock_time.units = "hours since 2023-01-01"
    
    mock_temp = MagicMock()
    mock_temp.dimensions = ('time', 'lat', 'lon')
    mock_temp.shape = (10, 5, 5)
    mock_temp.dtype = np.dtype('float32')
    mock_temp.ncattrs.return_value = ['units', 'long_name']
    mock_temp.units = "celsius"
    mock_temp.long_name = "Surface temperature"
    
    mock_ds.variables = {
        'time': mock_time,
        'temperature': mock_temp
    }
    
    mock_ds.ncattrs.return_value = ['description', 'history']
    mock_ds.description = "Test dataset"
    mock_ds.history = "Created for testing"
    
    return mock_ds

def test_list_netcdf_files(tmp_path):
    """Test NetCDF file function"""
    # Create nc file
    test_file = tmp_path / "test.nc"
    test_file.touch()
    
    # Create non-nc file
    other_file = tmp_path / "other.txt"
    other_file.touch()
    
    # Test nc found
    result = list_netcdf_files(str(tmp_path))
    assert "test.nc" in str(result[0])
    
    # Test non-existing dir
    result = list_netcdf_files("/nonexistent/path")
    assert "error" in result[0]
    a = 1

def test_get_netcdf_info(create_test_netcdf_file):
    """Test retrieve NetCDF file function"""
    file_path = create_test_netcdf_file
    
    # Test normal case
    result = get_netcdf_info(file_path)
    
    assert "dimensions" in result
    assert "variables" in result
    assert "global_attributes" in result
    
    # Validate dimension info
    assert result["dimensions"]["time"]["size"] == 10
    assert result["dimensions"]["lat"]["size"] == 5
    assert result["dimensions"]["lon"]["size"] == 5
    
    # Validate variable info
    assert "temperature" in result["variables"]
    assert result["variables"]["temperature"]["dimensions"] == ('time', 'lat', 'lon')
    assert result["variables"]["temperature"]["shape"] == (10, 5, 5)
    
    # Validate properties
    assert "description" in result["global_attributes"]
    
    # Test not exist nc file path
    result = get_netcdf_info("/nonexistent/file.nc")
    assert "does not exist" in result["error"]
    
    # Test non-nc file
    result = get_netcdf_info(__file__)
    assert "not a netCDF file" in result["error"]

def test_get_variable_data(create_test_netcdf_file):
    """Test get variable from nc function"""
    file_path = create_test_netcdf_file
    
    # Test to get all variables
    result = get_variable_data(file_path, "temperature")
    assert result["variable"] == "temperature"
    assert result["shape"] == (10, 5, 5)
    assert "data" in result
    assert "attributes" in result
    
    # Test to get all variables use slice
    slices = {"time": 0, "lat": "0:2:1", "lon": "0:2:1"}
    result = get_variable_data(file_path, "temperature", slices)
    assert result["shape"] == (2, 2)  # After slice
    
    # Test non-exist variables
    result = get_variable_data(file_path, "nonexistent_var")
    assert "does not exist" in result["error"]
    
    # Test sampling feature
    large_file_path = file_path + "_large.nc"
    with nc.Dataset(large_file_path, 'w') as ds:
        ds.createDimension('x', 100)
        ds.createDimension('y', 100)
        large_var = ds.createVariable('large_data', 'f4', ('x', 'y'))
        large_data = np.random.rand(100, 100)
        large_var[:] = large_data
    
    result = get_variable_data(large_file_path, "large_data", max_elements=100)
    assert result["sampled"] is True
    assert result["returned_elements"] <= 100
    
    if os.path.exists(large_file_path):
        os.remove(large_file_path)

def test_search_variables(create_test_netcdf_file):
    """Test search variable function"""
    file_path = create_test_netcdf_file
    
    # Test search variable name
    result = search_variables(file_path, "temperature")
    assert "temperature" in result["variables"]
    
    # Test search properties
    result = search_variables(file_path, "celsius")
    assert "temperature" in result["variables"]
    assert "celsius" in str(result["variables"]["temperature"]["matching_attributes"].get("units", ""))
    
    # Test search global properties
    result = search_variables(file_path, "Test netCDF")
    assert "description" in result["global_attributes"]
    
    # Test not found result
    result = search_variables(file_path, "nonexistent_pattern")
    assert not result["variables"] and not result["global_attributes"]

def test_extract_timeseries(create_test_netcdf_file):
    """Test get time series feature"""
    file_path = create_test_netcdf_file
    
    location = {"lat": 2, "lon": 2}
    result = extract_timeseries(file_path, "temperature", location)
    
    assert result["variable"] == "temperature"
    assert result["time_dimension"] == "time"
    assert len(result["time_values"]) == 10
    assert len(result["values"]) == 10
    assert "spatial_dimensions" in result
    
    # Test canont found location
    result = extract_timeseries(file_path, "temperature")
    assert len(result["values"]) == 10
    
    # Test not exists variable
    result = extract_timeseries(file_path, "nonexistent_var")
    assert "does not exist" in result["error"]
    
    # Test does not have time variable
    no_time_file = file_path + "_notime.nc"
    with nc.Dataset(no_time_file, 'w') as ds:
        ds.createDimension('x', 5)
        ds.createDimension('y', 5)
        var = ds.createVariable('data', 'f4', ('x', 'y'))
        var[:] = np.random.rand(5, 5)
    
    result = extract_timeseries(no_time_file, "data")
    assert "has no time dimension" in result["error"]
    
    if os.path.exists(no_time_file):
        os.remove(no_time_file)

def test_get_netcdf_variable_resource(create_test_netcdf_file):
    """Test get variable resources feature"""
    file_path = create_test_netcdf_file
    
    # Test normal case
    result = get_netcdf_variable_resource_impl(file_path, "temperature")
    assert "variable: temperature" in result
    assert "dimensions:" in result
    assert "shape:" in result
    assert "attributes:" in result
    
    # Test file not exists
    result = get_netcdf_variable_resource_impl("/nonexistent/file.nc", "temperature")
    assert "does not exist" in result
    
    # Test variable not exists
    result = get_netcdf_variable_resource_impl(file_path, "nonexistent_var")
    assert "error" in result

@patch('netCDF4.Dataset')
def test_netcdf_exception_handling(mock_dataset, create_test_netcdf_file):
    """Test exception"""
    file_path = create_test_netcdf_file
    
    mock_dataset.side_effect = Exception("Mocking Exception")
    
    # Test all function should be handle exception
    result = get_netcdf_info(file_path)
    assert "Mocking Exception" in result["error"]
    
    result = get_variable_data(file_path, "temperature")
    assert "Mocking Exception" in result["error"]
    
    result = search_variables(file_path, "test")
    assert "Mocking Exception" in result["error"]
    
    result = extract_timeseries(file_path, "temperature")
    assert "Mocking Exception" in result["error"]
    
    result = get_netcdf_variable_resource_impl(file_path, "temperature")
    assert "Mocking Exception" in result

def test_edge_cases():
    """test edge case"""
    # Empty dir
    with tempfile.TemporaryDirectory() as temp_dir:
        result = list_netcdf_files(temp_dir)
        assert "does not exist" in result[0]
    
    # test not valid slice params
    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Create a simple file
        with nc.Dataset(tmp_path, 'w') as ds:
            ds.createDimension('x', 5)
            ds.createDimension('y', 5)
            var = ds.createVariable('data', 'f4', ('x', 'y'))
            var[:] = np.random.rand(5, 5)
        
        # test not valid slice prams out of range
        slices = {"x": 10}
        result = get_variable_data(tmp_path, "data", slices)
        # should return error
        assert "index exceeds" in result['error']
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])