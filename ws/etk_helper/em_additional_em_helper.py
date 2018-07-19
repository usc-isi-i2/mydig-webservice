import os
import glob


def generated_additional_ems(additional_ems_path, generated_additional_ems_path,
                             glossary_dir, inferlink_dir, working_dir, spacy_dir):
    """
    This function will read the user defined etk modules and replace any paths.
    :return:


    """
    # Variables to replace:
    # ${GLOSSARY_PATH}

    for additional_em_path in glob.glob('{}/em_*.py'.format(additional_ems_path)):
        f_in = open(additional_em_path)
        f = f_in.read()
        f = replace_variables(f, glossary_dir)
        f_out = open('{}/{}'.format(generated_additional_ems_path, os.path.basename(additional_em_path)), 'w')
        f_out.write(f)
        f_in.close()
        f_out.close()


def replace_variables(content, glossary_dir):
    return content.replace("${GLOSSARY_PATH}", glossary_dir)
