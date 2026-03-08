from HSI import *
from UAV_Navigation import *

import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import cv2

DEF_MERGE_CUBE = True
DEF_IMAGE_MASKING = False



DEF_COMBINE_HSI_20250716 = False
DEF_COMBINE_HSI_20250718 = False
DEF_COMBINE_HSI_20250725 = False
DEF_COMBINE_HSI_20250730 = True


# It is used to combine different scans.
if DEF_MERGE_CUBE:
    Base_Folder = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_3007202515m\Resonon"
    Output_Folder = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_3007202515m\Resonon\S1_Row4"
    
    if DEF_COMBINE_HSI_20250716:
        prefix   = "RS_25HeritageWhtLL"  # folder prefix
    elif DEF_COMBINE_HSI_20250718:
        prefix   = "RS_25HeritageWhtLL_HSI"  # folder prefix
    elif DEF_COMBINE_HSI_20250725:
        prefix   = "RS_25HeritageWhtLL_HSI"  # folder prefix
    elif DEF_COMBINE_HSI_20250730:
        prefix   = "RS_25HeritageWhtLL_HSI"  # folder prefix


    start_num = 14
    total_files = 2
    end_num   = start_num + total_files -1  # or any upper bound
    load_and_combine_cubes(Base_Folder, prefix, start_num, end_num, Output_Folder)

#it is used to make pseudo masks
if DEF_IMAGE_MASKING:

    cube_path = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_1607202515m\Resonon\S1_Row2"
    #Mask_path = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_1607202515m\Resonon\S1_Row1\1607_S1_Row1_mask.png"
    Mask_path = os.path.join(cube_path, "\1607_S1_Row2_mask.png")

    Cube = Load_Cube(cube_path)

    Show_Centered_Freq(Cube.cube)

    #filtered_img = Show_Band_Filtered_Image(Cube.cube, band_index=50, value_min=800, value_max=7000)
    filtered_img = Show_Band_Filtered_Image(Cube.cube, band_index=55, value_min=0, value_max=6000)

    filtered_img2 = Show_Band_Filtered_Image(Cube.cube, band_index=335, value_min=0, value_max=300)
    #filtered_img2 = Show_Band_Filtered_Image(Cube.cube, band_index=442, value_min=0, value_max=300)
    
    mixed_img = filtered_img | filtered_img2

    threshold_img = threshold_by_horizontal_avg(mixed_img, 20)
    #threshold_img = threshold_by_xy_window(mixed_img, 20, 10)
    
    if False:
        cv2.imwrite(Mask_path, threshold_img.astype("uint8"))

    
    # --- 5️⃣ Show filtered binary image ---
    '''plt.figure()
    plt.imshow(filtered_img, cmap='gray')
    plt.title("Filtered Image (Band)")
    plt.axis('off')
    plt.show()'''

    fig, ax = plt.subplots(1, 4, figsize=(10, 5))

    ax[0].imshow(filtered_img, cmap='gray')
    ax[0].set_title("Filtered Image")
    ax[0].axis('off')

    ax[1].imshow(filtered_img2, cmap='gray')
    ax[1].set_title("filtered_img2 Image")
    ax[1].axis('off')
    
    ax[2].imshow(mixed_img, cmap='gray')
    ax[2].set_title("mixed_img Image")
    ax[2].axis('off')
    
    ax[3].imshow(threshold_img, cmap='gray')
    ax[3].set_title("threshold_img Image")
    ax[3].axis('off')

    plt.show()

    


    if False:
        for band_index in range(1, 478):  # inclusive of 470
            print(f"Processing band {band_index} ...")
            
            masked_img = Apply_Mask_On_Filtered_Band(
                cube=Cube.cube,
                mask=refined_mask,
                band_index=band_index,
                value_min=800,
                value_max=7000,
                out_dir=out_dir
            )
    





