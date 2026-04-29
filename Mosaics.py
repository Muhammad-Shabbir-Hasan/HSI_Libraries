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

    def __init__(self):
        self.localization_tools = localization.Localization_Tools()
        self.hsi_mat = hsi.Mat()
      


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



    def read_pixel_geolocation_mat(self, mat_file, variable):
       
        data = self.hsi_mat.read_mat_file(mat_file, variable)
        print("Data shape:", data.shape)

        return data

    def pixel_geolocation_mat_to_jpg(self, mat_file, output_folder):

        import h5py
        import numpy as np
        from PIL import Image, ImageDraw
        import os

        print("Loading MAT file...")

        with h5py.File(mat_file, 'r') as f:
            geo_data = np.array(f["geo_data"])

        #geo_data = self.read_pixel_geolocation_mat (mat_file, "geo_data")  # need to test this function

        class_map = geo_data[:, :, 2].astype(int)

        height, width = class_map.shape

        # -----------------------------------------
        # create RGB image
        # -----------------------------------------

        img = np.zeros((height, width, 3), dtype=np.uint8)

        unique_classes = np.unique(class_map)
        unique_classes = unique_classes[unique_classes > 0]

        print("Classes found:", unique_classes)

        # -----------------------------------------
        # generate colors
        # -----------------------------------------

        np.random.seed(42)
        color_map = {}

        for cls in unique_classes:
            color_map[cls] = np.random.randint(0, 255, 3)

        color_map[0] = np.array([0, 0, 0])

        # assign colors
        for cls, color in color_map.items():
            img[class_map == cls] = color

        # convert to PIL image
        mosaic_img = Image.fromarray(img)

        # -----------------------------------------
        # create legend image
        # -----------------------------------------

        legend_width = 250
        legend_height = max(height, 30 * (len(unique_classes) + 1))

        legend_img = Image.new("RGB", (legend_width, legend_height), (255, 255, 255))
        draw = ImageDraw.Draw(legend_img)

        y_offset = 10

        for cls in unique_classes:

            color = tuple(color_map[cls])

            draw.rectangle([10, y_offset, 40, y_offset + 20], fill=color)
            draw.text((50, y_offset), f"Plot {cls}", fill=(0, 0, 0))

            y_offset += 30

        # -----------------------------------------
        # combine both images
        # -----------------------------------------

        combined_width = width + legend_width
        combined_height = max(height, legend_height)

        combined_img = Image.new("RGB", (combined_width, combined_height), (255, 255, 255))

        # paste mosaic
        combined_img.paste(mosaic_img, (0, 0))

        # paste legend on right
        combined_img.paste(legend_img, (width, 0))

        # -----------------------------------------
        # save final output
        # -----------------------------------------

        os.makedirs(output_folder, exist_ok=True)

        output_path = os.path.join(output_folder, "pixel_geolocation_plotwise.jpg")
        combined_img.save(output_path)

        print("Combined image saved:", output_path)

        

    def save_to_mat(self, variable, file_path, var_name="data", use_hdf5=False):

        import numpy as np
        import os

        # ensure folder exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        print("Saving MAT file:", file_path)

        # -----------------------------------------
        # Case 1: MATLAB v7 (scipy)
        # -----------------------------------------

        if not use_hdf5:

            import scipy.io

            if isinstance(variable, dict):
                scipy.io.savemat(file_path, variable)
            else:
                scipy.io.savemat(file_path, {var_name: variable})

            print("Saved using scipy (MAT v7)")

        # -----------------------------------------
        # Case 2: MATLAB v7.3 (HDF5)
        # -----------------------------------------

        else:

            import h5py

            with h5py.File(file_path, "w") as f:

                if isinstance(variable, dict):

                    for key, value in variable.items():
                        f.create_dataset(key, data=np.array(value))

                else:
                    f.create_dataset(var_name, data=np.array(variable))

            print("Saved using h5py (MAT v7.3)")


    def save_plotwise_information_csv(self, data, output_path):

        import pandas as pd
        import os

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        df = pd.DataFrame(data, columns=[
            "pixel_x",
            "pixel_y",
            "longitude",
            "latitude",
            "class",
            "folder"
        ])

        df.to_csv(output_path, index=False)

        print("Saved CSV:", output_path)



    def combine_tiff_pixel_geolocation_jpg(self, tiff_image, plotwise_image, output_folder):

        from PIL import Image
        import os

        print("Loading images...")

        img1 = Image.open(tiff_image)
        img2 = Image.open(plotwise_image)

        # -----------------------------------------
        # match heights (resize only one image)
        # -----------------------------------------

        h1 = img1.height
        h2 = img2.height

        if h1 != h2:

            print("Resizing images to match height...")

            # resize second image to match first image height
            new_width = int(img2.width * (h1 / h2))
            img2 = img2.resize((new_width, h1))

        # -----------------------------------------
        # combine side by side
        # -----------------------------------------

        combined_width = img1.width + img2.width
        combined_height = img1.height  # both same now

        combined_img = Image.new("RGB", (combined_width, combined_height))

        combined_img.paste(img1, (0, 0))
        combined_img.paste(img2, (img1.width, 0))

        # -----------------------------------------
        # save output
        # -----------------------------------------

        os.makedirs(output_folder, exist_ok=True)

        output_path = os.path.join(output_folder, "HSI_and_pixel_geolocation.jpg")
        combined_img.save(output_path)

        print("Combined image saved:", output_path)




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

        print(f"Computing pixelwise geolocation...line start = {line_start}, line end {line_end}")

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

        print(f"Plots polygons  =   {p}")
        
        results = []
        yaw_mat = []
        

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

            #yaw_mat.append([yaw])

         
           


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

        #self.mosaics_tools.save_to_mat(yaw_mat, "Intermediate_date\cube.mat", var_name="estimated_yaw", use_hdf5=True)

        return df
    



    def Extract_Pixelwise_Geolocation_Pipeline(self,
                                                HSI_DJI_Synch_File_Txt,
                                                  Wheat_Plot_Locations_File,
                                                    Cube_Mat_File,
                                                      Pixel_Geo_Location_Path, Output_Path,
                                                      line_start = 0,
                                                      line_end = None,
                                                      ):

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
        plot_locations = self.mosaics_tools.read_plot_location_txt(Wheat_Plot_Locations_File)
        plot_locations = self.mosaics_tools.convert_plot_utm_to_gps(plot_locations)

        print("txt form plot locations after conversion", plot_locations)



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
            line_start=line_start,
            line_end=line_end,
            offset_cm=0,
            direction_avg_points=4
        )

        print("Computation pixel-wsie geolocation finished successfully")




        def extract_plot_data(self, geo_data, folder_id):

            import numpy as np

            lon = geo_data[:, :, 0]
            lat = geo_data[:, :, 1]
            cls = geo_data[:, :, 2].astype(int)

            height, width = cls.shape

            plots = {}

            for plot_id in np.unique(cls):

                if plot_id == 0:
                    continue  # skip background

                mask = cls == plot_id

                # create empty container
                plot_cube = np.zeros((height, width, 4), dtype=np.float32)

                plot_cube[:, :, 0] = lon
                plot_cube[:, :, 1] = lat
                plot_cube[:, :, 2] = cls
                plot_cube[:, :, 3] = folder_id  # store folder index

                # keep only plot pixels
                plot_cube[~mask] = np.nan

                plots[plot_id] = plot_cube

            return plots
        




    def extract_plot_data(self, geo_data, folder_id):

        import numpy as np

        lon = geo_data[:, :, 0]
        lat = geo_data[:, :, 1]

        cls = geo_data[:, :, 2]

        # FIX: clean NaNs
        cls = np.nan_to_num(cls, nan=0)
        cls = cls.astype(int)

        plots = {}

        y_indices, x_indices = np.indices(cls.shape)

        for plot_id in np.unique(cls):

            if plot_id <= 0:   # skip background + invalid
                continue

            mask = cls == plot_id

            x = x_indices[mask]
            y = y_indices[mask]

            pixels = np.stack([
                x,
                y,
                lon[mask],
                lat[mask],
                cls[mask],
                np.full(np.sum(mask), folder_id)
            ], axis=1)

            plots[plot_id] = pixels

        return plots


    # discarde this fucntion due to slow process, used txt saving
    def merge_plot_data_mat_string(self, global_plots, new_plots, sub_folder_name):

        import numpy as np

        for plot_id, pixels in new_plots.items():

            # -----------------------------------------
            # convert numeric → string + folder name
            # -----------------------------------------

            str_pixels = []

            for row in pixels:

                str_row = [
                    str(int(row[0])),     # x
                    str(int(row[1])),     # y
                    str(row[2]),          # lon
                    str(row[3]),          # lat
                    str(int(row[4])),     # class
                    sub_folder_name       # ✅ folder string
                ]

                str_pixels.append(str_row)

            str_pixels = np.array(str_pixels, dtype=object)  # (N, 6)

            # -----------------------------------------
            # merge
            # -----------------------------------------

            if plot_id not in global_plots:
                global_plots[plot_id] = str_pixels
            else:
                global_plots[plot_id] = np.vstack(
                    (global_plots[plot_id], str_pixels)
                )

        return global_plots


    def merge_plot_data_for_txt(self, global_plots, new_plots, sub_folder_name):

        import numpy as np

        for plot_id, pixels in new_plots.items():

            # -----------------------------------------
            # ensure pixels is numpy array
            # -----------------------------------------
            pixels = np.asarray(pixels)

            # -----------------------------------------
            # convert columns to string (vectorized)
            # -----------------------------------------

            x   = pixels[:, 0].astype(int).astype(str)
            y   = pixels[:, 1].astype(int).astype(str)
            lon = pixels[:, 2].astype(str)
            lat = pixels[:, 3].astype(str)
            cls = pixels[:, 4].astype(int).astype(str)

            # folder column (same value repeated)
            folder = np.full(pixels.shape[0], sub_folder_name, dtype=object)

            # -----------------------------------------
            # stack into (N, 6)
            # -----------------------------------------

            str_pixels = np.column_stack([x, y, lon, lat, cls, folder])

            # -----------------------------------------
            # merge
            # -----------------------------------------

            if plot_id not in global_plots:
                global_plots[plot_id] = str_pixels
            else:
                global_plots[plot_id] = np.vstack(
                    (global_plots[plot_id], str_pixels)
                )

        return global_plots

    def merging_plotwise_scan_information_mat(self, base_folder, output_folder):

        import os

        global_plots = {}
     

        print("Scanning folders...")

        for root, dirs, files in os.walk(base_folder):

            if "pixel_geolocation.mat" in files:

                mat_path = os.path.join(root, "pixel_geolocation.mat")
                # ✅ get folder name
                folder_name = os.path.basename(root)

                print("Processing:", mat_path)
                print("Folder:", folder_name)

                geo_data = self.mosaics_tools.read_pixel_geolocation_mat(mat_path, "geo_data")

                plots = self.extract_plot_data(geo_data, 1)

                global_plots = self.merge_plot_data_for_txt(global_plots, plots, folder_name)

        
        # -----------------------------------------
        # Save each plot separately
        # -----------------------------------------
        print(f"Number of plots = {len(global_plots)}")
        for plot_id, data in global_plots.items():
            #print(f"Plot {plot_id}: shape = {data.shape}")
            output_path = os.path.join(
                output_folder, f"plot_{int(plot_id)}",
                f"plot_{int(plot_id)}.txt"
            )

            #self.hsi_mat.save_mat_file(data, output_path, "plots_scan_info", use_hdf5 =False )
            self.mosaics_tools.save_plotwise_information_csv(data, output_path)
        print("All plots saved.")


