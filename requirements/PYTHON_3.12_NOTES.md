# Python 3.12 Compatibility Notes

## Known Issues

### Visual Processing Components

1. **imgaug**: Not compatible with Python 3.12
   - **Solution**: Removed from requirements. Use `albumentations` instead, which provides similar functionality.

2. **sort-track**: Version 1.0.0 doesn't exist
   - **Solution**: Changed to `>=0.0.8` (latest available version)

3. **retinaface**: Hardcoded dependency on old TensorFlow versions (2.1.0/2.5.0) incompatible with Python 3.12
   - **Solution**: Removed from requirements. Use YOLOv8 or MediaPipe for face detection instead.
   - **Config updated**: Default face detection model changed to `yolov8`

### Audio Processing Components

1. **speechbrain**: Newer versions may have issues with Python 3.12
   - **Solution**: Pinned to `<1.0.0` to avoid potential compatibility issues

## Recommendations

If you encounter Python 3.12 compatibility issues:

1. **Option 1**: Use Python 3.11 or 3.10
   ```bash
   python3.11 -m venv hendrix_venv
   source hendrix_venv/bin/activate
   ```

2. **Option 2**: Install only the components you need
   ```bash
   # Skip visual processing if not needed
   pip install -r requirements/base.txt
   pip install -r requirements/audio.txt
   pip install -r requirements/captioning.txt
   ```

3. **Option 3**: Use alternative packages
   - Instead of `imgaug`, use `albumentations`
   - Instead of advanced tracking, use basic OpenCV tracking

## Working Configurations

The following have been tested and work with Python 3.12:
- Base requirements ✓
- Video analysis ✓
- Audio processing (with version constraints) ✓
- Captioning ✓
- Core pipeline functionality ✓

## Optional Components

These components are optional and can be skipped if they cause issues:
- `imgaug` - Image augmentation (use albumentations instead)
- `sort-track` - Advanced tracking (basic tracking still works)
- `deep-sort-realtime` - Multi-object tracking (optional feature)