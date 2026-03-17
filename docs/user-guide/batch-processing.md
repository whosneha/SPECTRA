# Batch Processing

SPECTRA supports efficient batch processing of multiple objects from FITS catalogs or file lists.

## FITS Batch Processing

Process multiple rows from FITS catalogs:

```yaml
input:
  type: 'fits_batch'
  fits_dir: '/path/to/catalogs'
  file_pattern: '*.fits'
  max_rows_per_file: 50
```

### Features

- **Automatic file discovery**: Uses glob patterns to find FITS files
- **Row selection**: Process specific rows or limit number per file
- **Unique object IDs**: Automatically generates IDs like `filename_cluster123`
- **Error handling**: Continues processing if individual rows fail
- **Progress tracking**: Shows progress through files and rows

### Configuration Options

```yaml
input:
  type: 'fits_batch'
  fits_dir: '/path/to/catalogs'
  file_pattern: 'cluster_*.fits'  # Glob pattern
  max_rows_per_file: 100  # Limit rows per file
  row_indices: [0, 1, 2, 5, 10]  # Or specify exact rows
```

### Output Structure

```
output/
├── fit_summary.csv
├── catalog1_cluster0/
│   ├── catalog1_cluster0_sed.png
│   ├── catalog1_cluster0_corner.png
│   └── mcmc_samples.h5
├── catalog1_cluster1/
│   └── ...
└── catalog2_cluster0/
    └── ...
```

## File List Processing

Process multiple individual files:

```yaml
input:
  type: 'file_list'
  format: 'dat'
  photometry_files:
    - '/path/to/object1.dat'
    - '/path/to/object2.dat'
```

Or from a directory:

```yaml
input:
  type: 'file_list'
  format: 'dat'
  photometry_dir: '/path/to/data'
  file_pattern: '*_photometry.dat'
```

## Summary Output

After processing, a summary CSV is generated:

```csv
object_id,redshift,log_likelihood,mass,age,metallicity,dust
catalog1_cluster0,4.59,-45.23,11.2,0.5,-0.3,0.8
catalog1_cluster1,4.59,-52.11,10.8,1.2,-0.5,1.2
```

## Performance Tips

1. **Use max_rows_per_file**: Limit processing for testing
2. **Parallel processing**: Future versions will support multiprocessing
3. **Save intermediate results**: Enable HDF5 backend for MCMC
4. **Monitor memory**: Large catalogs may require chunking

## Error Handling

Objects that fail to process are logged but don't stop the batch:

```
[WARNING] Failed to load row 42: Invalid flux values
ERROR processing catalog1_cluster99: Optimization failed
```

The summary shows successful vs failed fits:

```
BATCH PROCESSING COMPLETE
  Successful: 95
  Failed: 5
  Output directory: ./output
```