"""

    def Create_Mosaics  (self,
                                                HSI_DJI_Synch_File_Txt,
                                                  Wheat_Plot_Locations__File,
                                                    Cube_Mat_File,
                                                      Pixel_Geo_Location_Path, Output_Path,
                                                      line_start = 0,
                                                      line_end = None,
                                                      ):


        # -------------------------------------------------
        # 5. Create mosaics at selected bands
        # -------------------------------------------------
        print("Creating mosaics...")
 
        #test.create_orthomosaic_mask_utm(Geo_Location_Path, Mosaic_output_Path, resolution=0.1)

        self.mosaics_tools.export_scanlines_and_points_geojson(Pixel_Geo_Location_Path, Output_Path)

        print("Pipeline finished successfully")

"""




class Plot_Mosaic:

    def __init__(self):
        self.localization_tools = localization.Localization_Tools()
        self.mosaics_tools = Mosaics_Tools()
        self.hsi_mat = hsi.Mat()
        self.hsi_cube = hsi.Cube()
        



    # -------------------------------------------------
    # 1. Read all plot files
    # -------------------------------------------------
    """
    def read_all_plot_files(self, base_folder):

        import os
        import pandas as pd

        plot_files = []

        for folder in os.listdir(base_folder):

            # -----------------------------------------
            # check folder starts with "plot_"
            # -----------------------------------------
            if not folder.startswith("plot_"):
                continue

            folder_path = os.path.join(base_folder, folder)

            if not os.path.isdir(folder_path):
                continue

            # -----------------------------------------
            # read files inside plot_X folder
            # -----------------------------------------
            for f in os.listdir(folder_path):

                if f.endswith(".txt") or f.endswith(".csv"):

                    file_path = os.path.join(folder_path, f)

                    df = pd.read_csv(file_path)

                    plot_files.append((folder, f, df))

        return plot_files
    """

    def read_all_plot_files(self, base_folder):

        import os
        import pandas as pd

        all_dfs = []

        for folder in os.listdir(base_folder):

            # -----------------------------------------
            # check folder starts with "plot_"
            # -----------------------------------------
            if not folder.startswith("plot_"):
                continue

            folder_path = os.path.join(base_folder, folder)

            if not os.path.isdir(folder_path):
                continue

            # -----------------------------------------
            # read files inside plot_X folder
            # -----------------------------------------
            for f in os.listdir(folder_path):

                if f.endswith(".txt") or f.endswith(".csv"):

                    file_path = os.path.join(folder_path, f)

                    df = pd.read_csv(file_path)

                    # -----------------------------------------
                    # add plot name column
                    # -----------------------------------------
                    df["plot"] = folder   # <-- NEW COLUMN

                    all_dfs.append(df)

        # -----------------------------------------
        # combine all into single dataframe
        # -----------------------------------------
        if len(all_dfs) > 0:
            final_df = pd.concat(all_dfs, ignore_index=True)
        else:
            final_df = pd.DataFrame()

        print("Final combined shape:", final_df.shape)

        return final_df



    # -------------------------------------------------
    # 2. Load cube (DUMMY)
    # -------------------------------------------------
    def load_cube_mat(self, cube_path):

        print("Loading cube :", cube_path)
        cube_mat, meta = self.hsi_mat.load_and_display_mat(cube_path)
        
        return cube_mat


    # -------------------------------------------------
    # 3. Extract pixel spectra
    # -------------------------------------------------

    def extract_pixel_spectra(self, df, cube_root):

        import os

        # -----------------------------------------
        # output: plot-wise dictionary
        # -----------------------------------------
        plot_data = {}

        # -----------------------------------------
        # group by folder (load cube once)
        # -----------------------------------------
        grouped_folder = df.groupby("folder")

        for folder, df_folder in grouped_folder:

            cube_path = os.path.join(cube_root, folder, "combined_cube.mat")

            print("Loading cube:", cube_path)

            cube = self.load_cube_mat(cube_path)   # load ONCE

            # -----------------------------------------
            # now group inside by plot
            # -----------------------------------------
            grouped_plot = df_folder.groupby("plot")

            for plot_name, df_plot in grouped_plot:

                #if plot_name != "plot_1":
                #    continue

                print(f"plot name = {plot_name} , {folder}")
                # initialize if not exists
                if plot_name not in plot_data:
                    plot_data[plot_name] = []

                # -----------------------------------------
                # extract all pixels for this plot
                # -----------------------------------------
                for _, row in df_plot.iterrows():

                    x = int(row["pixel_x"])
                    y = int(row["pixel_y"])

                    spectra = cube[y, x, :]  # (bands)

                    plot_data[plot_name].append([
                        row["longitude"],
                        row["latitude"],
                        spectra
                    ])

        return plot_data


    # -------------------------------------------------
    # 4. Compute resolution
    # -------------------------------------------------

    def compute_resolution(self, pixels):

        import numpy as np

        result = {}

        for plot_name, data in pixels.items():

            # -----------------------------------------
            # extract lon, lat (CORRECT INDEX)
            # -----------------------------------------
            lon = np.array([p[0] for p in data])
            lat = np.array([p[1] for p in data])

            # -----------------------------------------
            # compute differences
            # -----------------------------------------
            dlon = np.diff(np.sort(np.unique(lon)))
            dlat = np.diff(np.sort(np.unique(lat)))

            dlon = dlon[dlon > 0]
            dlat = dlat[dlat > 0]

            res_x = np.min(dlon) if len(dlon) > 0 else 1e-8
            res_y = np.min(dlat) if len(dlat) > 0 else 1e-8

            result[plot_name] = {
                "res_x": res_x,
                "res_y": res_y,
                "min_lon": lon.min(),
                "max_lon": lon.max(),
                "min_lat": lat.min(),
                "max_lat": lat.max()
            }

            print(f"{plot_name} → dlon:{res_x}, dlat:{res_y}")

        return result

    # -------------------------------------------------
    # 5. Create cube
    # -------------------------------------------------

    def create_plotwise_cube(self, pixels, plot_res):

        import numpy as np

        plot_cubes = {}

        for plot_name, data in pixels.items():

            print(f"\nProcessing {plot_name}")

            # -----------------------------------------
            # get resolution info
            # -----------------------------------------
            res = plot_res[plot_name]

            dlon = float(res["res_x"])
            dlat = float(res["res_y"])

            min_lon = float(res["min_lon"])
            max_lon = float(res["max_lon"])
            min_lat = float(res["min_lat"])
            max_lat = float(res["max_lat"])

            # -----------------------------------------
            # extract data
            # -----------------------------------------
            lon = np.array([p[0] for p in data])
            lat = np.array([p[1] for p in data])
            spectra_list = [p[2] for p in data]

            bands = len(spectra_list[0])

            # -----------------------------------------
            # compute grid size
            # -----------------------------------------
            width  = int(np.ceil((max_lon - min_lon) / dlon)) + 1
            height = int(np.ceil((max_lat - min_lat) / dlat)) + 1

            print("Grid size:", height, width, bands)

            # -----------------------------------------
            # initialize cube + counter
            # -----------------------------------------
            cube = np.zeros((height, width, bands), dtype=np.float32)
            count = np.zeros((height, width), dtype=np.int32)

            # -----------------------------------------
            # map pixels to grid
            # -----------------------------------------
            for i in range(len(data)):

                col = int(round((lon[i] - min_lon) / dlon))
                row = int(round((max_lat - lat[i]) / dlat))

                # bounds check
                if row < 0 or row >= height or col < 0 or col >= width:
                    continue

                cube[row, col, :] += spectra_list[i]
                count[row, col] += 1

            # -----------------------------------------
            # handle overlaps (average)
            # -----------------------------------------
            count_expanded = count[:, :, None].astype(np.float32)

            # avoid division by zero
            count_expanded[count_expanded == 0] = np.nan

            cube = cube / count_expanded

            # -----------------------------------------
            # store
            # -----------------------------------------
            plot_cubes[plot_name] = cube

        return plot_cubes



    # -------------------------------------------------
    # 6. Save BIL
    # -------------------------------------------------
    def save_bil(self, cube, bil_path):

        import numpy as np

        bil = np.transpose(cube, (0, 2, 1))  # (lines, bands, samples)

        bil.astype(np.float32).tofile(bil_path)

        print("Saved BIL:", bil_path)


    # -------------------------------------------------
    # 7. Create HDR
    # -------------------------------------------------
    def create_hdr(self, sample_hdr, output_hdr, width, height, bands):

        with open(sample_hdr, "r") as f:
            lines = f.readlines()

        new_lines = []

        for line in lines:

            if "samples" in line:
                new_lines.append(f"samples = {width}\n")

            elif "lines" in line:
                new_lines.append(f"lines = {height}\n")

            elif "bands" in line:
                new_lines.append(f"bands = {bands}\n")

            else:
                new_lines.append(line)

        with open(output_hdr, "w") as f:
            f.writelines(new_lines)

        print("HDR saved:", output_hdr)


    # -------------------------------------------------
    # 8. Dummy BIL → MAT
    # -------------------------------------------------
    def bil_to_mat(self, bil_path, mat_path):

        print("Dummy conversion:", bil_path, "→", mat_path)


    # -------------------------------------------------
    # 9. MAIN PIPELINE
    # -------------------------------------------------
    """
    def generate_plot_cubes(self, base_folder, cube_root, sample_hdr):

        import os

        plot_files = self.read_all_plot_files(base_folder)
        #print(f"plot_files = {plot_files}")
        for plot_folder, file_name, df in plot_files:

            #print("\nProcessing:", plot_folder, file_name)
        
    
            # -----------------------------------------
            # Step 1: Extract spectra
            # -----------------------------------------
            pixels = self.extract_pixel_spectra(df, cube_root)
            print("\npixels:", pixels)
        
            # -----------------------------------------
            # Step 2: Compute resolution
            # -----------------------------------------
            res_x, res_y = self.compute_resolution(pixels)
            print(f"resolution = {res_x}  and {res_y}")
        
        
            # -----------------------------------------
            # Step 3: Create cube
            # -----------------------------------------
            cube, width, height, bands = self.create_plot_cube(
                pixels, res_x, res_y
            )

            # -----------------------------------------
            # Step 4: Output paths
            # -----------------------------------------
            name = os.path.splitext(file_name)[0]

            out_dir = os.path.join(base_folder, "plots")

            bil_path = os.path.join(out_dir, name + ".bil")
            hdr_path = os.path.join(out_dir, name + ".hdr")
            mat_path = os.path.join(out_dir, name + ".mat")

            # -----------------------------------------
            # Step 5: Save BIL
            # -----------------------------------------
            self.save_bil(cube, bil_path)

            # -----------------------------------------
            # Step 6: Create HDR
            # -----------------------------------------
            self.create_hdr(sample_hdr, hdr_path, width, height, bands)

            # -----------------------------------------
            # Step 7: Convert to MAT
            # -----------------------------------------
            self.bil_to_mat(bil_path, mat_path)
        

        print("\nAll plots processed successfully.")
    """




