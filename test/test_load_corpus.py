import sys
import os
sys.path.append('../../')

from typical_frames import dir_path, load_corpus

output_folder = f'{dir_path}/output'

load_corpus(project="test_release",
            language="en",
            output_folder=output_folder,
            verbose=2)