if False:

    cube_path = r"D:\00-Workspace(NB)\00-Workspace(UoR)\00-Data(Field)\2025\01-AAFC(Raju)\Wheat_1607202515m\Resonon\RS_25HeritageWhtLL-1"

    out_dir = os.path.join(cube_path, "Plots")

    Cube = Load_Cude(cube_path)

    Show_Centered_Freq(Cube.cube)

    #Show_Image(Cube.cube, 50, 30, 10)
    Original_Image = Show_Band_Image(Cube.cube, band_index=50, value_min=800, value_max=7000)

    filtered_img = Show_Band_Filtered_Image(Cube.cube, band_index=50, value_min=800, value_max=7000)

    #filtered_img = Extract_Rows_From_Image(filtered_img, start_row=1700, end_row=2000)

    #final_img = Filter_Black_Boxes(filtered_img, min_size=150000, max_size=1000000000000)

    final_row_filtered_img, black_counts, white_counts = Plot_Rowwise_Pixel_Counts(filtered_img)

    final_row_filtered_img2, black_counts, white_counts = Plot_Columnwise_Pixel_Counts(filtered_img)

    mapped_img, refined_mask = Map_Gray_On_Original(filtered_img, final_row_filtered_img, final_row_filtered_img2)

    boxes = Get_And_Plot_BlackBox_Coordinates(refined_mask, min_area=500)

    #print(f"Boxes are {boxes}")

    h, w = refined_mask.shape[:2]

    lines = Get_Vertical_Line_Coordinates_From_Boxes(boxes, h, x_tolerance=20)

    offsets = Compute_Row_Offsets_LeftPriority(
        lines,
        binary_img=filtered_img,
        connection_width=10,
        majority_ratio=0.5
    )

    shifted_image = Apply_Row_Offsets_To_RGB(filtered_img, offsets)


    #print("Offsets sample:", offsets)


    #centerlines = Extract_Vertical_Centerlines_Auto(refined_mask)

    #shifts_all, avg_shifts = Measure_Row_Shifts(filtered_img, mapped_img)

    #avg_shifts = Measure_Row_Shifts_Correlation_Visual(filtered_img, refined_mask, max_shift_limit=150)



    #Original_Image = Show_Band_Image(Cube.cube, band_index=50, value_min=800, value_max=7000)


    #shifted_img, left_pad, right_pad= shifted_img, left_pad, right_pad = Shift_Image_Rows_With_Buffer(filtered_img, avg_shifts)


    #h, w = shifted_img.shape[:2]
    #print(f"Image dimensions: {w} x {h} (width x height)")


    '''

    for band_index in range(1, 478):  # inclusive of 470
        print(f"Processing band {band_index} ...")
        
        masked_img = Apply_Mask_On_Filtered_Band(
            cube=Cube.cube,
            mask=refined_mask,
            band_index=band_index,
            value_min=800,
            value_max=7000,
            out_dir=out_dir
        )
        

    '''


    #'''
    import matplotlib.pyplot as plt

    # 5️⃣ Show filtered binary image ---
    plt.figure(figsize=(10, 5))

    # Subplot 1 — Filtered Image
    plt.subplot(1, 2, 1)
    plt.title("Filtered Image (Band)")
    plt.imshow(filtered_img, cmap='gray')
    plt.axis('off')

    # Subplot 2 — Refined Mask
    plt.subplot(1, 2, 2)
    plt.title("Filtered Boxes (After Area Filter)")
    plt.imshow(refined_mask, cmap='gray')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    '''
    plt.figure(1)
    plt.title("Filtered Image (Band)")
    plt.imshow(filtered_img, cmap='gray')
    plt.axis('off')

    plt.figure(2)
    plt.title("Filtered Boxes (After Area Filter)")
    plt.imshow(refined_mask, cmap='gray')
    plt.axis('off')

    '''



    '''


    plt.figure(3)
    plt.title("Filtered2 Boxes (After Area Filter)")
    plt.imshow(final_row_filtered_img2, cmap='gray')
    plt.axis('off')
    '''
    '''
    plt.figure(4)
    plt.title("Filtered2 Boxes (After Area Filter)")
    plt.imshow(shifted_img, cmap='gray')
    plt.axis('off')


    plt.figure(10)
    plt.plot(avg_shifts, color='blue')
    plt.xlabel("Row index")
    plt.ylabel("Average horizontal shift (pixels)")
    plt.title("Row-wise Average Shift Outside→Inside Mask")
    plt.grid(True, alpha=0.3)
    plt.show()



    '''



    #plt.pause(50)  # keep both open for 5 seconds (or remove for indefinite)
    plt.show(block=True)


    #Extract_Parameters_Txt(cube_path, Cube)  # Save the results to a text file
    #Extract_Parameters_Csv(cube_path, Cube)   # Save the results to a CSV file
    #Plot_Data_Index(cube_path)
    #Plot_Data_Time(cube_path)


    #Plot_Data_Difference_Index(cube_path)
    #Plot_Data_Difference_Time(cube_path)



    '''
    # My first RUNs
    # load_cube.py
    import spectral as spy

    # Path to your hyperspectral cube
    # Example: "D:/data/hyperspectral/your_file.bil" or ".img" or ".raw" with matching .hdr

    # Load the cube
    cube = spy.open_image(cube_path + ".hdr")  # must point to the .hdr file

    print("✅ Cube loaded")
    print("Cube shape (lines, samples, bands):", cube.shape)
    print("Wavelengths:", cube.bands.centers[:10], "...")  # show first 10 wavelengths

    # Access pixel [row, col, :]
    spectrum = cube[100, 200]   # spectrum at pixel (100,200)
    print("Pixel spectrum length:", len(spectrum))

    # Show a quick RGB visualization (using 3 bands)
    spy.imshow(cube, (50, 30, 10))  # example: bands 50=R,30=G,10=B
    '''

#    *******************************From Main Nisar*****************************************************
