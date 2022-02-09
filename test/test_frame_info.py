import sys
import os
sys.path.append('../../')

from typical_frames import dir_path, frame_info

path = f'{dir_path}/test/input_files/Canberra disappears in the dust.naf'

frame_info_dict = frame_info(naf_root=path,
                                verbose=2)
