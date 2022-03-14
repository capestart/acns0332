"""Collection of methods for processing annotations files created in XNAT/OHIF
radiology viewer."""

import glob
import os
import shutil

import numpy as np
import parse
import pydicom
from pydicom.tag import Tag
from pydicom import Sequence, DataElement


def prepare_annotations(data_path):
    shutil.rmtree(f'{data_path}/Annotations', ignore_errors=True)
    os.makedirs(f'{data_path}/Annotations', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/1-Pre-Operative', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/2-Post-Operative', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/3-Post-Radiation', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/4-Post-Chemotherapy', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/5-Recurrence', exist_ok=True)
    os.makedirs(f'{data_path}/Annotations/Negative', exist_ok=True)

    rtss_files = glob.glob(f'{data_path}/**/AIM*.dcm', recursive=True)
    for file in rtss_files:
        ds = pydicom.dcmread(file)
        if ds.StructureSetLabel.lstrip().startswith('Neg'):
            shutil.copy(file, f'{data_path}/Annotations/Negative/')
        elif ds.StructureSetLabel.lstrip().startswith('1'):
            shutil.copy(file, f'{data_path}/Annotations/1-Pre-Operative/')
        elif ds.StructureSetLabel.lstrip().startswith('2'):
            shutil.copy(file, f'{data_path}/Annotations/2-Post-Operative/')
        elif ds.StructureSetLabel.lstrip().startswith('3'):
            shutil.copy(file, f'{data_path}/Annotations/3-Post-Radiation/')
        elif ds.StructureSetLabel.lstrip().startswith('4'):
            shutil.copy(file, f'{data_path}/Annotations/4-Post-Chemotherapy/')
        elif ds.StructureSetLabel.lstrip().startswith('5'):
            shutil.copy(file, f'{data_path}/Annotations/5-Recurrence/')
        else:
            print(
                f'Warning: Unmatched file: {file}, Label: {ds.StructureSetLabel}'
            )

    seg_files = glob.glob(f'{data_path}/**/SEG*.dcm', recursive=True)
    for file in seg_files:
        ds = pydicom.dcmread(file)
        if ds.SeriesDescription.lstrip().startswith('Neg'):
            shutil.copy(file, f'{data_path}/Annotations/Negative/')
        elif ds.SeriesDescription.lstrip().startswith('1'):
            shutil.copy(file, f'{data_path}/Annotations/1-Pre-Operative/')
        elif ds.SeriesDescription.lstrip().startswith('2'):
            shutil.copy(file, f'{data_path}/Annotations/2-Post-Operative/')
        elif ds.SeriesDescription.lstrip().startswith('3'):
            shutil.copy(file, f'{data_path}/Annotations/3-Post-Radiation/')
        elif ds.SeriesDescription.lstrip().startswith('4'):
            shutil.copy(file, f'{data_path}/Annotations/4-Post-Chemotherapy/')
        elif ds.SeriesDescription.lstrip().startswith('5'):
            shutil.copy(file, f'{data_path}/Annotations/5-Recurrence/')
        else:
            print(
                f'Warning: Unmatched file: {file}, Description: {ds.SeriesDescription}'
            )

    # ds = pydicom.dcmread(files[0])
    # print('Input SeriesDescription: ', ds.SeriesDescription)
    # ds.StructureSetLabel


def process_timepoint(data_path, timepoint, patient_name, patient_age,
                      patient_sex):

    data_path = data_path + '/Annotations/'

    if timepoint == 1:
        study_description = 'Pre-operative'
        data_path = os.path.join(data_path, '1-Pre-Operative')
    elif timepoint == 2:
        study_description = 'Post-operative'
        data_path = os.path.join(data_path, '2-Post-Operative')
    elif timepoint == 3:
        study_description = 'Post-radiation'
        data_path = os.path.join(data_path, '3-Post-Radiation')
    elif timepoint == 4:
        study_description = 'Post-chemotherapy'
        data_path = os.path.join(data_path, '4-Post-Chemotherapy')
    elif timepoint >= 5:
        study_description = 'Recurrence'
        data_path = os.path.join(data_path, '5-Recurrence')
    else:
        print('ERROR: No suitable timepoint specified.')

    if os.path.isdir(data_path):
        print(study_description + ' FOUND')
        files = glob.glob(os.path.join(data_path, 'SEG*[!modified].dcm'))
        files_rtss = glob.glob(os.path.join(data_path, 'AIM*[!modified].dcm'))
        files = sort_files_by_series_number(files)
        files_rtss = sort_files_by_series_number(files_rtss)

        for file, file_rtss in zip(files, files_rtss):
            print('Processing SEG file: ', file)
            print('Processing RTSS file: ', file_rtss)
            series_number_seg = int(parse.parse('{}_S{}.dcm', file)[1])
            series_number_rtss = int(parse.parse('{}_S{}.dcm', file_rtss)[1])
            if series_number_seg != series_number_rtss:
                print('ERROR: series numbers do not match.')
                break

            roi_name = get_roi_name(file)
            print('DETECTED ROI NAME: ', roi_name)
            process_dicom_seg(file, study_description, roi_name)
            process_dicom_rtss(file_rtss, study_description, roi_name, file,
                               patient_name, patient_age, patient_sex)
    else:
        print(study_description + ' NOT FOUND')


def process_dicom_seg(fname_in, study_description, roi_name):
    # PROCESS DICOM SEG OBJECT
    # fname_out = fname_in[:-4] + '_modified.dcm'
    fname_out = fname_in
    ds = pydicom.dcmread(fname_in)
    print('Input SeriesDescription: ', ds.SeriesDescription)
    print('PatientName: ', ds.PatientName)
    print('PatientAge: ', ds.PatientAge)
    print('PatientSex: ', ds.PatientSex)

    # Fix various issues
    ds.PatientID = str(ds.PatientName)
    ds.SeriesNumber = int(parse.parse('{}_S{}.dcm', fname_in)[1])

    ds.StudyID = ''
    ds.add(DataElement(Tag(0x0013, 0x0010), 'LO', 'CTP'))
    ds.add(DataElement(Tag(0x0013, 0x1010), 'LO', 'ACNS0332'))
    ds.add(DataElement(Tag(0x0013, 0x1013), 'LO', ds.StudyDate))
    if len(roi_name) > 0:
        ds.SegmentSequence[0].SegmentLabel = roi_name

    # Add series description (pre-op, post-op, follow-up, etc.)
    # Note: do not alter StudyDescription per guidance from David Clunie
    new_series_description = study_description + ', ' + ds.SeriesDescription
    ds.SeriesDescription = new_series_description[:64]
    ds.ClinicalTrialTimePointID = study_description

    # Add SNOMED-CT codes
    ds = add_coding_scheme_id(ds)
    ds = add_segmentation_code(ds)
    ds = add_tracking_id(ds)
    ds = add_acquisition_context_sequence(ds, study_description)

    # Remove noncompliant tags created by OHIF
    ds = remove_attribute(ds, 'ROIDisplayColor')
    ds = remove_attribute(ds, 'StructureSetDate')
    ds = remove_attribute(ds, 'StructureSetLabel')
    ds = remove_attribute(ds, 'ReferencedSegmentNumber')
    ds = remove_attribute(ds, 'ReferencedFrameNumber')

    # Remove ROI Color (Contour concept, not DICOM SEG)
    ds.SegmentSequence[0] = remove_attribute(ds.SegmentSequence[0],
                                             'RecommendedDisplayCIELabValue')

    print('Output SeriesDescription: ', ds.SeriesDescription)
    print(ds.SegmentSequence[0])
    ds.save_as(fname_out)
    print('Saved file ', fname_out)


def process_dicom_rtss(fname_in,
                       study_description,
                       roi_name,
                       fname_in_seg,
                       patient_name,
                       patient_age,
                       patient_sex,
                       ref_file_is_seg=True):
    # fname_out = fname_in[:-4] + '_modified.dcm'
    fname_out = fname_in
    structure_set_label = 'Seed Point'
    ds = pydicom.dcmread(fname_in)

    # Remove all other structures beside seed points
    remove_indices = []
    for i, structure in enumerate(ds.StructureSetROISequence):
        if 'seed' not in structure.ROIName.lower():
            remove_indices.append(i)
    for i in reversed(remove_indices):
        print('Removing ROI: ', ds.StructureSetROISequence[i].ROIName)
        ds.StructureSetROISequence.pop(i)
        ds.ROIContourSequence.pop(i)
        ds.RTROIObservationsSequence.pop(i)

    # Copy over relevant codes from DICOM SEG file
    if ref_file_is_seg:
        # fname_in_seg = fname_in_seg[:-4] + '_modified.dcm'
        seg = pydicom.dcmread(fname_in_seg)
        ds.SeriesDescription = seg.SeriesDescription
    else:
        seg = pydicom.dcmread(fname_in_seg)
        new_series_description = study_description + ', ' + roi_name
        ds.SeriesDescription = new_series_description[:64]
    ds.StudyTime = seg.StudyTime

    # TODO: The following 3 are problematic if more than 1 SEG file per time pt
    # ds.RTROIObservationsSequence[
    #     0].AnatomicRegionSequence = seg.SegmentSequence[
    #         0].AnatomicRegionSequence
    # ds.RTROIObservationsSequence[
    #     0].SegmentedPropertyCategoryCodeSequence = seg.SegmentSequence[
    #         0].SegmentedPropertyCategoryCodeSequence
    # ds.RTROIObservationsSequence[
    #     0].RTROIIdentificationCodeSequence = seg.SegmentSequence[
    #         0].SegmentedPropertyTypeCodeSequence
    # Fix patient age
    if ('PatientAge' not in ds) or len(ds.PatientAge) == 0:
        if ('PatientAge' in seg) and len(seg.PatientAge) > 0:
            ds.PatientAge = seg.PatientAge
        else:
            ds.PatientAge = patient_age

    # Fix various issues
    ds.PatientName = patient_name
    ds.PatientID = patient_name
    ds.PatientSex = patient_sex
    # ds.SeriesDescription = ds.StructureSetROISequence[0].ROIName

    for i in range(0, len(ds.RTROIObservationsSequence)):
        if 'seed' in ds.StructureSetROISequence[i].ROIName.lower():
            full_roi_name = ds.StructureSetROISequence[i].ROIName
        else:
            full_roi_name = ds.StructureSetROISequence[
                i].ROIName + ' Seed Point'
        ds.RTROIObservationsSequence[i].ROIObservationLabel = full_roi_name
        ds.StructureSetROISequence[i].ROINumber = i + 1
        ds.StructureSetROISequence[i].ROIName = full_roi_name
        ds.StructureSetROISequence[i].ROIGenerationAlgorithm = 'MANUAL'
        ds.RTROIObservationsSequence[i].ObservationNumber = i + 1
        ds.RTROIObservationsSequence[i].ReferencedROINumber = i + 1

        # Convert to POINT representation
        ds.ROIContourSequence[i].ContourSequence[
            0].ContourGeometricType = 'POINT'
        pts = ds.ROIContourSequence[i].ContourSequence[0].ContourData
        if len(pts) > 6:
            print('ERROR: More than 6 values in seed point ContourData.')
        ds.ROIContourSequence[i].ContourSequence[0].ContourData = [
            (pts[0] + pts[3]) / 2, (pts[1] + pts[4]) / 2, (pts[2] + pts[5]) / 2
        ]
        ds.ROIContourSequence[i].ContourSequence[0].NumberOfContourPoints = 1
        ds.ROIContourSequence[i].ReferencedROINumber = i + 1
        ds.ROIContourSequence[i].ROIDisplayColor = [255, 255, 0]  # yellow

        # Add SNOMED-CT code
        ds = add_segmentation_code(ds, segment_sequence=i, is_dcm_seg=False)

        # Remove referenced frame number
        ds.ROIContourSequence[i].ContourSequence[0].ContourImageSequence[
            0] = remove_attribute(
                ds.ROIContourSequence[i].ContourSequence[0].
                ContourImageSequence[0], 'ReferencedFrameNumber')

    ds.StructureSetLabel = structure_set_label
    ds.SeriesNumber = int(parse.parse('{}_S{}.dcm', fname_in)[1])
    ds.SeriesDate = ds.StructureSetDate
    ds.StudyID = ''
    ds.add(DataElement(Tag(0x0013, 0x0010), 'LO', 'CTP'))
    ds.add(DataElement(Tag(0x0013, 0x1010), 'LO', 'ACNS0332'))
    ds.add(DataElement(Tag(0x0013, 0x1013), 'LO', ds.StudyDate))

    # # Add series description (pre-op, post-op, follow-up, etc.)
    # # Note: do not alter StudyDescription per guidance from David Clunie
    # new_series_description = study_description + ', ' + ds.SeriesDescription
    # ds.SeriesDescription = new_series_description[:64]
    ds.ClinicalTrialTimePointID = study_description

    # Add codes
    ds = add_coding_scheme_id(ds)
    ds = add_acquisition_context_sequence(ds, study_description)

    print(ds.ROIContourSequence[0])
    print(ds.StructureSetROISequence[0])
    ds.save_as(fname_out)
    print(ds)


def add_coding_scheme_id(ds):
    # Define DCM Code template
    sct_elements = [
        DataElement(Tag(0x0008, 0x0102), 'SH',
                    'DCM'),  # set "Coding Scheme Designator"
        DataElement(Tag(0x0008, 0x010C), 'UI',
                    '1.2.840.10008.2.16.4'),  # set "Coding Scheme UID"
        DataElement(
            Tag(0x0008, 0x0115), 'ST',
            'DICOM Controlled Terminology'),  # set "Coding Scheme Name"
        DataElement(Tag(0x0008, 0x0116), 'ST',
                    'DICOM'),  # set "Coding Scheme Responsible Organization"
    ]
    ds1 = pydicom.Dataset()
    for element in sct_elements:
        ds1.add(element)

    # Define SNOMED-CT Code template
    sct_elements = [
        DataElement(Tag(0x0008, 0x0102), 'SH',
                    'SCT'),  # set "Coding Scheme Designator"
        DataElement(Tag(0x0008, 0x010C), 'UI',
                    '2.16.840.1.113883.6.96'),  # set "Coding Scheme UID"
        DataElement(Tag(0x0008, 0x0115), 'ST',
                    'SNOMED CT'),  # set "Coding Scheme Name"
        DataElement(Tag(0x0008, 0x0116), 'ST', 'SNOMED International'
                    ),  # set "Coding Scheme Responsible Organization"
    ]
    ds2 = pydicom.Dataset()
    for element in sct_elements:
        ds2.add(element)

    # Define NCIt Code template
    ncit_elements = [
        DataElement(Tag(0x0008, 0x0102), 'SH',
                    'NCIt'),  # set "Coding Scheme Designator"
        DataElement(Tag(0x0008, 0x010C), 'UI',
                    '2.16.840.1.113883.3.26.1.1'),  # set "Coding Scheme UID"
        DataElement(Tag(0x0008, 0x0115), 'ST',
                    'NCI Thesaurus'),  # set "Coding Scheme Name"
        DataElement(Tag(0x0008, 0x0116), 'ST',
                    'NCI'),  # set "Coding Scheme Responsible Organization"
    ]
    ds3 = pydicom.Dataset()
    for element in ncit_elements:
        ds3.add(element)

    ds.CodingSchemeIdentificationSequence = Sequence([ds1, ds2, ds3])
    return ds


def add_acquisition_context_sequence(ds, study_description):

    # Define SCT codes for time points
    ds1_elements = [DataElement(Tag(0x0040, 0xA040), 'CS', 'CODE')]
    ds1 = pydicom.Dataset()
    for element in ds1_elements:
        ds1.add(element)
    ds.AcquisitionContextSequence = Sequence([ds1])

    # Define Concept Name Code Sequence
    ds2_elements = [
        DataElement(Tag(0x0008, 0x0100), 'SH', '126072'),
        DataElement(Tag(0x0008, 0x0102), 'SH', 'DCM'),
        DataElement(Tag(0x0008, 0x0104), 'LO', 'Time Point Type')
    ]
    ds2 = pydicom.Dataset()
    for element in ds2_elements:
        ds2.add(element)
    ds.AcquisitionContextSequence[0].ConceptNameCodeSequence = Sequence([ds2])

    # Define Concept Code Sequence
    if study_description == 'Pre-operative':
        ds3_elements = [
            DataElement(Tag(0x0008, 0x0100), 'SH', '262068006'),
            DataElement(Tag(0x0008, 0x0102), 'SH', 'SCT'),
            DataElement(Tag(0x0008, 0x0104), 'LO', 'Pre-operative')
        ]
    elif study_description == 'Post-operative':
        ds3_elements = [
            DataElement(Tag(0x0008, 0x0100), 'SH', '262061000'),
            DataElement(Tag(0x0008, 0x0102), 'SH', 'SCT'),
            DataElement(Tag(0x0008, 0x0104), 'LO', 'Post-operative')
        ]
    elif study_description == 'Post-radiation':
        ds3_elements = [
            DataElement(Tag(0x0008, 0x0100), 'SH', '264908009'),
            DataElement(Tag(0x0008, 0x0102), 'SH', 'SCT'),
            DataElement(Tag(0x0008, 0x0104), 'LO', 'Post-radiation')
        ]
    elif study_description == 'Post-chemotherapy':
        ds3_elements = [
            DataElement(Tag(0x0008, 0x0100), 'SH', '262502001'),
            DataElement(Tag(0x0008, 0x0102), 'SH', 'SCT'),
            DataElement(Tag(0x0008, 0x0104), 'LO', 'Post-chemotherapy')
        ]
    elif study_description == 'Recurrence':
        ds3_elements = [
            DataElement(Tag(0x0008, 0x0100), 'SH', '25173007'),
            DataElement(Tag(0x0008, 0x0102), 'SH', 'SCT'),
            DataElement(Tag(0x0008, 0x0104), 'LO', 'Recurrent tumor (finding)')
        ]
    ds3 = pydicom.Dataset()
    for element in ds3_elements:
        ds3.add(element)
    ds.AcquisitionContextSequence[0].ConceptCodeSequence = Sequence([ds3])
    print(ds.AcquisitionContextSequence[0])

    return ds


def generate_code(code, meaning, scheme='SCT'):
    de = [
        DataElement(Tag(0x0008, 0x0102), 'SH',
                    scheme),  # set "Coding Scheme Designator"
        DataElement(Tag(0x0008, 0x0100), 'SH', code),  # set "Code Value"
        DataElement(Tag(0x0008, 0x0104), 'LO', meaning),  # set "Code Meaning"
    ]
    ds = pydicom.Dataset()
    for element in de:
        ds.add(element)
    return ds


def get_roi_name(ds):

    if os.path.isfile(str(ds)):
        ds = pydicom.dcmread(ds)

    roi_name = None
    if ('edema' in ds.SeriesDescription.lower()) or (
            'flair' in ds.SeriesDescription.lower()):
        roi_name = 'Edema'
    elif 'post' in ds.SeriesDescription.lower():
        roi_name = 'Enhancing Lesion'
    elif ('adc' in ds.SeriesDescription.lower()) or (
            'diff' in ds.SeriesDescription.lower()):
        roi_name = 'Restricted Diffusion'
    elif ('spine' in ds.SeriesDescription.lower()) or (
            'spinal' in ds.SeriesDescription.lower()):
        roi_name = 'Spine Met'
    else:
        print('ERROR: No ROI Name detected.')

    return roi_name


def add_segmentation_code(ds, segment_sequence=0, is_dcm_seg=True):

    print('SeriesDescription: ', ds.SeriesDescription)
    if is_dcm_seg:
        print('SegmentSequence[0].SegmentLabel: ',
              ds.SegmentSequence[0].SegmentLabel)

    segmentation_category = generate_code(
        '49755003', 'Morphologically Abnormal Structure')

    segmentation_code = []
    roi_name = get_roi_name(ds)
    if 'edema' in roi_name.lower():
        segmentation_code = generate_code('79654002', 'Edema')
    elif 'enhancing' in roi_name.lower():
        segmentation_code = generate_code('C113842',
                                          'Enhancing Lesion',
                                          scheme='NCIt')
    elif 'restricted' in roi_name.lower():
        segmentation_code = generate_code('C81175',
                                          'Non-Enhancing Lesion',
                                          scheme='NCIt')
    elif 'met' in roi_name.lower():
        segmentation_code = generate_code('14799000',
                                          'Neoplasm, Secondary',
                                          scheme='SCT')
    else:
        print('ERROR: No matching ROI name found for segmentation code.')

    #TODO: Implement the following segmentation structure types: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7159.html

    print('segmentation_code: ', segmentation_code)
    print('roi_name: ', roi_name)
    if is_dcm_seg and len(roi_name) > 0:
        ds.SegmentSequence[segment_sequence].SegmentLabel = roi_name

    regions = []
    if 'left' in ds.SeriesDescription.lower():
        if 'temporal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('52718009', 'Left temporal lobe structure'))
        if 'frontal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('74298007', 'Left frontal lobe structure'))
        if 'parietal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('9003000', 'Left parietal lobe structure'))
        if 'occipital' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('32373000', 'Left occipital lobe structure'))

    if 'right' in ds.SeriesDescription.lower():
        if 'temporal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('78029007', 'Right temporal lobe structure'))
        if 'frontal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('15046008', 'Right frontal lobe structure'))
        if 'parietal' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('47876008', 'Right parietal lobe structure'))
        if 'occipital' in ds.SeriesDescription.lower():
            regions.append(
                generate_code('59144001', 'Right occipital lobe structure'))

    if 'ganglia' in ds.SeriesDescription.lower():
        regions.append(generate_code('32610002', 'Basal ganglion structure'))

    if 'pineal' in ds.SeriesDescription.lower():
        regions.append(generate_code('45793000', 'Pineal gland'))

    if 'chiasm' in ds.SeriesDescription.lower():
        regions.append(generate_code('244453006', 'Optic chiasm'))

    if 'spine' in ds.SeriesDescription.lower():
        regions.append(generate_code('2748008', 'Spinal cord'))

    #TODO: Add all anatomic regions per: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7153.html

    if is_dcm_seg:  # DICOM SEG object
        ds.SegmentSequence[
            segment_sequence].SegmentedPropertyCategoryCodeSequence = Sequence(
                [segmentation_category])
        ds.SegmentSequence[
            segment_sequence].SegmentedPropertyTypeCodeSequence = Sequence(
                [segmentation_code])
        ds.SegmentSequence[segment_sequence].AnatomicRegionSequence = Sequence(
            regions)
    else:  # DICOM RTSS object
        ds.RTROIObservationsSequence[
            segment_sequence].SegmentedPropertyCategoryCodeSequence = Sequence(
                [segmentation_category])
        ds.RTROIObservationsSequence[
            segment_sequence].RTROIIdentificationCodeSequence = Sequence(
                [segmentation_code])
        ds.RTROIObservationsSequence[
            segment_sequence].AnatomicRegionSequence = Sequence(regions)

    return ds


