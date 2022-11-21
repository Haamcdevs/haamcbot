import string


def html2md(content: string):
    return content.replace('\n', '')\
            .replace('<br>', "\n")\
            .replace('<b>', '**')\
            .replace('</b>', '**')\
            .replace('<i>', '*')\
            .replace('</i>', '*')