class PlotMatSaver:

    # -------------------------------------------------
    # 1. Dummy MAT saver (replace later)
    # -------------------------------------------------
    def save_mat(self, data, output_path, var_name="data"):

        import os
        import numpy as np

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"Saving MAT: {output_path}")
        print("Shape:", data.shape)

        # -----------------------------------------
        # choose format based on size
        # -----------------------------------------
        data = np.asarray(data)

        size_gb = data.nbytes / (1024**3)

        try:
            # -----------------------------------------
            # small file → MATLAB v7
            # -----------------------------------------
            if size_gb < 2:

                import scipy.io

                scipy.io.savemat(
                    output_path,
                    {var_name: data}
                )

                print("Saved using scipy (MAT v7)")

            # -----------------------------------------
            # large file → MATLAB v7.3 (HDF5)
            # -----------------------------------------
            else:

                import h5py

                with h5py.File(output_path, "w") as f:

                    f.create_dataset(
                        var_name,
                        data=data,
                        compression="gzip"
                    )

                print("Saved using h5py (MAT v7.3)")

        except Exception as e:

            print("Error saving MAT:", e)

    # -------------------------------------------------
    # 2. Extract spectra only (ignore lat/lon)
    # -------------------------------------------------
    def extract_spectra_only(self, data):

        import numpy as np

        # data format: [lon, lat, spectra]
        spectra_list = [p[2] for p in data]

        # stack into (N, bands)
        spectra_array = np.vstack(spectra_list).astype(np.float32)

        return spectra_array


    # -------------------------------------------------
    # 3. Save all plots (MAIN)
    # -------------------------------------------------
    def save_all_plots(self, pixels, base_output_path):

        import os

        for plot_name, data in pixels.items():

            print(f"\nProcessing {plot_name}")

            # -----------------------------------------
            # create plot folder
            # -----------------------------------------
            plot_folder = os.path.join(base_output_path, plot_name)
            os.makedirs(plot_folder, exist_ok=True)

            # -----------------------------------------
            # extract spectra
            # -----------------------------------------
            spectra_array = self.extract_spectra_only(data)

            # -----------------------------------------
            # output path
            # -----------------------------------------
            output_mat = os.path.join(plot_folder, f"{plot_name}.mat")

            # -----------------------------------------
            # save
            # -----------------------------------------
            self.save_mat(spectra_array, output_mat)

        print("\nAll plots saved successfully.")








