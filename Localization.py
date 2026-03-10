
import os
import numpy as np
import pandas as pd
import simplekml
import colorsys

import pandas as pd
import numpy as np
import os



import numpy as np
import os


class Localization_Tools:

    # -------------------------------------------------------
    # GENERIC TXT SAVE FUNCTION
    # -------------------------------------------------------

    def save_txt(self, data, output_path, filename):

        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        os.makedirs(output_path, exist_ok=True)

        file_path = os.path.join(output_path, filename)

        df.to_csv(file_path, sep="\t", index=False)

        print("Saved:", file_path)

        return file_path


    # -------------------------------------------------------
    # SAVE FLIGHT PATH TO KML
    # -------------------------------------------------------

    def save_to_kml(self, path_points, output_path):

        kml = simplekml.Kml()

        folder_values = sorted(list({d['Folder'] for d in path_points}))
        n = len(folder_values)

        def generate_color(i, total):
            h = i / float(total)
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            return "ff" + f"{int(b*255):02x}" + f"{int(g*255):02x}" + f"{int(r*255):02x}"

        folder_styles = {}

        for i, folder in enumerate(folder_values):

            color = generate_color(i, n)

            style = simplekml.Style()
            style.iconstyle.color = color
            style.iconstyle.scale = 1.2
            style.iconstyle.icon.href = \
                "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"

            folder_styles[folder] = style

        for data in path_points:

            p = kml.newpoint(
                name=f"Time: {data['GPS_Time']}",
                coords=[(data['Longitude'], data['Latitude'], data['Altitude'])]
            )

            p.style = folder_styles[data['Folder']]

        output_kml = os.path.join(output_path, "Path_Synch_Data.kml")

        kml.save(output_kml)

        print("KML saved:", output_kml)

    def load_dji_file_txt(self, dji_file):

        # ---------------------------------------------
        # Load DJI file
        # ---------------------------------------------

        dji = pd.read_csv(dji_file, sep="\t", skiprows=1)

        # ---------------------------------------------
        # Assign headers
        # ---------------------------------------------

        dji.columns = [
            'GPSTime','Latitude','Longitude','Altitude_ft',
            'hSpeed','xSpeed','ySpeed','zSpeed',
            'Pitch','Roll','Yaw','Direction'
        ]

        # ---------------------------------------------
        # Convert numeric columns safely
        # ---------------------------------------------

        for col in dji.columns:
            try:
                dji[col] = pd.to_numeric(dji[col])
            except:
                pass

        # ---------------------------------------------
        # Sort by time (important for interpolation)
        # ---------------------------------------------

        dji = dji.sort_values("GPSTime").reset_index(drop=True)

        # ---------------------------------------------
        # Preview
        # ---------------------------------------------

        #print("\nDJI Data (Top 3 rows):")
        #print(dji.head(3))

        #print("\nDJI Column types:")
        #print(dji.dtypes)

        return dji



    # ---------------------------------------------
    # Distance function (Haversine)
    # ---------------------------------------------

    def haversine(self, lat1, lon1, lat2, lon2):

        R = 6371000

        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)
        lat2 = np.radians(lat2)
        lon2 = np.radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
        c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))

        return R*c



    def load_times_lcf_file_txt(self, times_lcf_file):

        # ---------------------------------------------
        # Load file
        # ---------------------------------------------

        times_lcf_data = pd.read_csv(times_lcf_file, sep="\t")

        # ---------------------------------------------
        # Convert numeric columns safely
        # ---------------------------------------------

        for col in times_lcf_data.columns:
            try:
                times_lcf_data[col] = pd.to_numeric(times_lcf_data[col])
            except:
                pass

        # ---------------------------------------------
        # Print preview
        # ---------------------------------------------

        #print("\nTimes_LCF Data (Top 3 rows):")
        #print(times_lcf_data.head(3))

        #print("\nColumn types:")
        #print(times_lcf_data.dtypes)

        return times_lcf_data

    def load_bil_times_file(self, bil_times_file, prefix):

        # ---------------------------------------------
        # Load BIL.times file
        # ---------------------------------------------

        bil_times = pd.read_csv(bil_times_file)

        # ---------------------------------------------
        # Convert numeric columns safely
        # ---------------------------------------------

        for col in bil_times.columns:
            try:
                bil_times[col] = pd.to_numeric(bil_times[col])
            except:
                pass



        # ---------------------------------------------
        # Extract file number from source_file
        # ---------------------------------------------

        if "source_file" in bil_times.columns:

            bil_times["file_number"] = (
                bil_times["source_file"]
                .str.replace(".bil.times", "", regex=False)
                .str.extract(r'_(\d+)$')
                .astype(float)
            )

        if prefix is not None:

            print("Filtering prefix:", prefix)

            bil_times = bil_times[bil_times["source_file"].str.startswith(prefix)]

        # ---------------------------------------------
        # Ensure timestamp column is numeric
        # ---------------------------------------------

        if "gps_seconds" in bil_times.columns:
            bil_times["gps_seconds"] = pd.to_numeric(bil_times["gps_seconds"], errors="coerce")

        # ---------------------------------------------
        # Sort by time
        # ---------------------------------------------

        if "gps_seconds" in bil_times.columns:
            bil_times = bil_times.sort_values("gps_seconds").reset_index(drop=True)

        # ---------------------------------------------
        # Print preview
        # ---------------------------------------------

        #print("\nBIL Times Data (Top 3 rows):")
        #print(bil_times.head(3))

        #print("\nColumn types:")
        #print(bil_times.dtypes)

        return bil_times


    def load_lcf_file(self, lcf_file, prefix):

        # ---------------------------------------------
        # Load LCF file
        # ---------------------------------------------

        lcf_data = pd.read_csv(lcf_file)

        # ---------------------------------------------
        # Convert numeric columns safely
        # ---------------------------------------------

        for col in lcf_data.columns:
            try:
                lcf_data[col] = pd.to_numeric(lcf_data[col])
            except:
                pass

        # ---------------------------------------------
        # Ensure GPS_Time numeric
        # ---------------------------------------------

        if "GPS_Time" in lcf_data.columns:
            lcf_data["GPS_Time"] = pd.to_numeric(lcf_data["GPS_Time"], errors="coerce")

        # ---------------------------------------------
        # Extract file number from source_file
        # ---------------------------------------------

        if "source_file" in lcf_data.columns:

            lcf_data["file_number"] = (
                lcf_data["source_file"]
                .str.replace(".lcf", "", regex=False)
                .str.extract(r'_(\d+)$')
                .astype(float)
            )

        # ---------------------------------------------------
        # Prefix filtering
        # ---------------------------------------------------

        if prefix is not None:

            print("Filtering prefix:", prefix)

            lcf_data = lcf_data[lcf_data["source_file"].str.startswith(prefix)]


        # ---------------------------------------------
        # Sort by time
        # ---------------------------------------------

        if "GPS_Time" in lcf_data.columns:
            lcf_data = lcf_data.sort_values("GPS_Time").reset_index(drop=True)

        # ---------------------------------------------
        # Preview
        # ---------------------------------------------

        #print("\nLCF Data (Top 3 rows):")
        #print(lcf_data.head(3))

        #print("\nColumn types:")
        #print(lcf_data.dtypes)

        return lcf_data


    def find_closest_dji_points(self, time_lcf_file, dji_file, output_path, top_n=5):

        # ---------------------------------------------
        # Load data using existing functions
        # ---------------------------------------------

        time_lcf = self.load_times_lcf_file_txt(time_lcf_file)
        dji = self.load_dji_file_txt(dji_file)

        # ---------------------------------------------
        # Take first HSI point
        # ---------------------------------------------

        time_lcf_time = time_lcf.iloc[0]["GPS_Time"]
        time_lcf_lat  = time_lcf.iloc[0]["latitude_deg"]
        time_lcf_lon  = time_lcf.iloc[0]["longitude_deg"]

        print("\nHSI First Point")
        print("Time:", time_lcf_time)
        print("Lat :", time_lcf_lat)
        print("Lon :", time_lcf_lon)

        # ---------------------------------------------
        # Compute distance for all DJI points
        # ---------------------------------------------

        dji["distance_m"] = self.haversine(
            time_lcf_lat,
            time_lcf_lon,
            dji["Latitude"],
            dji["Longitude"]
        )

        # ---------------------------------------------
        # Compute time difference
        # ---------------------------------------------

        dji["time_difference"] = time_lcf_time - dji["GPSTime"]

        # ---------------------------------------------
        # Find closest points
        # ---------------------------------------------

        closest = dji.sort_values("distance_m").head(top_n)

        # ---------------------------------------------
        # Display result
        # ---------------------------------------------

        print("\nTop", top_n, "Closest DJI Points")
        print(closest[[
            "GPSTime",
            "Latitude",
            "Longitude",
            "distance_m",
            "time_difference"
        ]])

        # ---------------------------------------------
        # Save result
        # ---------------------------------------------

        output_file = os.path.join(output_path, "Closest_DJI_Points.txt")

        closest.to_csv(output_file, sep="\t", index=False)

        print("\nSaved:", output_file)

        return closest





    def undersample_kml_points(self, input_kml, output_kml, target_points=9500):

        import xml.etree.ElementTree as ET
        import numpy as np
        import simplekml

        # ---------------------------------------------
        # Read coordinates from original KML
        # ---------------------------------------------
        tree = ET.parse(input_kml)
        root = tree.getroot()

        ns = {"kml": "http://www.opengis.net/kml/2.2"}

        coords = []

        for coord in root.findall(".//kml:coordinates", ns):
            values = coord.text.strip().split()
            for v in values:
                lon, lat, *rest = v.split(",")
                alt = rest[0] if rest else 0
                coords.append((float(lon), float(lat), float(alt)))

        total_points = len(coords)

        print("Total points in original KML:", total_points)

        if total_points == 0:
            print("No coordinates found.")
            return

        # ---------------------------------------------
        # Uniform under-sampling
        # ---------------------------------------------
        if total_points > target_points:
            idx = np.linspace(0, total_points - 1, target_points, dtype=int)
            sampled = [coords[i] for i in idx]
        else:
            sampled = coords

        print("Points after sampling:", len(sampled))

        # ---------------------------------------------
        # Create new valid KML
        # ---------------------------------------------
        kml = simplekml.Kml()

        for i, (lon, lat, alt) in enumerate(sampled):
            kml.newpoint(name=str(i), coords=[(lon, lat, alt)])

        kml.save(output_kml)

        print("Saved new Google-Earth compatible KML:")
        print(output_kml)

        

