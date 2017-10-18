import unittest

from media_management_scripts.renamer import rename_process


def new_names(results):
    return list(list(zip(*results))[1])


class RenameTests(unittest.TestCase):
    def test_rename(self):
        template = '${i}'
        files = ['test.mkv', 'test2.mkv']
        results = new_names(rename_process(template, files))
        self.assertEqual(['1', '2'], results)

    def test_function(self):
        template = '${i | zpad}'
        files = ['test.mkv', 'test2.mkv']
        results = new_names(rename_process(template, files))
        self.assertEqual(['01', '02'], results)

    def test_nested(self):
        template = '${lpad(zpad(i), 3)}'
        files = ['test.mkv', 'test2.mkv']
        results = new_names(rename_process(template, files))
        self.assertEqual([' 01', ' 02'], results)

    def test_concat(self):
        template = '${zpad(i)+\' \'}'
        files = ['test.mkv', 'test2.mkv']
        results = new_names(rename_process(template, files))
        self.assertEqual(['01 ', '02 '], results)

    def test_ifempty(self):
        template = '${ifempty(var, \'test\', \'\')}'
        files = ['test.mkv']
        params = {'var': None}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(['test'], results)

        template = '${ifempty(var, None, var+\'test\')}'
        files = ['test.mkv']
        params = {'var': 'ww'}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(['wwtest'], results)

    def test_regex(self):
        template = '${re[1]}'
        files = ['S2', 'S1']
        regex = 'S(\d)'
        results = new_names(rename_process(template, files, regex=regex))
        self.assertEqual(['2', '1'], results)

    def test_regex_missing(self):
        template = '${re[1]}'
        files = ['S2', 'S']
        regex = 'S(\d)'
        with self.assertRaises(IndexError) as context:
            new_names(rename_process(template, files, regex=regex))

    def test_regex_missing_ignore(self):
        template = '${re[1]}'
        files = ['S2', 'S']
        regex = 'S(\d)'
        results = new_names(rename_process(template, files, regex=regex, ignore_missing_regex=True))
        self.assertEqual(['2', ''], results)

    def test_regex_missing_ifempty(self):
        template = '${ifempty(re[1], "Unknown", str(re[1])+" ")}'
        files = ['S2', 'S']
        regex = 'S(\d)'
        results = new_names(rename_process(template, files, regex=regex, ignore_missing_regex=True))
        self.assertEqual(['2 ', 'Unknown'], results)

    def test_plex(self):
        template = '${inherit "plex"}'
        files = ['file.mkv']
        params = {'show': 'TV Show', 'season': 1, 'episode_num': 2, 'episode_name': 'Episode Name'}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(['TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv'], results)

        params = {'show': 'TV Show', 'season': 1, 'episode_num': 2, 'episode_name': None}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(['TV Show/Season 01/TV Show - S01E02.mkv'], results)

        template = '${inherit "plex"}/Some/Path/'
        params = {'show': 'TV Show', 'season': 1, 'episode_num': 2, 'episode_name': 'Episode Name'}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(['/Some/Path/TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv'], results)
