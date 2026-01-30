import numpy as np
import pandas as pd

class PhotometryLoader:
    """Load photometry data from various formats."""
    
    @staticmethod
    def load_photometry(filepath, format='dat'):
        """
        Load photometry data.
        
        Args:
            filepath: Path to photometry file
            format: File format (dat, csv, hdf5, parquet)
            
        Returns:
            dict with keys: wavelength, obs_flux, obs_err, mod_flux
        """
        if format == 'dat':
            return PhotometryLoader._load_dat(filepath)
        elif format == 'csv':
            return PhotometryLoader._load_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _load_dat(filepath):
        """Load from ASCII .dat file."""
        data = pd.read_csv(filepath, sep=r'\s+', comment='#', 
                          names=['wavelength', 'obs_flux', 'obs_err', 'mod_flux'])
        
        print(f"[IO DEBUG] Loaded data shape: {data.shape}")
        print(f"[IO DEBUG] Column names: {data.columns.tolist()}")
        print(f"[IO DEBUG] Data head:\n{data.head()}")
        print(f"[IO DEBUG] mod_flux values: {data['mod_flux'].values}")
        print(f"[IO DEBUG] mod_flux range: {data['mod_flux'].min():.2e} to {data['mod_flux'].max():.2e}")
        
        return {
            'wavelength': data['wavelength'].values,
            'obs_flux': data['obs_flux'].values,
            'obs_err': data['obs_err'].values,
            'mod_flux': data['mod_flux'].values,
        }
    
    @staticmethod
    def _load_csv(filepath):
        """Load from CSV file."""
        data = pd.read_csv(filepath)
        return {
            'wavelength': data['wavelength'].values,
            'obs_flux': data['obs_flux'].values,
            'obs_err': data['obs_err'].values,
            'mod_flux': data.get('mod_flux', np.zeros_like(data['obs_flux'])).values,
        }
    
    @staticmethod
    def save_results(filepath, results, format='hdf5'):
        """Save fitting results to file."""
        if format == 'hdf5':
            import h5py
            with h5py.File(filepath, 'w') as f:
                for key, val in results.items():
                    f.create_dataset(key, data=val)
        elif format == 'csv':
            pd.DataFrame(results).to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported save format: {format}")
