from __future__ import (division, absolute_import, print_function, unicode_literals)
import sys, os, tempfile, logging, time
import requests, json, argparse

if sys.version_info >= (3,):
    import urllib.request as urllib2
    import urllib.parse as urlparse
else:
    import urllib2
    import urlparse

CONTENT_TYPE = os.getenv('CONTENT_TYPE', 'application/json')
ACCEPT = os.getenv('ACCEPT', 'application/json')
AUTHORIZATION = os.environ['AUTHORIZATION']
PROJECT_KEY = os.environ['PROJECT_KEY']
PROJECT_URL = 'https://api.localizejs.com/v2.0/projects/' + PROJECT_KEY

try:
    parser = argparse.ArgumentParser(description='Calls localisejs and translates.', add_help=True,
                                     epilog='Example of use')
    parser.add_argument('--operation', type=str, help='task to be performed', default=False,
                        dest="task")
    parser.add_argument('--phraseFile', type=argparse.FileType('r'), help='file name containing text', default=False,
                        dest="filename")
    parser.add_argument('--downloadFormat', type=str, help='type of file to downlaod', default=False,
                        dest="filetype")
    parser.add_argument('--language', type=str, help='which language file to download', default=False,
                        dest="language")
    parser.add_argument('--state', type=str, help='state of phrase', default=False,
                        dest="state")
    args = parser.parse_args()
except ImportError:
    flags = None


class LocalisejsUtil:
    @staticmethod
    def get_headers():
        return {'Content-Type': CONTENT_TYPE, 'Accept': ACCEPT, 'Authorization': AUTHORIZATION}

    @staticmethod
    def get_stat_url():
        return 'https://api.localizejs.com/v2.0/projects/' + PROJECT_KEY + '/stats'

    @staticmethod
    def get_url(action, parameters):
        url = PROJECT_URL + '/' + action
        if parameters is not None and isinstance(parameters, dict):
            url = PROJECT_URL + '/' + action + '?' + urlparse.urlencode(parameters)
        else:
            url = PROJECT_URL + '/' + action
        return url

    @staticmethod
    def get_translation_url():
        return 'https://api.localizejs.com/v2.0/projects/' + PROJECT_KEY + '/phrases'

    @staticmethod
    def get_resource_url(file_format, lnguage):
        resource_url = 'https://api.localizejs.com/v2.0/projects/' + PROJECT_KEY + '/resources'
        arg_string = 'format=' + file_format.upper() + '&language=' + lnguage.lower() + \
                     '&filter=has-active-translations'
        return resource_url + '?' + arg_string

    @staticmethod
    def read_file():
        text = []
        try:
            if args.filename is not None:
                with args.filename as data:
                    for each_line in data:
                        try:
                            text.append(dict(phrase=each_line.rstrip('\n')))
                        except ValueError:
                            pass
            else:
                print('Oh well ; No args, no problems')
        except:
            pass
        return text

    @staticmethod
    def download_specs(file_format, lnguage):
        return {'format': file_format, 'language': lnguage, 'filter': 'has-active-translations'}

    @staticmethod
    def push_for_translation():
        headers = LocalisejsUtil.get_headers()
        translation_url = LocalisejsUtil.get_translation_url()
        translation_response = requests.post(translation_url, data=json.dumps(dict(phrases=LocalisejsUtil.read_file())),
                                             headers=headers)
        print(translation_response)

    @staticmethod
    def add_headers(request, headers):
        for key, value in headers.items():
            request.add_header(key, value)
        return request

    @staticmethod
    def download_translation():
        file_type = ""
        language = ""
        try:
            if args.filetype is not None and args.language is not None:
                file_type = args.filetype
                language = args.language
            else:
                print('Oh well ; No args, no problems')
                raise
        except:
            pass
        resource_url = LocalisejsUtil.get_resource_url(file_type, language)
        req = LocalisejsUtil.add_headers(urllib2.Request(resource_url), LocalisejsUtil.get_headers())
        u = urllib2.urlopen(req)

        dest = None
        scheme, netloc, path, query, fragment = urlparse.urlsplit(resource_url)
        now = time.strftime("%d-%m-%Y") + '##' + time.strftime("%H%M%S")
        filename = 'localize-' + language + '-phrases-' + now + '.' + file_type.lower()
        if not filename:
            filename = 'downloaded.file'
        if dest:
            filename = os.path.join(dest, filename)
        with open(filename, 'wb') as f:
            meta = u.info()
            meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
            meta_length = meta_func("Content-Length")
            file_size = None
            if meta_length:
                file_size = int(meta_length[0])
            print("Downloading: {0} Bytes: {1}".format(resource_url, file_size))
            os.system('cls')
            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
                file_size_dl += len(buffer)
                f.write(buffer)
                status = "{0:16}".format(file_size_dl)
                if file_size:
                    status += "   [{0:6.2f}%]".format(file_size_dl * 100 / file_size)
                status += chr(13)
                print(status, end="")
            f.close()
            print()
        return filename

    @staticmethod
    def get_phrases(phrase_state):
        headers = LocalisejsUtil.get_headers()
        response = requests.request("GET", LocalisejsUtil.get_url('phrases', {'state': phrase_state}),
                                    headers=headers)
        phrase_collection = []
        phrases_lst = response.json()['data']['phrases']
        if len(phrases_lst) > 0:
            for i, value in enumerate(phrase_dict['phrase'] for phrase_dict in phrases_lst):
                phrase_collection.append(value[1:])
        return phrase_collection


if __name__ == '__main__':
    task = args.task
    if task is None or task not in ['push_translation', 'download_translation', 'get_phrases']:
        sys.exit('Operation (argument: --operation value) name must be provided. Valid values are: '
                 '{ push_translation, download_translation, get_phrases }')

    if task == 'push_translation':
        readFile = args.filename
        if readFile is None:
            sys.exit('File to read must be provided. Generally it is the file at the root of your directory.'
                     '(argument: --phraseFile value)')
        else:
            LocalisejsUtil.push_for_translation()

    if task == 'download_translation':
        fileFormat = args.filetype
        if fileFormat is None or fileFormat not in ['xliff', 'json', 'yaml', 'csv', 'po', 'strings', 'xml', 'resx']:
            sys.exit('Download (argument: --downloadFormat value) format must be provided. Valid values are: '
                     '{ xliff, json, yaml, csv, po, strings, xml, resx }')
        else:
            lang = args.language
            if lang is None:
                sys.exit('Language (argument: --language value) must be provided. Valid values are: { ko, en }')
            else:
                file = LocalisejsUtil.download_translation()
                print(file)

    if task == 'get_phrases':
        state = args.state
        if state is None:
            sys.exit('In order to get phrases you must specify the state against which query should be made'
                     '(argument: --state value). Valid values are: {\'pending\', \'active\', \'all\'}')
        else:
            phrases = LocalisejsUtil.get_phrases(state)
            print(phrases)
