![image](https://user-images.githubusercontent.com/15251768/158514568-313427fc-3d43-4e1a-a9c9-3f6c128c6422.png)
**Example Dataset:** Enhancing lesion segmentation on T1-post, lesion+edema on FLAIR, and restricted diffusion on ADC.


# Objective

The key objective of this project is to generate a large and highly curated imaging dataset of pediatric medulloblastoma patients with annotations suitable for cancer researchers and AI developers. The artifacts generated in this project will conform to the imaging and informatics standards adopted by The Cancer Imaging Archive (TCIA) and the Imaging Data Commons (IDC) initiatives and will be made available to the community. The curation and annotation protocol will be developed collaboratively by a team of clinicians, engineers, and data scientists at the National Cancer Institute, Leidos Biomedical Research, Frederick National Laboratory, and CapeStart.

# Imaging Protocol

Post-operative brain MRI scans with and without contrast (preferably within 72 hours post-surgery); for patients who undergo stereotactic biopsy only, either a pre or post-operative MRI is sufficient; for patients with M2 and M3 disease, a post-op MRI is strongly encouraged, but not mandatory

Spinal MRI imaging with and without gadolinium is required within 10 days of surgery if done preoperatively or within 28 days of surgery if done post-operatively; for posterior fossa tumors, pre-operative MRI scans are preferred

# Annotation Protocol

For each patient, every DICOM Study and DICOM Series was reviewed to identify and annotate clinically relevant time points and sequences. In a typical patient the following time points were annotated:

1. Pre-surgical study
2. Post-surgical study [if applicable]
3. Follow-up study at the completion of radiotherapy.
4. Follow-up study at the end of chemotherapy.
5. Follow-up study relapse [if applicable]

At each time point, the following items were annotated:

1. The enhancing tumor on an axial 3D T1 post contrast sequence (if not available, will use a 3D post contrast sequence in another plane. If no 3D post contrast sequence is available, the tumor was annotated in all 3 planes utilizing 2D post contrast sequences. On post-contrast sequences, the entire tumor, including the cystic and non enhancing components was annotated. Any resection cavity or post-op changes/products was excluded. 
2. The edema on an axial T2 FLAIR sequence (may use an axial T2 or other T2 weighted sequence if T2 FLAIR is not available). The segmentation mask contains both the edematous tissue and the tumor.
3. The portion of the tumor demonstrating restricted diffusion on an ADC sequence. 
4. Up to 5 metastatic lesions within the brain and and up to 5 metastatic lesions in the spine as demonstrated on whatever T1 post contrast sequence they are visualized on. When present, the 5 largest lesions were annotated.
5. A manually placed seed point (kernel) were created for each segmented structure. The seed points for each segmentation are provided in a separate DICOM RTSS file. Spinal metastases, which are too small to apply a volumetric mask to, only have a seed point annotation. 
6. SNOMED-CT “Anatomic Region Sequence” and “Segmented Property Category Code Sequence” and codes were inserted for all segmented structures. In cases where tumor spans multiple regions, multiple location codes were inserted. For example, if the tumor is centered in the parietal lobe, but also involves the frontal and temporal lobes, anatomical codes for all three locations were attached to the structure.
7. “Tracking ID” and “Tracking UID” tags will be inserted for each segmented structure to enable longitudinal lesion tracking.
8. When a time point has no findings to annotate, a “negative” (empty) annotation file for appropriate codes is provided
9. Imaging time point code was inserted to help identify each annotation in the context of the clinical trial assessment protocol. 


