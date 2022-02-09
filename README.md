### Typical Frame Analysis
This package provides functions that extract linguistic information from a corpus of reference texts categorized into event types. One can apply an FF*ICF metric on the frames between the event types in order to derive a typicality score for each frame per event type, ranging between 0-1. The scores are exported to both an excel file and a json dictionary. The latter can be used to update the typicality scores in the DFNDataReleases package.

This package was built and used for the purpose of the paper Variation in framing as a function of temporal reporting distance; Remijnse et al. 2021.

### Prerequisites
Python 3.7.4 was used to create this package. It might work with older versions of Python.

### Installing

# Resources
The DFNDataReleases package needs to be cloned. This can be done calling:
```bash
bash install.sh
```

# Python modules
A number of external modules need to be installed, which are listed in **requirements.txt**.
Use the following command:
```bash
pip install -r requirements.txt
```

### Usage
This package comes with different main functions:

# Frame information from a file
The function frame_info() extracts the following linguistic information from a NAF iterable. You can run the function on an example file with the following command:

```python
from HDD_analysis import frame_info, dir_path

frame_info(naf_root=f"{dir_path}/test/input_files/Canberra disappears in the dust.naf"
            verbose=0)
```
The following parameters are specified:
* **naf_root** the path to a NAF file
* **verbose**: 2: print the extracted information
When running this function in python, the output will be printed in your terminal.

# load corpus
The function load_corpus() loads the corpus from DFNDataReleases and distributes the texts and their extracted linguistic information over event types. texts with less than 10 annotated frames in the SRL layer are ignored. You can run the function with the following command:

```python
from typical_frames import dir_path, load_corpus

load_corpus(project="test_release",
            language="en",
            output_folder=f"{dir_path}/output",
            verbose=2)
```
The following parameters are specified:
* **project** the project under which the corpus is organized in DFNDataReleases
* **language** the language of the texts you want to load
* **output_folder** the folder where the extracted and reorganized information is written to
* **verbose**
When running this function, the loaded, processed and reorganized corpus is written to the output folder.

# Contrastive analysis
The function contrastive_analysis() opens the previously loaded corpus from the output folder, performs a contrastive analysis and writes the output to different formats. You can run the function with the following command:

```python
from typical_frames import dir_path, contrastive_analysis

event_types = ["Q24050099","Q8065"]

contrastive_analysis(event_types=event_types,
                        output_folder=f"{dir_path}/output",
                        start_from_scratch=False,
                        verbose=4)
```
The following parameters are specified:
* **event_types** a list of specified event type identifiers. If this list is not specified, the function will perform FF*ICF between all event types in the corpus.
* **output_folder** output folder
* **start_from_scratch** boolean that indicates whether previous output should be overwritten
* **verbose**

When running this function, the output of the contrastive analysis is written to 1) an excel file with a ranking of the annotated frames per event type, based on their FF*ICF scores. Frequency distributions are provided as well. 2) a json file per event type with a dictionary displaying {frame:typicality_score}. This can be used to update the typicality scores in DFNDataReleases.

### Authors
* **Levi Remijnse** (l.remijnse@vu.nl)

### License
This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details