class HSI_Localization:

    def __init__(self):

        self.tools = Localization_Tools()


    # -------------------------------------------------------
    # LCF (200 Hz) → BIL.TIMES (161 Hz)
    # -------------------------------------------------------

    def synchronize_lcf_to_bil_times(
        self,
        lcf_file,
        bil_times_file,
        output_path,
        prefix=None,
        file_numbers=None
    ):

        print("Loading LCF:", lcf_file)
        print("Loading BIL_TIMES:", bil_times_file)


        lcf = self.tools.load_lcf_file(lcf_file, prefix)
        bil_times = self.tools.load_bil_times_file(bil_times_file, prefix)

        print("Length LCF:", len(lcf))
        print("Length BIL_TIMES:", len(bil_times))
   
        # ---------------------------------------------------
        # File number filtering
        # ---------------------------------------------------

        if file_numbers is not None:

            print("Filtering file numbers: in lcf", file_numbers)

            #print("\lcf columns:")
            #print(lcf.columns)

            #print("\nFirst few rows of lcf:")
            #print(lcf.head())

            lcf = lcf[lcf["file_number"].isin(file_numbers)]

        
        
        if file_numbers is not None:

            print("Filtering file numbers: in bil_times", file_numbers)

            #print("\nBIL_TIMES columns:")
            #print(bil_times.columns)

            #print("\nFirst few rows of bil_times:")
            #print(bil_times.head())

            bil_times = bil_times[bil_times["file_number"].isin(file_numbers)]
        
        

        print("Length LCF after filter:", len(lcf))
        print("Length bil_times after filter:", len(bil_times))
        
        # ---------------------------------------------------
        # Sort by time
        # ---------------------------------------------------

        lcf = lcf.sort_values("GPS_Time").reset_index(drop=True)
        bil_times = bil_times.sort_values("gps_seconds").reset_index(drop=True)

        lcf_times = lcf["GPS_Time"].values

        interpolated_rows = []

        # Numeric columns for interpolation
        numeric_cols = lcf.select_dtypes(include=["number"]).columns

        # Non-numeric columns copied from nearest sample
        non_numeric_cols = lcf.select_dtypes(exclude=["number"]).columns


        #print("First two LCF GPS_Time values:")
        #print(lcf["GPS_Time"].head(2).tolist())

        #print("First two BIL gps_seconds values:")
        #print(bil_times["gps_seconds"].head(2).tolist())
        base_time_bil_times = lcf["GPS_Time"].iloc[0]
        print("fist valur of lcf   =  ",base_time_bil_times)

        for _, frame in bil_times.iterrows():

            timestamp = frame["gps_seconds"]

            idx = np.searchsorted(lcf_times, timestamp)

            if idx == 0:
                before = lcf.iloc[0]
                after = lcf.iloc[1]

            elif idx >= len(lcf_times):
                before = lcf.iloc[-2]
                after = lcf.iloc[-1]

            else:
                before = lcf.iloc[idx-1]
                after = lcf.iloc[idx]


            #if idx == 0 or idx >= len(lcf_times):
            #    continue

            #before = lcf.iloc[idx-1]
            #after = lcf.iloc[idx]

            dt = after["GPS_Time"] - before["GPS_Time"]

            if dt == 0:
                continue

            weight = (timestamp - before["GPS_Time"]) / dt

            new_row = {}

            # Interpolate numeric columns
            for col in numeric_cols:

                v1 = before[col]
                v2 = after[col]

                new_row[col] = v1 + weight * (v2 - v1)

            # Copy non-numeric columns
            for col in non_numeric_cols:

                new_row[col] = before[col]

            # overwrite GPS_Time with BIL timestamp
            new_row["GPS_Time"] = timestamp

            interpolated_rows.append(new_row)


        
        if len(interpolated_rows) == 0:
            raise ValueError("No synchronized LCF points generated.")
        
        synchronized_df = pd.DataFrame(interpolated_rows)

        return self.tools.save_txt(
            synchronized_df,
            output_path,
            "HSI_Localization_Synch_Times_LCF.txt"
        )


    # -------------------------------------------------------
    # CHECK TIME OVERLAP
    # -------------------------------------------------------


    def check_time_overlap(self, hsi_time_lcf_file, dji_flight_log):

        #hsi_time_lcf_data = pd.read_csv(hsi_time_lcf_file, sep="\t")
        #dji_data = pd.read_csv(dji_flight_log, sep="\t", skiprows=1)

        dji_data = self.tools.load_dji_file_txt(dji_flight_log)
        hsi_time_lcf_data = self.tools.load_times_lcf_file_txt(hsi_time_lcf_file)
        
  
        # Apply time offset
        hsi_time_lcf_data["GPS_Time"] = hsi_time_lcf_data["GPS_Time"]

        # Time ranges
        hsi_min = hsi_time_lcf_data["GPS_Time"].min()
        hsi_max = hsi_time_lcf_data["GPS_Time"].max()

        dji_min = dji_data.iloc[:,0].min()
        dji_max = dji_data.iloc[:,0].max()

        print("HSI Time Range:", hsi_min, "to", hsi_max)
        print("DJI Time Range:", dji_min, "to", dji_max)

        # Initial offset
        offset = hsi_min - dji_min
        print("Initial Offset:", offset)

        # ------------------------------------------------
        # Calculate overlap
        # ------------------------------------------------

        overlap_start = max(hsi_min, dji_min)
        overlap_end = min(hsi_max, dji_max)

        if overlap_end > overlap_start:

            overlap_duration = overlap_end - overlap_start
            hsi_duration = hsi_max - hsi_min

            overlap_percentage = (overlap_duration / hsi_duration) * 100

        else:

            overlap_duration = 0
            overlap_percentage = 0

        print("Overlap Duration (seconds):", overlap_duration)
        print("Overlap Percentage (HSI covered by DJI):", round(overlap_percentage, 2), "%")

        return hsi_time_lcf_data, dji_data


    # -------------------------------------------------------
    # SYNCHRONIZE HSI NAVIGATION WITH DJI
    # -------------------------------------------------------

    def synchronize_hsi_with_dji(
            self,
            hsi_navigation,
            dji_flight_log,
            output_path,
            time_offset=0
        ):

        # -------------------------------------------------------
        # Prepare DJI log
        # -------------------------------------------------------

        '''
        dji_flight_log.columns = [
            'GPSTime','Latitude','Longitude','Altitude_ft',
            'hSpeed','xSpeed','ySpeed','zSpeed',
            'Pitch','Roll','Yaw','Direction'
        ]
        '''

        dji_flight_log = dji_flight_log.sort_values("GPSTime").reset_index(drop=True)

        dji_times = dji_flight_log["GPSTime"].values

        # -------------------------------------------------------
        # Apply time offset to HSI
        # -------------------------------------------------------

        hsi_navigation = hsi_navigation.copy()
        hsi_navigation["GPS_Time"] = hsi_navigation["GPS_Time"] + time_offset
        #hsi_navigation["GPS_Time"] = hsi_navigation["GPS_Time"] 


        output_position_only = []
        output_full_dji = []

        kml_points = []

        # -------------------------------------------------------
        # Interpolate using DJI ground truth
        # -------------------------------------------------------

        for _, row in hsi_navigation.iterrows():

            timestamp = row["GPS_Time"]

            idx = np.searchsorted(dji_times, timestamp)

            if idx == 0 or idx >= len(dji_times):
                continue

            before = dji_flight_log.iloc[idx-1]
            after = dji_flight_log.iloc[idx]

            dt = after["GPSTime"] - before["GPSTime"]

            if dt == 0:
                continue

            weight = (timestamp - before["GPSTime"]) / dt

            # ---------------------------------------------------
            # Interpolate position
            # ---------------------------------------------------

            latitude = before["Latitude"] + weight*(after["Latitude"]-before["Latitude"])
            longitude = before["Longitude"] + weight*(after["Longitude"]-before["Longitude"])
            altitude = before["Altitude_ft"] + weight*(after["Altitude_ft"]-before["Altitude_ft"])

            # ---------------------------------------------------
            # Create new HSI row with updated position
            # ---------------------------------------------------

            new_row = row.copy()

            new_row["latitude_deg"] = latitude
            new_row["longitude_deg"] = longitude
            new_row["altitude_m"] = altitude

            output_position_only.append(new_row)

            # ---------------------------------------------------
            # Interpolate DJI orientation and speeds
            # ---------------------------------------------------

            pitch = before["Pitch"] + weight*(after["Pitch"]-before["Pitch"])
            roll = before["Roll"] + weight*(after["Roll"]-before["Roll"])
            yaw = before["Yaw"] + weight*(after["Yaw"]-before["Yaw"])

            speed1 = before["hSpeed"] + weight*(after["hSpeed"]-before["hSpeed"])
            speed2 = before["xSpeed"] + weight*(after["xSpeed"]-before["xSpeed"])
            speed3 = before["ySpeed"] + weight*(after["ySpeed"]-before["ySpeed"])
            speed4 = before["zSpeed"] + weight*(after["zSpeed"]-before["zSpeed"])

            direction = before["Direction"] + weight*(after["Direction"]-before["Direction"])

            full_row = new_row.copy()

            full_row["DJI_Latitude"] = latitude
            full_row["DJI_Longitude"] = longitude
            full_row["DJI_Altitude_ft"] = altitude
            full_row["DJI_Pitch"] = pitch
            full_row["DJI_Roll"] = roll
            full_row["DJI_Yaw"] = yaw
            full_row["DJI_Direction"] = direction

            full_row["DJI_hSpeed"] = speed1
            full_row["DJI_xSpeed"] = speed2
            full_row["DJI_ySpeed"] = speed3
            full_row["DJI_zSpeed"] = speed4

            output_full_dji.append(full_row)

            # ---------------------------------------------------
            # KML data
            # ---------------------------------------------------

            kml_points.append({
                "GPS_Time": timestamp,
                "Latitude": latitude,
                "Longitude": longitude,
                "Altitude": altitude,
                "Folder": "HSI"
            })

        # -------------------------------------------------------
        # Save files
        # -------------------------------------------------------

        '''
        pos_file = self.tools.save_txt(
            output_position_only,
            output_path,
            "HSI_Synch_Flight_Path_LCF_Orientation.txt"
        )
        '''

        full_file = self.tools.save_txt(
            output_full_dji,
            output_path,
            "HSI_Path_Synch_LCF_DJI.txt"
        )

        self.tools.save_to_kml(kml_points, output_path)

        return full_file

    # -------------------------------------------------------
    # COMPLETE PIPELINE
    # -------------------------------------------------------

    def synchronize_DJI_LCF(
        self,
        lcf_file,
        bil_times_file,
        dji_flight_log,
        output_path,
        prefix=None,
        file_numbers=None,
        time_offset=0
    ):

        print("Starting synchronization pipeline")

        
        hsi_synch_file = self.synchronize_lcf_to_bil_times(
            lcf_file,
            bil_times_file,
            output_path,
            prefix,
            file_numbers
        )

        '''
        hsi_navigation, dji_data = self.check_time_overlap(
            hsi_synch_file,
            dji_flight_log
        )
    

        
        self.synchronize_hsi_with_dji(
            hsi_navigation,
            dji_data,
            output_path,
            time_offset
        )
        '''
        print("Pipeline completed")



