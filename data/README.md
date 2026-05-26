# Data Directory

## Required Dataset

Place the UCL Stroke EIT Dataset file here:

```
data/UCL_Stroke_EIT_Dataset.mat
```

## Dataset Information

- **Source**: UCL Stroke EIT Dataset (MATLAB v7.3 HDF5 format)
- **Subjects**: 27 total (10 healthy, 10 ischaemia, 7 haemorrhage)
- **Measurements**: 930 voltage measurements per subject
- **Frequencies**: 17 frequency points (100 Hz - 2000 Hz)

## Cache Files

The pipeline automatically creates cache files:
- `eit_cache.npz`: Processed voltage data and metadata

## Notes

- The original dataset file is not included in this repository
- Contact the UCL research group for dataset access
- Ensure you have appropriate permissions to use the dataset