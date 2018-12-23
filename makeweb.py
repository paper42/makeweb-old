#!/usr/bin/env python3
import os
import json
import shutil
from pathlib import Path
from collections import defaultdict

import jinja2
enabled = {}
try:
    import commonmark
    enabled['commonmark'] = True
except ImportError:
    enabled['commonmark'] = False
    print('[ERROR] commonmark module MISSING!')

source_suffixes = ['.html', '.htm', '.source', '.md']
ignore_suffixes = ['.json', '.template']

def dir_content(directory='.', relative_to='.', folders=False, recursive=True): #{{{
    """Return list of all files in directory"""
    result = []
    before_dir = Path.cwd()
    os.chdir(relative_to)
    for item in Path(directory).iterdir():

        if item.is_dir():
            if folders:
                result.append(item)
            if recursive:
                result += dir_content(directory=item, folders=folders)
        else:
            result.append(item)
    os.chdir(before_dir)
    return result
#}}}
def smart_read(filename):#{{{
    """Return content of file"""
    with open(filename, 'r', encoding='utf=8') as f:
        return f.read()
#}}}
def smart_write(filename, text):#{{{
    """Return content of file"""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w+', encoding='utf=8') as f:
        return f.write(text)
#}}}
def smart_json_loads(jsonstr, path):#{{{
    """Return dictionary from a json string"""
    try:
        return json.loads(jsonstr)
    except json.decoder.JSONDecodeError as e:
        print('exception occured in json decoding')
        print('ignoring json data')
        print(f'file:{path}')
        print(f'content: "{jsonstr}"')
        return {}
        #  raise e
#}}}
def smart_json_load(filename):#{{{
    """Return dictionary from a json file"""
    with open(filename, 'r') as f:
        return json.load(f)
#}}}
def split_by_line(txt, line):#{{{
    """Splits a string by linenumber
    returns tuple (before, after)
    destroys the line by which it was split
    """
    before = ''
    after = ''
    #  if line is None:
    #      return ('', txt)
    for linenum, linetxt in enumerate(txt.splitlines(keepends=True)):
        if linenum < line:
            before += linetxt
        elif linenum > line:
            after += linetxt
    return (before, after)
#}}}
def split_vars_content(txt):#{{{
    """Returns a tuple (vars, content)"""

    split_line = -1
    for linenum, linetxt in enumerate(txt.splitlines()):
        if linetxt == '---':
            split_line = linenum
            break

    return split_by_line(txt, split_line)
#}}}
def load_template(filename):#{{{
    path = Path('input', filename)
    mtime = os.path.getmtime(path)
    source = split_vars_content(smart_read(path))[1]
    return source, str(filename), lambda: mtime == os.path.getmtime(path)
#}}}
class Page():#{{{
    """Represents a webpage"""

    variables = {}
    def __init__(self, path):
        #  print(template)
        self.env = jinja2.Environment(
            loader=jinja2.FunctionLoader(load_template),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self.template = self.env.get_template(path)
        #  self.template = jinja2.Template(template)
        #  self.template = self.env.get_template(template)

    def render(self):
        return self.template.render(self.variables)

#}}}
def to_html(txt, txt_format):#{{{
    if txt_format == None:
        txt_format = 'html'
    if txt_format.lower() in ['html']:
        return txt
    if txt_format.lower() in ['md', 'markdown']:
        if enabled['commonmark']:
            return commonmark.commonmark(txt)
#}}}
def generate(path):#{{{
    """Return generated html or False if the page shouldn't be generated"""
    # create dict with variables for a page
    dict_vars, content = split_vars_content(smart_read(Path('input', path)))

    variables = defaultdict(lambda: None)
    variables.update(smart_json_loads(dict_vars, path))
    variables.update(smart_json_load('input/global.json'))

    content = to_html(content, variables['format'])

    if variables['render'] is False \
            or path.suffix == '.template':
        print(f'not rendering {path}')
        return False
    print(f'rendering {path}')

    # add variables to variables
    if variables['use'] not in [[], None]:
        for item in variables['use']:
            variables.update(smart_json_load(Path('input', item)))
    # add builtin variables to variables
    if variables['use_builtin'] not in [[], None]:
        for item in variables['use_builtin']:
            variables.update(smart_json_load(Path('input', item)))

    # build page - substitute variables
    page = Page(str(path))
    page.variables.update(variables)

    # write page to 'output'
    return page.render()
#}}}

Path('input').mkdir(parents=True, exist_ok=True)
Path('output').mkdir(parents=True, exist_ok=True)

for item in dir_content(directory='.', relative_to='input'):
    if item.suffix in source_suffixes:
        result = generate(item)
        # if page was generated
        if result is not False:
            smart_write(Path('output', item), result)
    elif item.suffix in ignore_suffixes:
        print(f'ignoring {item}')
    else:
        print(f'linking {item}', end='')
        try:
            Path('output', item).parent.mkdir(parents=True, exist_ok=True)
            os.link(Path('input', item), Path('output', item))
            print()
        except FileExistsError:
            print(' ... already there')
        #  print(f'copying {item}')
        #  shutil.copy(Path('input', item), Path('output', item))
# get 'input' and 'output'
#  in_path = 'test/test_content.html'
#  in_path = input('input: ')
#  out_path = input('output: ')