def add_tracking_id(ds, segment_sequence=0):

    #TODO: Add code to handle multiple lesions or mets (each needs unique
    # tracking UID)
    roi_name = get_roi_name(ds)

    if 'edema' in roi_name.lower():
        ds.SegmentSequence[segment_sequence].TrackingID = 'Edema'
        ds.SegmentSequence[
            segment_sequence].TrackingUID = '2.25.282254060485931654441677076302135519352'
    elif 'enhancing' in roi_name.lower():
        ds.SegmentSequence[segment_sequence].TrackingID = 'Enhancing_Lesion'
        ds.SegmentSequence[
            segment_sequence].TrackingUID = '2.25.191465688770867204140652933651558585028'
    elif 'restricted' in roi_name.lower():
        ds.SegmentSequence[
            segment_sequence].TrackingID = 'Restricted_Diffusion'
        ds.SegmentSequence[
            segment_sequence].TrackingUID = '2.25.244304104175290246376252700917730902179'
    elif 'spine' in roi_name.lower():
        ds.SegmentSequence[segment_sequence].TrackingID = 'Spine_Met'
        ds.SegmentSequence[
            segment_sequence].TrackingUID = '2.25.121541891310895770373655103598854335335'
        # UIDs generated by:
        # pydicom.uid.generate_uid(prefix=None)
    else:
        print(
            'ERROR: Tracking UID generation failed. No matching structures found.'
        )
    return ds


def remove_attribute(ds, attribute):
    if attribute in ds:
        del ds[attribute]
    return ds


def sort_files_by_series_number(files):
    series_number_list = []
    for file in files:
        series_number_list.append(int(parse.parse('{}_S{}.dcm', file)[1]))
    ti = np.argsort(np.array(series_number_list))
    files = [files[i] for i in ti]

    return files
