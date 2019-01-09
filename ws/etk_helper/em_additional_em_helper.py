import os
import glob


def generated_additional_ems(additional_ems_path, generated_additional_ems_path,
                             glossary_dir, inferlink_dir, working_dir, spacy_dir):
    """
    This function will read the user defined etk modules and replace any paths.

    Variables to replace:
    # ${GLOSSARY_PATH}
    # ${INFERLINK_RULES_PATH}
    # ${SPACY_RULES_PATH}
    :return:
    the ETK modules with variables replaced by

    """
    #

    for additional_em_path in glob.glob('{}/em_*.py'.format(additional_ems_path)):
        f_in = open(additional_em_path, mode='r', encoding='utf-8')
        f = f_in.read()
        f = replace_variables(f, glossary_dir, inferlink_dir, spacy_dir)
        f_out = open('{}/{}'.format(generated_additional_ems_path, os.path.basename(additional_em_path)), mode='w', encoding='utf-8')
        f_out.write(f)
        f_in.close()
        f_out.close()


def replace_variables(content, glossary_dir, inferlink_dir, spacy_dir):
    content = content.replace("${GLOSSARY_PATH}", glossary_dir)
    content = content.replace("${SPACY_RULES_PATH}", spacy_dir)
    content = content.replace("${INFERLINK_RULES_PATH}", inferlink_dir)
    return content