def Data_Process_Set(
        DEF_DATASET_16072025_S1_ROW1 = False,
        DEF_DATASET_16072025_S1_ROW2 = False,
        DEF_DATASET_16072025_S1_ROW3 = False,
        DEF_DATASET_16072025_S1_ROW4 = False,
        DEF_DATASET_16072025_S2_ROW2 = False,
        DEF_DATASET_16072025_S2_ROW3 = False,
        DEF_DATASET_16072025_S2_ROW4 = False,
        DEF_DATASET_18072025_S1_ROW1 = False,
        DEF_DATASET_18072025_S1_ROW2 = False,
        DEF_DATASET_18072025_S1_ROW3 = False,
        DEF_DATASET_18072025_S1_ROW4 = False,
        DEF_DATASET_18072025_S1_ROW5 = False,
        
                     ):
   

    if DEF_DATASET_16072025_S1_ROW1:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row1"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[1,2,3]   # None = all files
        #file_numbers=[1]   # None = all files
  
        time_offset = 119.265

    elif DEF_DATASET_16072025_S1_ROW1:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265



    elif DEF_DATASET_16072025_S1_ROW3:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row3"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[7,8,9]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_16072025_S1_ROW4:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row4"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[11]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_16072025_S2_ROW2:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\Combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S2_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[13,14,15,16]   # None = all files
        time_offset = 0.0

    elif DEF_DATASET_16072025_S2_ROW3:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S2_Row3"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[17,18,19,20]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_16072025_S2_ROW4:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S2_Row4"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[21]   # None = all files
        time_offset = 119.265


    elif DEF_DATASET_18072025_S1_ROW1:
         
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S2_Row1"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_18072025_S1_ROW2:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_18072025_S1_ROW3:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_18072025_S1_ROW4:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265

    elif DEF_DATASET_18072025_S1_ROW5:
        
        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\1607_S1_Row2"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=[4,5,6]   # None = all files
        time_offset = 119.265

    else:

        lcf_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.lcf"
        bil_folder=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined\combined_navigation.bil.times"
        dji_file=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\01-DJI_Drone_RC4APP_Extracted\DJIFlightRecord_2025-07-16_[15-49-28]\DJIFlightRecord_2025-07-16_[15-49-28].txt"
            
        output_path=r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\01-Processed_Data\16072025_Combined"
        prefix="RS_25HeritageWhtLL_Pika IR L+_"
        file_numbers=None   # None = all files
        #file_numbers=[1]   # None = all files
  
        time_offset = 119.265
 


    return (lcf_file, bil_folder, dji_file, output_path, prefix, file_numbers, time_offset)
