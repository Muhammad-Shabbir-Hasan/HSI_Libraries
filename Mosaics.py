import sys
import importlib
import pandas as pd
from pyproj import Transformer
import numpy as np
import h5py
from shapely.geometry import Point, Polygon
import os

# Add directory containing the module
sys.path.append("..")   # go one level up to project/
sys.path.append(r"D:\00-Workspace\OneDrive - University of Regina\00-Workstation(UoR)\00-Research_Work\00-HSI_Libraries\HSI")


import Localization.Localization as localization
importlib.reload(localization)

import HSI as hsi
importlib.reload(hsi)

class Mosaics_Tools:

    def read_plot_location_txt(self, plot_file):

        # ---------------------------------------------
        # Load plot file
        # ---------------------------------------------

        plots = pd.read_csv(plot_file, sep="\t")

        # ---------------------------------------------
        # Convert numeric fields safely
        # ---------------------------------------------

        for col in plots.columns:
            if col.lower() not in ["plot_id", "plot"]:
                plots[col] = pd.to_numeric(plots[col], errors="coerce")

        return plots


    def convert_plot_utm_to_gps(self, plots_df):

        from pyproj import Transformer

        transformer = Transformer.from_crs(
            "EPSG:32613",   # UTM
            "EPSG:4326",    # GPS
            always_xy=True
        )

        gps_plots = []

        for _, row in plots_df.iterrows():

            plot_id = row["Plot_Number"]

            utm_points = [
                (row["Point1_long"], row["Point1_lat"]),
                (row["Point2_long"], row["Point2_lat"]),
                (row["Point3_long"], row["Point3_lat"]),
                (row["Point4_long"], row["Point4_lat"])
            ]

            gps_points = []

            for x, y in utm_points:

                lon, lat = transformer.transform(x, y)

                gps_points.append((lon, lat))

            gps_plots.append({
                "plot_id": plot_id,
                "gps_corners": gps_points
            })

        return gps_plots





    def create_orthomosaic_mask_utm(self, txt_file, output_folder, resolution=0.1):

        import pandas as pd
        import numpy as np
        from pyproj import Transformer
        import tifffile
        import os

        print("Reading TXT file...")

        df = pd.read_csv(txt_file)

        lon = df["longitude"].values
        lat = df["latitude"].values
        cls = df["class"].values

        transformer = Transformer.from_crs(
            "EPSG:4326",
            "EPSG:32613",
            always_xy=True
        )

        x, y = transformer.transform(lon, lat)

        x = np.array(x)
        y = np.array(y)

        # Bounding box
        min_x = x.min()
        max_x = x.max()
        min_y = y.min()
        max_y = y.max()

        # Real area size
        width_m  = max_x - min_x
        height_m = max_y - min_y

        print("Orthomosaic width (meters):", round(width_m,2))
        print("Orthomosaic height (meters):", round(height_m,2))

        width_px  = int(width_m / resolution) + 1
        height_px = int(height_m / resolution) + 1

        print("Raster size (pixels):", width_px, "x", height_px)

        # Safety check
        total_pixels = width_px * height_px
        print("Total pixels:", total_pixels)

        if total_pixels > 2e8:
            print("WARNING: raster extremely large, increase resolution")

        raster = np.zeros((height_px, width_px, 3), dtype=np.uint8)

        px = ((x - min_x) / resolution).astype(int)
        py = ((max_y - y) / resolution).astype(int)

        valid = (px >= 0) & (px < width_px) & (py >= 0) & (py < height_px)

        px = px[valid]
        py = py[valid]
        cls = cls[valid]

        mask = cls > 0
        raster[py[mask], px[mask], 0] = 255

        tif_path = os.path.join(output_folder, "orthomosaic_mask.tif")

        tifffile.imwrite(tif_path, raster, photometric="rgb")

        print("Saved:", tif_path)


    '''
    def export_scanlines_geojson(self, txt_file, output_folder):

        import pandas as pd
        import json
        import os

        print("Reading TXT file...")

        df = pd.read_csv(txt_file)

        # output file
        output_file = os.path.join(output_folder, "scanlines.geojson")

        features = []

        # group by scanline (pixel_y)
        grouped = df.groupby("pixel_y")

        for line_id, group in grouped:

            # sort pixels in correct order
            group = group.sort_values("pixel_x")

            coords = []

            for _, row in group.iterrows():

                coords.append([
                    float(row["longitude"]),
                    float(row["latitude"])
                ])

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "scanline": int(line_id)
                }
            }

            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        with open(output_file, "w") as f:
            json.dump(geojson, f)

        print("Scanlines GeoJSON saved:", output_file)
    '''

    def export_scanlines_and_points_geojson(self, txt_file, output_folder):

        import pandas as pd
        import json
        import os

        print("Reading TXT file...")

        df = pd.read_csv(txt_file)

        scanline_file = os.path.join(output_folder, "scanlines.geojson")
        point_file = os.path.join(output_folder, "pixel_points.geojson")

        scanline_features = []
        point_features = []

        # -----------------------------------------
        # Create point features
        # -----------------------------------------

        for _, row in df.iterrows():

            point_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(row["longitude"]),
                        float(row["latitude"])
                    ]
                },
                "properties": {
                    "pixel_x": int(row["pixel_x"]),
                    "pixel_y": int(row["pixel_y"]),
                    "class": float(row["class"])
                }
            }

            point_features.append(point_feature)

        # -----------------------------------------
        # Create scanline features
        # -----------------------------------------

        grouped = df.groupby("pixel_y")

        for line_id, group in grouped:

            group = group.sort_values("pixel_x")

            coords = []

            for _, row in group.iterrows():

                coords.append([
                    float(row["longitude"]),
                    float(row["latitude"])
                ])

            line_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "scanline": int(line_id)
                }
            }

            scanline_features.append(line_feature)

        # -----------------------------------------
        # Save scanlines
        # -----------------------------------------

        scanline_geojson = {
            "type": "FeatureCollection",
            "features": scanline_features
        }

        with open(scanline_file, "w") as f:
            json.dump(scanline_geojson, f)

        print("Scanlines saved:", scanline_file)

        # -----------------------------------------
        # Save points
        # -----------------------------------------

        point_geojson = {
            "type": "FeatureCollection",
            "features": point_features
        }

        with open(point_file, "w") as f:
            json.dump(point_geojson, f)

        print("Points saved:", point_file)







