import process_annotations

patient_id = input('Enter directory of the current user to process \n')
patient_age = input('Enter patient age ( 015Y ) \n')
patient_sex = input('patient sex M/F \n')

base_path = patient_id + '/'
patient_name = 'ACNS0332_' + patient_id

process_annotations.prepare_annotations(base_path)

process_annotations.process_timepoint(base_path, 1, patient_name, patient_age, patient_sex)
process_annotations.process_timepoint(base_path, 2, patient_name, patient_age, patient_sex)
process_annotations.process_timepoint(base_path, 3, patient_name, patient_age, patient_sex)
process_annotations.process_timepoint(base_path, 4, patient_name, patient_age, patient_sex)
process_annotations.process_timepoint(base_path, 5, patient_name, patient_age, patient_sex)