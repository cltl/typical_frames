import sys
import os
sys.path.append('../../')

from typical_frames import dir_path, contrastive_analysis

output_folder = f'{dir_path}/output'
event_types = ["Q24050099","Q8065"]

contrastive_analysis(event_types=event_types,
                        output_folder=output_folder,
                        start_from_scratch=False,
                        verbose=4)
