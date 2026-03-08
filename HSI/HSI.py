import os
import numpy as np
import spectral as spy
import os
import glob

from typing import Tuple, Dict, Any, Optional


import scipy.io
import h5py
import matplotlib.pyplot as plt

import os
import numpy as np
import h5py


class Cube:
      
    def __init__(self):
        print("Cube initialized")
        
        
    def Load_Cube(self, Path):

        # List files in the specified directory
        files = os.listdir(Path)

        # Extract file names and convert to full path
        self.bil_file = next(
            (os.path.join(Path, f) for f in files if f.endswith("radiance.bil") or f.endswith(".bil")),
            None
        )

        self.times_file = next(
            (os.path.join(Path, f) for f in files if f.endswith(".bil.times")),
            None
        )

        self.lcf_file = next(
            (os.path.join(Path, f) for f in files if f.endswith(".lcf")),
            None
        )

        self.kml_file = next(
            (os.path.join(Path, f) for f in files if f.endswith(".kml")),
            None
        )

        self.hdr_file = next(
            (os.path.join(Path, f) for f in files if f.endswith(".bil.hdr")),
            None
        )

        print(f"\n\nSelected .bil file: {self.bil_file}")
        print(f"\nSelected .times file: {self.times_file}")
        print(f"\nSelected .lcf file: {self.lcf_file}")
        print(f"\nSelected .kml file: {self.kml_file}")
        print(f"\nSelected .hdr file: {self.hdr_file}\n\n")

        # Check if both .bil and .hdr files exist
        if self.bil_file and self.hdr_file:

            # Load the cube using the .hdr file
            self.cube = spy.open_image(os.path.join(Path, self.hdr_file))

            print("✅ Cube loaded")
            print("Cube shape (lines, samples, bands):", self.cube.shape)

        else:
            print("❌ Error: .bil or .hdr file not found in the specified folder.")
            self.cube = None


    def Show_Centered_Freq (self, cube):
    
        #print("Wavelengths:", cube.bands.centers, "...")  # show first 10 wavelengths

        spectrum = cube[1, 1] 
        print("\n\n\nTotal number of spectrum:", len(spectrum))

    def Show_Image (self, cube, r_band, g_band, b_band):
        
        spy.imshow(cube, ( r_band, g_band, b_band))  # example: bands 50=R,30=G,10=B
        #input("Press Enter to close the image window...")


    def Show_Filtered_Reflectance_as_Green(self, cube, band_index, value_min, value_max):
        """
        Selects one band, displays it in green only, filters pixels within a 12-bit range,
        assigns white to pixels inside the range, else zero, and shows the result.

        Parameters:
            cube (numpy.ndarray): Hyperspectral cube (H, W, B)
            band_index (int): Band to visualize
            value_min (int or float): Minimum value for filtering (0–4095)
            value_max (int or float): Maximum value for filtering (0–4095)
        """

        # --- 1️⃣ Select and squeeze the desired band ---
        band = np.squeeze(cube[:, :, band_index]).astype(np.float32)  # remove (H, W, 1) → (H, W)

        # --- 2️⃣ Normalize for visualization (12-bit → 0–1) ---
        band_norm = np.clip(band / 4095.0, 0, 1)

        # --- 3️⃣ Create RGB image with green channel only ---
        rgb = np.zeros((band.shape[0], band.shape[1], 3), dtype=np.float32)
        rgb[:, :, 1] = band_norm  # assign to green channel

        '''
        plt.figure(figsize=(8, 6))
        plt.title(f"Band {band_index} (Green only)")
        plt.imshow(rgb)
        plt.axis('off')
        plt.show()
        '''
        # --- 4️⃣ Apply range filter ---
        filtered = np.where((band >= value_min) & (band <= value_max), 0, 255).astype(np.uint8)
        
        
        return filtered


    def Show_Cube_as_Green_Image(self, cube, band_index):
        """
        Selects one band, displays it in green only, filters pixels within a 12-bit range,
        assigns white to pixels inside the range, else zero, and shows the result.

        Parameters:
            cube (numpy.ndarray): Hyperspectral cube (H, W, B)
            band_index (int): Band to visualize
            value_min (int or float): Minimum value for filtering (0–4095)
            value_max (int or float): Maximum value for filtering (0–4095)
        """

        # --- 1️⃣ Select and squeeze the desired band ---
        band = np.squeeze(cube[:, :, band_index]).astype(np.float32)  # remove (H, W, 1) → (H, W)

        # --- 2️⃣ Normalize for visualization (12-bit → 0–1) ---
        band_norm = np.clip(band / ((1024* 6 )-1), 0, 1)

        # --- 3️⃣ Create RGB image with green channel only ---
        rgb = np.zeros((band.shape[0], band.shape[1], 3), dtype=np.float32)
        rgb[:, :, 1] = band_norm  # assign to green channel

        '''
        plt.figure(figsize=(8, 6))
        plt.title(f"Band {band_index} (Green only)")
        plt.imshow(rgb)
        plt.axis('off')
        plt.show()
        '''
        
        
        return band


    def Extract_Rows_From_Cube(self, img, start_row, end_row):
        """
        Extracts rows between start_row and end_row from a given image array.

        Parameters:
            img (np.ndarray): Input image array (grayscale or color)
            start_row (int): Starting row index (inclusive)
            end_row (int): Ending row index (inclusive)
        
        Returns:
            cropped_img (np.ndarray): Extracted rows as a new image array
        """
        h = img.shape[0]
        start_row = max(0, start_row)
        end_row = min(h - 1, end_row)

        # Include end_row → use end_row + 1 because slicing is exclusive
        cropped_img = img[start_row:end_row + 1, :]

        return cropped_img

    '''
    # old one, new one is not tested if new one works delete this. New one aim to add more hdr information in final output
    def load_and_combine_cubes(self, base_dir, prefix, start_num, end_num, output_folder):
        
        def write_envi_hdr(hdr_path, lines, samples, bands, interleave, data_type, wavelengths):
            with open(hdr_path, "w") as f:
                f.write("ENVI\n")
                f.write(f"samples = {samples}\n")
                f.write(f"lines   = {lines}\n")
                f.write(f"bands   = {bands}\n")
                f.write(f"header offset = 0\n")
                f.write(f"file type = ENVI Standard\n")
                f.write(f"data type = {data_type}\n")
                f.write(f"interleave = {interleave}\n")
                f.write("byte order = 0\n")

                # Write wavelength list for Spectral
                if wavelengths is not None:
                    wl_str = ", ".join([str(w) for w in wavelengths])
                    f.write(f"wavelength = {{{wl_str}}}\n")
        
        available_folders = []

        # Scan directory and collect existing numbered folders
        for i in range(start_num, end_num + 1):
            folder_name = f"{prefix}-{i}"
            folder_path = os.path.join(base_dir, folder_name)

            if os.path.isdir(folder_path):
                available_folders.append((i, folder_path))
            else:
                print(f"Missing: {folder_name}, skipping")

        # Ensure strict ascending order
        available_folders.sort(key=lambda x: x[0])

        if not available_folders:
            print("No valid folders found.")
            return

        all_cubes = []
        meta = None

        for num, folder_path in available_folders:

            # optional: check presence of .hdr or .bil before loading
            has_cube_file = any(
                f.lower().endswith((".bil.hdr", ".bil"))
                for f in os.listdir(folder_path)
            )

            if not has_cube_file:
                print(f"No cube files found in: {folder_path}")
                continue

            print(f"Loading folder {num}: {folder_path}")

            # IMPORTANT: Load_Cube requires folder, NOT file
            cube_obj = self.Load_Cube(folder_path)
            
                
            #print("Cube object type:", type(cube_obj))
            #print("Cube attributes:", dir(cube_obj))

            # Get HDR file path
            hdr_path = cube_obj.hdr   # this is the filename only

            # Build full HDR path
            hdr_full = os.path.join(folder_path, hdr_path)
            print("HDR full path:", hdr_full)

            # Load using spectral
            img = spy.open_image(hdr_full)
            cube = img.load()              # <-- REAL DATA (lines, samples, bands)

            print("Extracted cube shape:", cube.shape)
            if meta is None:
                meta = {
                    "lines": cube.shape[0],
                    "samples": cube.shape[1],
                    "bands": cube.shape[2], 
                    "wavelengths": getattr(cube_obj, "wavelengths", None),
                    "interleave": getattr(cube_obj, "interleave", "bip"),
                    "data_type": getattr(cube_obj, "data_type", 4)  }
            all_cubes.append(cube)

            
        # -----------------------------------------------------
        # Merge vertically
        # -----------------------------------------------------
        combined_cube = np.concatenate(all_cubes, axis=0)
        print("Merged shape:", combined_cube.shape)

        # Final merged shape
        final_lines = combined_cube.shape[0]
        samples     = combined_cube.shape[1]
        bands       = combined_cube.shape[2]

        # Save output directory
        os.makedirs(output_folder, exist_ok=True)

        dat_path = os.path.join(output_folder, "combined_cube.bil")
        hdr_path = os.path.join(output_folder, "combined_cube.bil.hdr")

        # -------------------------------------
        # Save binary + hdr
        # -------------------------------------
        combined_cube.astype(np.float32).tofile(dat_path)

        write_envi_hdr(
            hdr_path,
            final_lines,
            samples,
            bands,
            meta["interleave"],
            meta["data_type"],
            meta["wavelengths"]
        )

        print(f"Saved merged cube (BIL): {dat_path}")
        print(f"Saved HDR file:         {hdr_path}")

        # Save combined cube
        #os.makedirs(output_folder, exist_ok=True)
        #out_path = os.path.join(output_folder, "combined_cube.npy")
        #np.save(out_path, combined_cube)

        #print(f"Saved: {out_path}")
    '''


    def load_and_combine_cubes(self, base_dir, prefix, start_num, end_num, output_folder):

        def parse_hdr(hdr_path):
            """Read full ENVI header into dictionary."""
            meta = {}
            with open(hdr_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                if "=" in line:
                    k, v = line.split("=", 1)
                    meta[k.strip().lower()] = v.strip()

            return meta


        def write_envi_hdr(hdr_path, meta):
            """Write full ENVI header dictionary."""
            with open(hdr_path, "w") as f:

                f.write("ENVI\n")

                # important fields first
                ordered = [
                    "samples","lines","bands",
                    "header offset","file type",
                    "data type","interleave","byte order"
                ]

                for k in ordered:
                    if k in meta:
                        f.write(f"{k} = {meta[k]}\n")

                # write remaining metadata
                for k,v in meta.items():
                    if k not in ordered:
                        f.write(f"{k} = {v}\n")


        available_folders = []

        for i in range(start_num, end_num + 1):
            folder_name = f"{prefix}-{i}"
            folder_path = os.path.join(base_dir, folder_name)

            if os.path.isdir(folder_path):
                available_folders.append((i, folder_path))
            else:
                print(f"Missing: {folder_name}, skipping")

        available_folders.sort(key=lambda x: x[0])

        if not available_folders:
            print("No valid folders found.")
            return

        all_cubes = []
        meta = None

        acquisition_times = []

        for num, folder_path in available_folders:

            print(f"Loading folder {num}: {folder_path}")

            cube_obj = self.Load_Cube(folder_path)

            hdr_full = os.path.join(folder_path, cube_obj.hdr)

            # read hdr metadata
            hdr_meta = parse_hdr(hdr_full)

            img = spy.open_image(hdr_full)
            cube = img.load()

            print("Cube shape:", cube.shape)

            # keep metadata from first cube
            if meta is None:
                meta = hdr_meta.copy()

            # collect acquisition times
            if "acquisition time" in hdr_meta:
                acquisition_times.append(hdr_meta["acquisition time"])

            all_cubes.append(cube)


        # -------------------------
        # merge cubes
        # -------------------------
        combined_cube = np.concatenate(all_cubes, axis=0)

        final_lines = combined_cube.shape[0]
        samples     = combined_cube.shape[1]
        bands       = combined_cube.shape[2]

        print("Merged shape:", combined_cube.shape)

        # -------------------------
        # update metadata
        # -------------------------
        meta["lines"] = final_lines
        meta["samples"] = samples
        meta["bands"] = bands

        # acquisition time conflict handling
        if len(acquisition_times) > 1:
            meta["acquisition time"] = f"{acquisition_times[0]} to {acquisition_times[-1]}"


        # -------------------------
        # save cube
        # -------------------------
        os.makedirs(output_folder, exist_ok=True)

        dat_path = os.path.join(output_folder, "combined_cube.bil")
        hdr_path = os.path.join(output_folder, "combined_cube.bil.hdr")

        # preserve datatype
        dtype_map = {
            "1": np.uint8,
            "2": np.int16,
            "3": np.int32,
            "4": np.float32,
            "5": np.float64,
            "12": np.uint16
        }

        dtype = dtype_map.get(meta.get("data type","4"), np.float32)

        combined_cube.astype(dtype).tofile(dat_path)

        write_envi_hdr(hdr_path, meta)

        print("Saved merged cube:", dat_path)
        print("Saved HDR:", hdr_path)


    def Convert_Mat_to_Cube(self, mat_path, out_folder=None):

        if out_folder is None:
            out_folder = os.path.dirname(mat_path)

        os.makedirs(out_folder, exist_ok=True)

        with h5py.File(mat_path, "r") as f:

            cube = np.array(f["hsi"])

            meta = {}
            if "envi_hdr" in f:
                for k, v in f["envi_hdr"].attrs.items():

                    # decode bytes if needed
                    if isinstance(v, bytes):
                        v = v.decode()

                    meta[k.lower()] = v

        lines, samples, bands = cube.shape

        dtype_code = int(meta.get("data type", 4))

        # ENVI datatype mapping
        dtype_map = {
            1: np.uint8,
            2: np.int16,
            3: np.int32,
            4: np.float32,
            5: np.float64,
            12: np.uint16
        }

        dtype = dtype_map.get(dtype_code, np.float32)

        cube = cube.astype(dtype)

        interleave = str(meta.get("interleave", "bip")).lower()

        # Convert cube layout
        if interleave == "bil":
            cube = cube.transpose(0, 2, 1)

        elif interleave == "bsq":
            cube = cube.transpose(2, 0, 1)

        base = os.path.splitext(os.path.basename(mat_path))[0]

        bil_path = os.path.join(out_folder, base + ".bil")
        hdr_path = os.path.join(out_folder, base + ".bil.hdr")

        # write raw cube
        cube.tofile(bil_path)

        # ---------- write hdr ----------
        with open(hdr_path, "w") as hdr:

            hdr.write("ENVI\n")

            # important fields first
            hdr.write(f"interleave = {interleave}\n")
            hdr.write(f"data type = {dtype_code}\n")
            hdr.write(f"lines = {lines}\n")
            hdr.write(f"samples = {samples}\n")
            hdr.write(f"bands = {bands}\n")

            # write remaining metadata
            for k, v in meta.items():

                if k in ["interleave","data type","lines","samples","bands"]:
                    continue

                # format wavelength arrays
                if k == "wavelength":

                    if isinstance(v, str):
                        hdr.write(f"{k} = {{{v}}}\n")

                    elif isinstance(v, (list, tuple, np.ndarray)):
                        values = ", ".join(map(str, v))
                        hdr.write(f"{k} = {{{values}}}\n")

                else:
                    hdr.write(f"{k} = {v}\n")

        print("Cube saved:", bil_path)
        print("HDR saved :", hdr_path)


# 01-Main_Cube_to_Mat.py
# ENVI (BIL/BIP/BSQ + .hdr) -> MATLAB .mat (v7.3/HDF5) with compression


class Mat:
    def __init__(self):
        print("Mat Object initialized") 
       

    # ---------- HDR PARSER ----------

    def parse_envi_hdr(self, hdr_path: str) -> Dict[str, Any]:
        """
        Parse ENVI .hdr file.
        Returns metadata dictionary with correct numeric types.
        """

        meta: Dict[str, Any] = {}

        with open(hdr_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Normalize lines
        lines = [ln.strip() for ln in text.replace("\r", "\n").split("\n") if ln.strip()]

        # Remove first ENVI line
        if lines and lines[0].upper() == "ENVI":
            lines = lines[1:]

        i = 0
        while i < len(lines):

            line = lines[i]

            if "=" not in line:
                i += 1
                continue

            key, val = [x.strip() for x in line.split("=", 1)]
            key = key.lower()

            # Handle multi-line lists { ... }
            if val.startswith("{") and not val.endswith("}"):
                parts = [val]
                i += 1
                while i < len(lines):
                    parts.append(lines[i])
                    if lines[i].endswith("}"):
                        break
                    i += 1
                val = " ".join(parts)

            if val.startswith("{") and val.endswith("}"):
                val = val[1:-1].strip()

            # Convert known numeric fields
            if key in [
                "samples",
                "lines",
                "bands",
                "header offset",
                "data type",
                "byte order"
            ]:
                try:
                    meta[key] = int(val)
                except ValueError:
                    meta[key] = val
            else:
                meta[key] = val

            i += 1

        return meta



    def envi_dtype_to_numpy(self, data_type: int) -> np.dtype:
        """
        ENVI 'data type' codes -> numpy dtype.
        """
        mapping = {
            1: np.uint8,
            2: np.int16,
            3: np.int32,
            4: np.float32,
            5: np.float64,
            6: np.complex64,
            9: np.complex128,
            12: np.uint16,
            13: np.uint32,
            14: np.int64,
            15: np.uint64,
        }
        if data_type not in mapping:
            raise ValueError(f"Unsupported ENVI data type code: {data_type}")
        return mapping[data_type]


    # ---------- PATH RESOLVER ----------

    def resolve_envi_pair(self, path_in: str) -> Tuple[str, str]:
        """
        Accepts either:
        - a directory containing .hdr + raw (.bil/.bip/.bsq/.dat/.img or no extension)
        - a direct path to .hdr or raw file
        Returns (raw_path, hdr_path)
        """
        path_in = os.path.abspath(path_in)

        if os.path.isdir(path_in):
            hdrs = sorted(glob.glob(os.path.join(path_in, "*.hdr")))
            if not hdrs:
                raise FileNotFoundError(f"No .hdr found in folder: {path_in}")
            hdr_path = hdrs[0]

            base = os.path.splitext(hdr_path)[0]
            candidates = [
                base + ".bil",
                base + ".bip",
                base + ".bsq",
                base + ".dat",
                base + ".img",
                base,  # sometimes raw has no extension
            ]
            for c in candidates:
                if os.path.isfile(c):
                    return c, hdr_path

            # Fallback: pick largest non-hdr file
            files = [p for p in glob.glob(os.path.join(path_in, "*")) if os.path.isfile(p)]
            files = [p for p in files if not p.lower().endswith(".hdr")]
            if files:
                files.sort(key=lambda p: os.path.getsize(p), reverse=True)
                return files[0], hdr_path

            raise FileNotFoundError(f"Found hdr but no raw cube file in: {path_in}")

        # If file input
        if path_in.lower().endswith(".hdr"):
            hdr_path = path_in
            base = os.path.splitext(hdr_path)[0]
            for c in (base + ".bil", base + ".bip", base + ".bsq", base + ".dat", base + ".img", base):
                if os.path.isfile(c):
                    return c, hdr_path
            raise FileNotFoundError(f"HDR provided but raw file not found next to it: {hdr_path}")

        # raw provided -> look for hdr
        raw_path = path_in
        base = os.path.splitext(raw_path)[0]
        hdr_path = base + ".hdr"
        if os.path.isfile(hdr_path):
            return raw_path, hdr_path

        # handle case raw like combined_cube.bil with hdr combined_cube.bil.hdr
        hdr_path2 = raw_path + ".hdr"
        if os.path.isfile(hdr_path2):
            return raw_path, hdr_path2

        raise FileNotFoundError(f"Raw file provided but .hdr not found next to it: {hdr_path} or {hdr_path2}")


    # ---------- ENVI READER (BIP/BIL/BSQ) ----------

    def read_envi_cube(self, cube, hdr_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Accepts cube data (any array-like) and header file path.
        Ensures cube is numpy array and returns (cube, meta).
        """

        if cube is None:
            raise ValueError("Cube is None")

        # Convert to numpy if needed
        if not isinstance(cube, np.ndarray):
            cube = np.asarray(cube)

        # Validate dimensions
        if cube.ndim != 3:
            raise ValueError(f"Cube must be 3D (lines, samples, bands). Got shape {cube.shape}")

        # Parse metadata from HDR
        meta = self.parse_envi_hdr(hdr_path)

        print(f"Meta data is \n\n\n {meta} \n\n\n")

        lines, samples, bands = cube.shape

        meta_lines = int(meta.get("lines", lines))
        meta_samples = int(meta.get("samples", samples))
        meta_bands = int(meta.get("bands", bands))

        if (meta_lines, meta_samples, meta_bands) != (lines, samples, bands):
            raise ValueError(
                f"Cube shape mismatch with metadata: "
                f"cube={cube.shape}, meta=({meta_lines},{meta_samples},{meta_bands})"
            )

        return cube, meta    

    # ---------- MAT v7.3 (HDF5) SAVER ----------

    def save_mat_v73(self, mat_path: str, var_name: str, cube: np.ndarray, meta: Optional[Dict[str, Any]] = None):
        """
        Save as MATLAB v7.3-compatible HDF5 .mat.
        Requires: pip install h5py
        """
        import h5py  # local import so script can still run up to this point without it

        os.makedirs(os.path.dirname(os.path.abspath(mat_path)), exist_ok=True)

        with h5py.File(mat_path, "w") as f:
            f.create_dataset(
                var_name,
                data=cube,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
                chunks=True,
            )

            if meta:
                g = f.create_group("envi_hdr")
                # store as attributes (strings)
                for k, v in meta.items():
                    try:
                        g.attrs[k] = str(v)
                    except Exception:
                        pass


    # ---------- MAIN CONVERSION CUBE TO MAT ----------

    def envi_to_mat(self, cube, out_mat: str, var_name: str = "hsi", save_meta: bool = True):
        
        #raw_path, hdr_path = self.resolve_envi_pair(path_in)

        #print("Using RAW:", raw_path)
        #print("Using HDR:", hdr_path)

        cube, meta = self.read_envi_cube(cube.cube.load(), cube.hdr_file)

        # Save large cubes safely (MAT v7.3)
        self.save_mat_v73(out_mat, var_name, cube, meta if save_meta else None)

        print("Saved:", out_mat)
        print("Cube shape (lines, samples, bands):", cube.shape)
        print("Cube dtype:", cube.dtype)




    def load_and_display_mat(self, mat_path):

        print(f"\nLoading MAT file: {mat_path}\n")

        data = {}
        meta = None

        try:
            data = scipy.io.loadmat(mat_path)
            mat_type = "MATLAB v7"

        except:
            mat_type = "MATLAB v7.3 (HDF5)"

            with h5py.File(mat_path, "r") as f:

                # load datasets
                for key in f.keys():

                    if isinstance(f[key], h5py.Dataset):
                        data[key] = np.array(f[key])

                # load metadata attributes
                if "envi_hdr" in f:
                    meta = {}

                    for k, v in f["envi_hdr"].attrs.items():
                        meta[k] = v

        print("MAT type:", mat_type)

        print("\nVariables in file:")
        for k in data.keys():
            print(" ", k)

        cube = None

        for k in data.keys():
            if isinstance(data[k], np.ndarray) and data[k].ndim == 3:
                cube = data[k]
                cube_name = k
                break

        if cube is None:
            print("\nNo 3D hyperspectral cube found.")
            return

        print(f"\nCube variable: {cube_name}")
        print("Cube shape:", cube.shape)
        print("Data type:", cube.dtype)

        lines, samples, bands = cube.shape

        print("\nCube info:")
        print("Lines   :", lines)
        print("Samples :", samples)
        print("Bands   :", bands)

        # print metadata
        if meta:
            print("\nMetadata extracted:")
            for k, v in meta.items():
                print(k, "=", v)

        # RGB preview
        if bands >= 3:

            r = cube[:, :, int(bands*0.6)]
            g = cube[:, :, int(bands*0.4)]
            b = cube[:, :, int(bands*0.2)]

            rgb = np.stack([r, g, b], axis=2)
            rgb = (rgb - rgb.min()) / (rgb.max() - rgb.min())

            plt.figure(figsize=(6,6))
            plt.imshow(rgb)
            plt.title("HSI RGB Preview")
            plt.axis("off")
            plt.show()

        print("\nFinished.\n")

    def Convert_Cube_to_Mat(self, in_path) :


        # Provide either:
        #   1) a folder that contains the .hdr and raw file, OR
        #   2) a direct path to the .hdr, OR
        #   3) a direct path to the raw file
        #in_path = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_1607202515m\Resonon\1607_S1_Row3"
        cube = Cube()
        cube.Load_Cube(in_path)

        # Resolve raw + hdr first
        #raw_path, hdr_path = self.resolve_envi_pair(in_path)

        # Output: same directory, same base name as raw (.bil/.bip/.bsq/.dat)
        out_mat = os.path.splitext(cube.bil_file)[0] + ".mat"
        print (f" out45mat = {out_mat}")

        self.envi_to_mat(cube, out_mat, var_name="hsi", save_meta=True)

# used temporarily to modify hdr file with missing informations
def update_hdr_from_reference(folder_path, reference_hdr):

    import os

    def read_hdr(path):
        meta = {}
        with open(path, "r") as f:
            lines = f.readlines()

        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip().lower()] = v.strip()

        return meta


    def write_hdr(path, meta):
        with open(path, "w") as f:

            f.write("ENVI\n")

            # preferred order
            ordered = [
                "samples",
                "lines",
                "bands",
                "header offset",
                "file type",
                "data type",
                "interleave",
                "byte order"
            ]

            for k in ordered:
                if k in meta:
                    f.write(f"{k} = {meta[k]}\n")

            for k, v in meta.items():
                if k not in ordered:
                    f.write(f"{k} = {v}\n")


    # ---------------------------------------------------
    # find hdr file in folder
    # ---------------------------------------------------
    hdr_file = None

    for f in os.listdir(folder_path):
        if f.lower().endswith(".hdr"):
            hdr_file = os.path.join(folder_path, f)
            break

    if hdr_file is None:
        print("No HDR file found in folder")
        return

    print("Target HDR:", hdr_file)
    print("Reference HDR:", reference_hdr)


    # ---------------------------------------------------
    # read both hdr files
    # ---------------------------------------------------
    target_meta = read_hdr(hdr_file)
    ref_meta = read_hdr(reference_hdr)


    # ---------------------------------------------------
    # fields we should NOT overwrite
    # ---------------------------------------------------
    protected_fields = [
        "lines",
        "samples",
        "bands",
        "header offset"
    ]


    # ---------------------------------------------------
    # copy missing metadata
    # ---------------------------------------------------
    for k, v in ref_meta.items():

        if k in protected_fields:
            continue

        if k not in target_meta:
            target_meta[k] = v


    # ---------------------------------------------------
    # write updated hdr
    # ---------------------------------------------------
    write_hdr(hdr_file, target_meta)

    print("HDR updated successfully.")