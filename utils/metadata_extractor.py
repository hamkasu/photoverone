"""
EXIF Metadata Extraction Utilities for PhotoVault
Extracts comprehensive metadata from photographs for digitization projects
"""

from PIL import Image, ExifTags
import exifread
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
import json
import os
import re

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extract and process EXIF metadata from photographs"""
    
    def __init__(self):
        # GPS reference mappings
        self.gps_ref_map = {
            'N': 1, 'S': -1, 'E': 1, 'W': -1
        }
        
        # Common date formats found in EXIF
        self.date_formats = [
            "%Y:%m:%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y:%m:%d",
            "%Y-%m-%d"
        ]
    
    def extract_all_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing all extracted metadata
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {}
        
        try:
            # Try PIL first for modern EXIF support
            pil_metadata = self._extract_pil_metadata(image_path)
            
            # Try exifread for additional data and fallback
            exifread_metadata = self._extract_exifread_metadata(image_path)
            
            # Merge and normalize data
            combined_metadata = self._merge_metadata(pil_metadata, exifread_metadata)
            
            # Add file-based metadata
            file_metadata = self._extract_file_metadata(image_path)
            combined_metadata.update(file_metadata)
            
            logger.info(f"Extracted metadata from: {image_path}")
            return combined_metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {image_path}: {e}")
            return self._extract_file_metadata(image_path)  # At least return file info
    
    def _extract_pil_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata using Pillow/PIL"""
        metadata = {}
        
        try:
            with Image.open(image_path) as img:
                # Basic image info
                metadata['format'] = img.format
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['mode'] = img.mode
                
                # Extract EXIF data
                exif_data = img.getexif()
                if exif_data:
                    # Process standard EXIF tags
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, f"Tag_{tag_id}")
                        metadata[f"exif_{tag_name.lower()}"] = value
                    
                    # Extract GPS data if available (GPSInfo tag is 34853)
                    gps_info = exif_data.get(34853)  # GPSInfo tag
                    if gps_info:
                        metadata['gps_info_raw'] = str(gps_info)
                        
        except Exception as e:
            logger.warning(f"PIL metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_exifread_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata using exifread library"""
        metadata = {}
        
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                
                for tag_name, tag_value in tags.items():
                    if tag_name not in ('JPEGThumbnail', 'TIFFThumbnail'):
                        # Convert exifread values to strings
                        metadata[f"exif_{tag_name.lower().replace(' ', '_')}"] = str(tag_value)
                        
        except Exception as e:
            logger.warning(f"ExifRead metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_file_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract file system metadata"""
        metadata = {}
        
        try:
            stat = os.stat(image_path)
            metadata['file_size'] = stat.st_size
            metadata['file_modified'] = datetime.fromtimestamp(stat.st_mtime)
            metadata['file_created'] = datetime.fromtimestamp(stat.st_ctime)
            
        except Exception as e:
            logger.warning(f"File metadata extraction failed: {e}")
        
        return metadata
    
    def _merge_metadata(self, pil_data: Dict, exifread_data: Dict) -> Dict[str, Any]:
        """Merge and normalize metadata from different sources"""
        # Start with PIL data as it's more reliable for modern formats
        metadata = pil_data.copy()
        
        # Add exifread data where PIL data is missing
        for key, value in exifread_data.items():
            if key not in metadata:
                metadata[key] = value
        
        return metadata
    
    def extract_photo_metadata_for_db(self, image_path: str) -> Dict[str, Any]:
        """
        Extract metadata specifically formatted for database storage
        
        Returns:
            Dictionary with keys matching Photo model fields
        """
        raw_metadata = self.extract_all_metadata(image_path)
        
        # Initialize database fields
        db_metadata = {
            'date_taken': None,
            'camera_make': None,
            'camera_model': None,
            'iso': None,
            'aperture': None,
            'shutter_speed': None,
            'focal_length': None,
            'flash_used': None,
            'gps_latitude': None,
            'gps_longitude': None,
            'gps_altitude': None,
            'orientation': None,
            'color_space': None,
            'width': raw_metadata.get('width'),
            'height': raw_metadata.get('height'),
            'file_size': raw_metadata.get('file_size')
        }
        
        # Extract and convert specific fields
        db_metadata['date_taken'] = self._extract_date_taken(raw_metadata)
        db_metadata['camera_make'] = self._extract_camera_make(raw_metadata)
        db_metadata['camera_model'] = self._extract_camera_model(raw_metadata)
        db_metadata['iso'] = self._extract_iso(raw_metadata)
        db_metadata['aperture'] = self._extract_aperture(raw_metadata)
        db_metadata['shutter_speed'] = self._extract_shutter_speed(raw_metadata)
        db_metadata['focal_length'] = self._extract_focal_length(raw_metadata)
        db_metadata['flash_used'] = self._extract_flash_info(raw_metadata)
        
        # GPS coordinates
        lat, lon, alt = self._extract_gps_coordinates(raw_metadata)
        db_metadata['gps_latitude'] = lat
        db_metadata['gps_longitude'] = lon
        db_metadata['gps_altitude'] = alt
        
        # Image properties
        db_metadata['orientation'] = self._extract_orientation(raw_metadata)
        db_metadata['color_space'] = self._extract_color_space(raw_metadata)
        
        return db_metadata
    
    def _extract_date_taken(self, metadata: Dict) -> Optional[datetime]:
        """Extract date taken from various EXIF fields"""
        date_fields = [
            'exif_datetime',
            'exif_datetimeoriginal',
            'exif_datetimedigitized',
            'exif_image_datetime'
        ]
        
        for field in date_fields:
            date_str = metadata.get(field)
            if date_str:
                for fmt in self.date_formats:
                    try:
                        return datetime.strptime(str(date_str), fmt)
                    except ValueError:
                        continue
        
        return None
    
    def _extract_camera_make(self, metadata: Dict) -> Optional[str]:
        """Extract camera manufacturer"""
        make_fields = ['exif_make', 'exif_image_make']
        
        for field in make_fields:
            make = metadata.get(field)
            if make:
                return str(make).strip()
        
        return None
    
    def _extract_camera_model(self, metadata: Dict) -> Optional[str]:
        """Extract camera model"""
        model_fields = ['exif_model', 'exif_image_model']
        
        for field in model_fields:
            model = metadata.get(field)
            if model:
                return str(model).strip()
        
        return None
    
    def _extract_iso(self, metadata: Dict) -> Optional[int]:
        """Extract ISO sensitivity"""
        iso_fields = ['exif_isospeedratings', 'exif_photographicsensitivity']
        
        for field in iso_fields:
            iso = metadata.get(field)
            if iso:
                try:
                    return int(str(iso))
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_aperture(self, metadata: Dict) -> Optional[float]:
        """Extract aperture f-stop value"""
        aperture_fields = ['exif_fnumber', 'exif_aperture', 'exif_aperturevalue']
        
        for field in aperture_fields:
            aperture = metadata.get(field)
            if aperture:
                try:
                    # Handle fractional values like "f/2.8" or "28/10"
                    aperture_str = str(aperture)
                    if '/' in aperture_str:
                        # Handle ratios
                        if aperture_str.startswith('f/'):
                            return float(aperture_str[2:])
                        else:
                            # Handle fractional EXIF format
                            parts = aperture_str.split('/')
                            if len(parts) == 2:
                                return float(parts[0]) / float(parts[1])
                    else:
                        return float(aperture_str)
                except (ValueError, TypeError, ZeroDivisionError):
                    continue
        
        return None
    
    def _extract_shutter_speed(self, metadata: Dict) -> Optional[str]:
        """Extract shutter speed/exposure time"""
        shutter_fields = ['exif_exposuretime', 'exif_shutterspeedvalue']
        
        for field in shutter_fields:
            shutter = metadata.get(field)
            if shutter:
                return str(shutter).strip()
        
        return None
    
    def _extract_focal_length(self, metadata: Dict) -> Optional[float]:
        """Extract focal length in mm"""
        focal_fields = ['exif_focallength']
        
        for field in focal_fields:
            focal = metadata.get(field)
            if focal:
                try:
                    focal_str = str(focal)
                    if '/' in focal_str:
                        # Handle fractional format
                        parts = focal_str.split('/')
                        if len(parts) == 2:
                            return float(parts[0]) / float(parts[1])
                    else:
                        return float(focal_str)
                except (ValueError, TypeError, ZeroDivisionError):
                    continue
        
        return None
    
    def _extract_flash_info(self, metadata: Dict) -> Optional[bool]:
        """Extract whether flash was used"""
        flash_fields = ['exif_flash']
        
        for field in flash_fields:
            flash = metadata.get(field)
            if flash is not None:
                try:
                    # Flash EXIF values: 0 = no flash, >0 = flash used
                    flash_value = int(str(flash))
                    return flash_value > 0
                except (ValueError, TypeError):
                    # Try string matching
                    flash_str = str(flash).lower()
                    return 'fired' in flash_str or 'yes' in flash_str
        
        return None
    
    def _extract_gps_coordinates(self, metadata: Dict) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Extract GPS coordinates (latitude, longitude, altitude)"""
        try:
            # Try to get already processed GPS data
            lat = metadata.get('gps_latitude')
            lon = metadata.get('gps_longitude')
            
            if lat is not None and lon is not None:
                alt = metadata.get('gps_altitude')
                return lat, lon, alt
            
            # Extract from raw EXIF GPS tags
            gps_lat = metadata.get('exif_gps_gpslatitude')
            gps_lat_ref = metadata.get('exif_gps_gpslatituderef')
            gps_lon = metadata.get('exif_gps_gpslongitude')
            gps_lon_ref = metadata.get('exif_gps_gpslongituderef')
            gps_alt = metadata.get('exif_gps_gpsaltitude')
            
            if all([gps_lat, gps_lat_ref, gps_lon, gps_lon_ref]):
                lat = self._convert_gps_to_decimal(gps_lat, gps_lat_ref)
                lon = self._convert_gps_to_decimal(gps_lon, gps_lon_ref)
                
                # Convert altitude if available
                alt = None
                if gps_alt:
                    try:
                        alt_str = str(gps_alt)
                        if '/' in alt_str:
                            parts = alt_str.split('/')
                            alt = float(parts[0]) / float(parts[1])
                        else:
                            alt = float(alt_str)
                    except:
                        alt = None
                
                return lat, lon, alt
                
        except Exception as e:
            logger.warning(f"GPS extraction failed: {e}")
        
        return None, None, None
    
    def _convert_gps_to_decimal(self, gps_coords, ref) -> float:
        """Convert GPS coordinates from DMS to decimal degrees"""
        # Handle string format like "41, 52, 54.23"
        coords_str = str(gps_coords).replace('[', '').replace(']', '')
        parts = [float(x.strip()) for x in coords_str.split(',')]
        
        if len(parts) >= 3:
            degrees, minutes, seconds = parts[:3]
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        elif len(parts) == 2:
            degrees, minutes = parts
            decimal = degrees + (minutes / 60.0)
        else:
            decimal = float(parts[0])
        
        # Apply reference direction
        if str(ref).upper() in ['S', 'W']:
            decimal = -decimal
            
        return decimal
    
    def _extract_orientation(self, metadata: Dict) -> Optional[int]:
        """Extract image orientation"""
        orientation = metadata.get('exif_orientation')
        if orientation:
            try:
                return int(str(orientation))
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_color_space(self, metadata: Dict) -> Optional[str]:
        """Extract color space information"""
        color_fields = ['exif_colorspace', 'exif_whitepoint']
        
        for field in color_fields:
            color_space = metadata.get(field)
            if color_space:
                color_str = str(color_space).strip()
                if color_str and color_str.lower() != 'none':
                    return color_str
        
        return None

# Create global extractor instance
extractor = MetadataExtractor()

def extract_metadata_for_photo(image_path: str) -> Dict[str, Any]:
    """Convenience function for extracting photo metadata"""
    return extractor.extract_photo_metadata_for_db(image_path)

def extract_all_metadata(image_path: str) -> Dict[str, Any]:
    """Convenience function for extracting all available metadata"""
    return extractor.extract_all_metadata(image_path)