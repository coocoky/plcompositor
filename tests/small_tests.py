import unittest
import sys
import os
import shutil
import numpy
import traceback
import json

from osgeo import gdal, gdal_array

TEMPLATE_FLOAT = 'data/2x2_float_template.tif'
TEMPLATE_GRAY = 'data/2x2_gray_template.tif'
TEMPLATE_RGB  = 'data/2x2_rgb_template.tif'
TEMPLATE_RGBA = 'data/2x2_rgba_template.tif'

class Tests(unittest.TestCase):

    def setUp(self):
        self.temp_test_files = []

    def tearDown(self):
        pass

    def make_file(self, template_filename, data=None, filename = None):
        if filename is None:
            caller = traceback.extract_stack(limit=2)[0][2]
            filename = '%s_%d.tif' % (caller, len(self.temp_test_files))

        shutil.copyfile(template_filename, filename)
        self.temp_test_files.append(filename)
        
        if data is not None:
            data = numpy.array(data)
            ds = gdal.Open(filename, gdal.GA_Update)
            if len(data.shape) == 2:
                ds.GetRasterBand(1).WriteArray(data)
            else:
                assert ds.RasterCount == data.shape[0]
                for bi in range(ds.RasterCount):
                    ds.GetRasterBand(bi+1).WriteArray(data[bi])
            ds = None

        return filename

    def clean_files(self):
        for filename in self.temp_test_files:
            os.unlink(filename)
        self.temp_test_files = []

    def compare_file(self, test_file, golden_data, tolerance=0.0):
        test_data = gdal_array.LoadFile(test_file)
        
        if golden_data is None:
            print 'No golden data, %s is:' % test_file
            print test_data.tolist()
            raise Exception('No golden data, %s is:' % test_file)

        if not numpy.allclose(test_data, numpy.array(golden_data),atol=tolerance):
            print '%s differs from golden data:' % test_file
            print
            print test_file
            print test_data.tolist()
            print
            print 'golden data:'
            print golden_data
            
            raise Exception('%s differs from golden data' % test_file)

    def run_compositor(self, args):
        if os.path.exists('../compositor'):
            binary = '../compositor'
        else:
            binary = 'compositor'
        cmd = ' '.join([binary] + args)
        print cmd
        return os.system(cmd)

    def test_small_darkest_gray(self):
        test_file = self.make_file(TEMPLATE_GRAY)
        quality_out = 'sd_quality_out.tif'

        args = [
            '-q',
            '-s', 'quality', 'darkest',
            '-o', test_file, 
            '-qo', quality_out,
            '-i', 
            self.make_file(TEMPLATE_GRAY, [[0, 1], [6, 5]]),
            '-i',
            self.make_file(TEMPLATE_GRAY, [[9, 8], [2, 3]]),
            ]

        self.run_compositor(args)

        self.compare_file(test_file, [[0, 1], [2, 3]])
        self.compare_file(quality_out, 
                          [[[1.0, 0.9960784316062927],
                            [0.9921568632125854, 0.9882352948188782]],
                           [[1.0, 0.9960784316062927],
                            [0.9764705896377563, 0.9803921580314636]],
                           [[0.9647058844566345, 0.9686274528503418],
                            [0.9921568632125854, 0.9882352948188782]]],
                          tolerance = 0.000001)

        os.unlink('sd_quality_out.tif')
        self.clean_files()
        
    def test_small_darkest_gray_json(self):
        json_file = 'small_darkest_gray.json'
        test_file = self.make_file(TEMPLATE_GRAY)
        quality_out = 'sdj_quality_out.tif'

        control = {
            'output_file': test_file,
            'quality_output': quality_out,
            'compositors': [
                {
                    'class': 'darkest',
                    },
                ],
            'inputs': [
                {
                    'filename': self.make_file(TEMPLATE_GRAY, [[0, 1], [6, 5]]),
                    },
                {
                    'filename': self.make_file(TEMPLATE_GRAY, [[9, 8], [2, 3]]),
                    },
                ],
            }

        open(json_file,'w').write(json.dumps(control))
        self.run_compositor([ '-q', '-j', json_file])

        self.compare_file(test_file, [[0, 1], [2, 3]])
        self.compare_file(quality_out,
                          [[[1.0, 0.9960784316062927],
                            [0.9921568632125854, 0.9882352948188782]],
                           [[1.0, 0.9960784316062927],
                            [0.9764705896377563, 0.9803921580314636]],
                           [[0.9647058844566345, 0.9686274528503418],
                            [0.9921568632125854, 0.9882352948188782]]],
                          tolerance = 0.000001)

        os.unlink('sdj_quality_out.tif')
        os.unlink(json_file)
        self.clean_files()
        
    def test_small_darkest_rgb(self):
        test_file = self.make_file(TEMPLATE_RGB)
        args = [
            '-q',
            '-s', 'quality', 'darkest',
            '-o', test_file, 
            '-i',
            self.make_file(TEMPLATE_RGB, 
                           [[[9, 1], [3, 0]],
                            [[0, 1], [3, 0]],
                            [[0, 1], [3, 9]]]),
            '-i',
            self.make_file(TEMPLATE_RGB, 
                           [[[0, 8], [6, 5]],
                            [[9, 8], [6, 5]],
                            [[9, 8], [6, 5]]]),
            ]

        self.run_compositor(args)

        self.compare_file(test_file, 
                          [[[9, 1], [3, 0]], 
                           [[0, 1], [3, 0]], 
                           [[0, 1], [3, 9]]])

        self.clean_files()
        
    def test_small_darkest_rgba(self):
        test_file = self.make_file(TEMPLATE_RGBA)
        args = [
            '-q',
            '-s', 'quality', 'darkest',
            '-o', test_file, 
            '-i',
            self.make_file(TEMPLATE_RGBA, 
                           [[[0, 1], [3, 4]],
                            [[0, 1], [3, 4]],
                            [[0, 1], [3, 4]],
                            [[255, 255], [255, 255]]]),
            '-i',
            self.make_file(TEMPLATE_RGBA, 
                           [[[9, 8], [6, 5]],
                            [[9, 8], [6, 5]],
                            [[9, 8], [6, 5]],
                            [[255, 255], [255, 255]]]),
            ]

        self.run_compositor(args)

        self.compare_file(test_file, 
                          [[[0, 1], [3, 4]], 
                           [[0, 1], [3, 4]], 
                           [[0, 1], [3, 4]], 
                           [[255, 255], [255, 255]]])

        self.clean_files()
        
    def test_percentile(self):
        test_file = self.make_file(TEMPLATE_GRAY)
        
        args = [
            '-q',
            '-s', 'quality', 'darkest',
            '-s', 'quality_percentile', '60.0',
            '-o', test_file, 
            '-i', self.make_file(TEMPLATE_GRAY, [[9, 0], [1, 1]]),
            '-i', self.make_file(TEMPLATE_GRAY, [[5, 1], [9, 9]]),
            '-i', self.make_file(TEMPLATE_GRAY, [[1, 2], [9, 1]]),
            ]

        self.run_compositor(args)

        self.compare_file(test_file, [[5, 1], [9, 1]])

        self.clean_files()
        
    def test_percentile_json(self):
        json_file = 'percentile.json'
        test_file = self.make_file(TEMPLATE_GRAY)

        control = {
            'output_file': test_file,
            'compositors': [
                {
                    'class': 'darkest',
                    },
                {
                    'class': 'percentile',
                    'quality_percentile': 60.0,
                    },
                ],
            'inputs': [
                {
                    'filename': self.make_file(TEMPLATE_GRAY, [[9, 0], [1, 1]]),
                    },
                {
                    'filename': self.make_file(TEMPLATE_GRAY, [[5, 1], [9, 9]]),
                    },
                {
                    'filename': self.make_file(TEMPLATE_GRAY, [[1, 2], [9, 1]]),
                    },
                ],
            }

        open(json_file, 'w').write(json.dumps(control))
        self.run_compositor(['-q', '-j', json_file])
        self.compare_file(test_file, [[5, 1], [9, 1]])

        os.unlink(json_file)
        self.clean_files()
        
    def test_quality_file(self):
        test_file = self.make_file(TEMPLATE_GRAY)
        quality_out = 'qf_test_quality.tif'

        in_1 = self.make_file(TEMPLATE_GRAY, [[101, 101], [101, 101]])
        self.make_file(TEMPLATE_FLOAT, [[0.5, 2.0], [-1.0, 0.01]],
                       filename = in_1 + '.q')

        in_2 = self.make_file(TEMPLATE_GRAY, [[102, 102], [102, 102]])
        self.make_file(TEMPLATE_FLOAT, [[2.0, 1.8], [-1.0, 0.25]],
                       filename = in_2 + '.q')
                       
        args = [
            '-q',
            '-s', 'quality', 'darkest',
            '-qo', quality_out,
            '-s', 'quality_file', '.q',
            '-s', 'quality_file_scale_min', '0.0',
            '-s', 'quality_file_scale_max', '2.0',
            '-o', test_file, 
            '-i', in_1,
            '-i', in_2,
            ]

        self.run_compositor(args)

        self.compare_file(test_file, [[102, 101], [0, 102]])
        self.compare_file(quality_out, 
                          [[[0.6000000238418579, 0.6039215922355652],
                            [0.0, 0.07500000298023224]],
                           [[0.1509803980588913, 0.6039215922355652],
                            [-1.0, 0.0030196078587323427]],
                           [[0.6000000238418579, 0.5400000214576721],
                            [-1.0, 0.07500000298023224]]],
                          tolerance=0.001)

        os.unlink(quality_out)
        self.clean_files()
        
    def test_quality_file_json(self):
        json_file = 'quality_file.json'
        test_file = self.make_file(TEMPLATE_GRAY)
        quality_out = 'qfj_test_quality.tif'

        control = {
            'output_file': test_file,
            'quality_output': quality_out,
            'compositors': [
                {
                    'class': 'darkest',
                    },
                {
                    'class': 'qualityfromfile',
                    'file_key': 'quality',
                    'scale_min': 0.0,
                    'scale_max': 2.0,
                    },
                ],
            'inputs': [
                {
                    'filename': self.make_file(TEMPLATE_GRAY, 
                                               [[101, 101], [101, 101]]),
                    'quality': self.make_file(TEMPLATE_FLOAT, 
                                              [[0.5, 2.0], [-1.0, 0.01]]),
                    },
                {
                    'filename': self.make_file(TEMPLATE_GRAY, 
                                               [[102, 102], [102, 102]]),
                    'quality': self.make_file(TEMPLATE_FLOAT,
                                              [[2.0, 1.8], [-1.0, 0.25]]),
                    },
                ],
            }

        open(json_file,'w').write(json.dumps(control))
        self.run_compositor(['-q', '-j', json_file])

        self.compare_file(test_file, [[102, 101], [0, 102]])
        self.compare_file(quality_out, 
                          [[[0.6000000238418579, 0.6039215922355652],
                            [0.0, 0.07500000298023224]],
                           [[0.1509803980588913, 0.6039215922355652],
                            [-1.0, 0.0030196078587323427]],
                           [[0.6000000238418579, 0.5400000214576721],
                            [-1.0, 0.07500000298023224]]],
                          tolerance=0.001)

        os.unlink(quality_out)
        os.unlink(json_file)
        self.clean_files()
        
if __name__ == '__main__':
    unittest.main()