class Mosaics:

    def __init__(self):
        self.localization_tools = localization.Localization_Tools()
        self.mosaics_tools = Mosaics_Tools()
        self.hsi_mat = hsi.Mat()
        

    def create_mosaic(self, cube_data, geolocation_data, bands):
        """
        Create mosaics for selected bands.
        (Empty for now)
        """
        pass



    # ---------------------------------------------------
    # Navigation parameters
    # ---------------------------------------------------

    def get_navigation_parameters(self, nav_row):

        # -----------------------------------------
        # extract values
        # -----------------------------------------

        lat = nav_row.get("latitude_deg", 0)
        lon = nav_row.get("longitude_deg", 0)

        alt_ft = nav_row.get("altitude_m", 0)



        roll  = np.radians(nav_row.get("DJI_Roll", 0))
        pitch = np.radians(nav_row.get("DJI_Pitch", 0))
        yaw   = np.radians(nav_row.get("DJI_Direction", 0))

        # -----------------------------------------
        # unit conversions
        # -----------------------------------------

        # feet → meters
        alt_m = alt_ft * 0.3048
        #alt_m = 100 


        # -----------------------------------------
        # return standardized values
        # -----------------------------------------

        return lat, lon, alt_m, roll, pitch, yaw
    

    # ---------------------------------------------------
    # Compute flight direction from N points
    # ---------------------------------------------------

    def compute_flight_direction(self, nav_df, line_index, n_avg=4):

        start = max(0, line_index - n_avg)
        end   = min(len(nav_df)-1, line_index + n_avg)

        lat1 = nav_df.iloc[start]["latitude_deg"]
        lon1 = nav_df.iloc[start]["longitude_deg"]

        lat2 = nav_df.iloc[end]["latitude_deg"]
        lon2 = nav_df.iloc[end]["longitude_deg"]

        dy = lat2 - lat1
        dx = lon2 - lon1

        yaw = np.degrees(np.arctan2(dy, dx))

        return yaw


    # ---------------------------------------------------
    # Compute ground offset of pixel
    # ---------------------------------------------------

    def compute_pixel_offset(self, pixel_index, center_pixel, IFOV_deg, altitude):

        # pixel viewing angle in degrees
        pixel_angle_deg = (pixel_index - center_pixel) * IFOV_deg

        # convert to radians
        pixel_angle_rad = np.radians(pixel_angle_deg)

        # compute ground offset
        ground_offset = altitude * np.tan(pixel_angle_rad)

        return ground_offset

    # ---------------------------------------------------
    # Convert meters to GPS shift
    # ---------------------------------------------------

    def meters_to_gps(self, dx, dy, lat):

        earth_radius = 6378137.0

        lat_rad = np.radians(lat)

        dlat = dy / earth_radius
        dlon = dx / (earth_radius * np.cos(lat_rad))

        return np.degrees(dlon), np.degrees(dlat)


    # ---------------------------------------------------
    # Apply sensor offset
    # ---------------------------------------------------

    def apply_sensor_offset(self, lon, lat, yaw, offset_cm):

        offset_m = offset_cm / 100.0

        dx = offset_m * np.cos(yaw)
        dy = offset_m * np.sin(yaw)

        dlon, dlat = self.meters_to_gps(dx, dy, lat)

        return lon + dlon, lat + dlat


    # ---------------------------------------------------
    # Classify pixel inside plot
    # ---------------------------------------------------

    def classify_pixel(self, point, plot_polygons):

        for plot_id, poly in plot_polygons:

            if poly.contains(point):
                return plot_id

        return 0


    # ---------------------------------------------------
    # Save outputs
    # ---------------------------------------------------

    def save_txt(self, df, file_path):

        df.to_csv(file_path, index=False)

        print("TXT saved:", file_path)

 
    # Need to correct it
    def save_mat(self, df, file_path, n_lines, n_pixels):

        import numpy as np
        import h5py

        print("Preparing 3D geo cube...")

        # initialize cube
        geo_cube = np.full((n_lines, n_pixels, 3), np.nan, dtype=np.float32)

        # extract dataframe columns
        x = df["pixel_x"].to_numpy(dtype=np.int64)
        y = df["pixel_y"].to_numpy(dtype=np.int64)

        lon = df["longitude"].to_numpy(dtype=np.float32)
        lat = df["latitude"].to_numpy(dtype=np.float32)
        cls = df["class"].to_numpy(dtype=np.float32)

        # -----------------------------
        # check indices
        # -----------------------------
        if np.any(x >= n_pixels) or np.any(x < 0):
            raise ValueError("pixel_x indices outside range")

        if np.any(y >= n_lines) or np.any(y < 0):
            raise ValueError("pixel_y indices outside range")

        print("Unique lines:", np.unique(y).shape[0])
        print("Unique pixels:", np.unique(x).shape[0])

        # -----------------------------
        # fill cube
        # -----------------------------
        geo_cube[y, x, 0] = lon
        geo_cube[y, x, 1] = lat
        geo_cube[y, x, 2] = cls

        # -----------------------------
        # save MAT v7.3
        # -----------------------------
        print("Saving MAT file...")

        with h5py.File(file_path, "w") as f:
            f.create_dataset(
                "geo_data",
                data=geo_cube,
                compression="gzip"
            )

        print("MAT saved:", file_path)



    # ---------------------------------------------------
    # Main Pixelwise Geolocation Function
    # ---------------------------------------------------

    def compute_pixelwise_geolocation(
            self,
            cube_mat,
            meta_data,
            hsi_data,
            plot_locations,
            geo_localize_output_path,
            output_prefix,
            line_start=0,
            line_end=None,
            offset_cm=0,
            direction_avg_points=2
        ):

        print("Computing pixelwise geolocation...")

        n_lines, n_samples, n_bands = cube_mat.shape

        if line_end is None:
            line_end = n_lines

        #VFOV = meta_data.get("field of view", 0.00025)
        #print(f"meta_data= {meta_data}")
        VFOV = 21.7

        angle_per_pixel = VFOV /n_samples 
        IFOV = angle_per_pixel

        center_pixel = n_samples / 2

        print(f"center pixel = {center_pixel}, IFOV = {IFOV}")
        
        # -------------------------------------------
        # build plot polygons
        # -------------------------------------------

        plot_polygons = []

        for p in plot_locations:

            poly = Polygon(p["gps_corners"])

            plot_polygons.append((p["plot_id"], poly))

        #print(f"Plots polygons  =   {p}")
        
        results = []
        

        # -------------------------------------------
        # process cube line by line
        # -------------------------------------------

        for y in range(line_start, line_end):

            nav = hsi_data.iloc[y]
            #print(f"Line  = {nav}")


            lat, lon, alt, roll, pitch, yaw = self.get_navigation_parameters(nav)
            #print(f"lat = {lat}, lon = {lon}, lat = {alt}, roll = {roll}, pitch = {pitch}, yaw = {yaw}")
            

            # compute yaw from navigation if missing
            if yaw is None:
                print("Computing missing yaw")
                yaw = self.compute_flight_direction(
                    hsi_data,
                    y,
                    direction_avg_points
                )

            # apply sensor offset
            lon, lat = self.apply_sensor_offset(
                lon,
                lat,
                yaw,
                offset_cm
            )
            #print(f"after offst lat = {lat}, lon = {lon}, offset_cm = {offset_cm}, yaw = {yaw}")


            # read cube line
            cube_line = cube_mat[y, :, :]

            for x in range(n_samples):

                ground_offset = self.compute_pixel_offset(
                    x,
                    center_pixel,
                    IFOV,
                    alt
                )
                

                #if x > 620: 
                    #print (f"pixel = {x}    ground_offset = {ground_offset, }\n")

                dx = ground_offset * np.cos(yaw)
                dy = ground_offset * np.sin(yaw)
                #dx = ground_offset * np.cos(np.radians(yaw))
                #dy = ground_offset * np.sin(np.radians(yaw))
                

                dlon, dlat = self.meters_to_gps(dx, dy, lat)

                pixel_lon = lon + dlon
                pixel_lat = lat + dlat

                point = Point(pixel_lon, pixel_lat)

                pixel_class = self.classify_pixel(
                    point,
                    plot_polygons
                )

                results.append([
                    x,
                    y,
                    pixel_lon,
                    pixel_lat,
                    pixel_class
                ])

        df = pd.DataFrame(
            results,
            columns=[
                "pixel_x",
                "pixel_y",
                "longitude",
                "latitude",
                "class"
            ]
        )
    
        self.save_txt(
            df,
            os.path.join(
                geo_localize_output_path, "pixel_geolocation.txt"
            )
        )

        self.save_mat(
            df,
            os.path.join(
                geo_localize_output_path, "pixel_geolocation.mat"
            ),
            n_lines,
            n_samples
        )

        return df
    



    def Extract_Pixelwise_Geolocation_Pipeline(self, HSI_DJI_Synch_File_Txt, Wheat_Plot_Locations__File, Cube_Mat_File, Pixel_Geo_Location_Path, Output_Path):

        print("Starting HSI Mosaic Pipeline")

        # -------------------------------------------------
        # 1. Read synchronized HSI navigation file
        # -------------------------------------------------
        #print("Loading HSI synchronization data...")
        hsi_data = self.localization_tools.load_hsi_LCF_DJI_synch_file(HSI_DJI_Synch_File_Txt)   # from other file/module



        # ---------------------------------------------
        # Print preview (optional)
        # ---------------------------------------------

        #print("\nHSI Synch Data (Top 3 rows):")
        #print(hsi_data["GPS_Time"].iloc[:3])

        #print("\nColumn types:")
        #print(hsi_data.dtypes)



        # -------------------------------------------------
        # 2. Read plot information
        # -------------------------------------------------
        print("Loading plot information...")
        plot_locations = self.mosaics_tools.read_plot_location_txt(Wheat_Plot_Locations__File)
        plot_locations = self.mosaics_tools.convert_plot_utm_to_gps(plot_locations)

        #print("txt form plot locations after conversion", plot_locations)



        # -------------------------------------------------
        # 3. Load hyperspectral cube
        # -------------------------------------------------
        print("Loading hyperspectral cube...")
        cube_mat, meta_data = self.hsi_mat.load_and_display_mat( Cube_Mat_File)
        #cube_data = load_cube(cube_path)   # from other file/module



        # -------------------------------------------------
        # 4. Compute pixel-wise geolocation
        # -------------------------------------------------
        print("Computing pixel-wise geolocation...")

        geo_df = self.compute_pixelwise_geolocation(
            cube_mat=cube_mat,
            meta_data=meta_data,
            hsi_data=hsi_data,
            plot_locations=plot_locations,
            geo_localize_output_path= Output_Path,
            output_prefix="geolocation",
            line_start=0,
            line_end=None,
            offset_cm=0,
            direction_avg_points=4
        )

        # -------------------------------------------------
        # 5. Create mosaics at selected bands
        # -------------------------------------------------
        print("Creating mosaics...")
 
        #test.create_orthomosaic_mask_utm(Geo_Location_Path, Mosaic_output_Path, resolution=0.1)

        self.mosaics_tools.export_scanlines_and_points_geojson(Pixel_Geo_Location_Path, Output_Path)

        print("Pipeline finished successfully")
