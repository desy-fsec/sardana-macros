# coding=utf-8
from sardana.macroserver.macro import Macro, Type
import time

SRC_IMAGES = "/beamlines/bl13/controls/processing/edna-mx/strategy/benchmark/images"
RESULTS_ROOT = "/beamlines/bl13/controls/workspace/tmp/"
XML_TEMPLATE = "/beamlines/bl13/controls/processing/edna-mx/input_plugin_templates/XSDataInputMXCuBE.xml"
SUFFIX = "_dnafiles"
XML_NAME = "XSDataInputMXCuBE.xml"


class mockup_testxtal_benchmark(Macro):

    param_def = []
    # param_def = [['results_dir', Type.String, "./", 'Results folder']]

    def run(self):
        self.setEnv("MXCurrentStrategy", "Running...")
        self.info('Generating images...')
        time.sleep(2)
        image_list = self.generate_images()
        self.info('Generating XML input file...')
        time.sleep(3)
        self.generate_xml(image_list)
        self.setEnv("MXCurrentStrategy", self.results_path)
        self.info('Current results_dir: %s' % self.results_path)
        self.info('[done]')

    def generate_images(self):
        from datetime import datetime
        import os
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.images_path = os.path.join(RESULTS_ROOT, "images_%s" % date)
        import os
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)
        import shutil
        src_files = os.listdir(SRC_IMAGES)
        dest_files = []
        for file_name in src_files:
            full_file_name = os.path.join(SRC_IMAGES, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, self.images_path)
                dest_files.append(os.path.join(self.images_path,file_name))
        return dest_files

    def generate_xml(self, image_list):
        from ednaXMLbuilder import XMLEdnaFile, add_images2xml
        import shutil
        import os
        # Create results path
        #self.results_path = os.path.join(self.images_path, SUFFIX)
        self.results_path = self.get_results_folder(image_list[0])
        if not os.path.exists(self.results_path):
            os.makedirs(self.results_path)
        # copy template file to current location and open xml parser
        template = XML_TEMPLATE
        self.xml_file = os.path.join(self.images_path, XML_NAME)
        shutil.copy(template, self.xml_file)
        xml = XMLEdnaFile(self.xml_file)

        # Edit xml file
        # Add output results file
        xml.set("outputFileDirectory/path", self.results_path)

        # insert new tags
        xml_images = add_images2xml(image_list)
        xml.insert('dataSet', xml_images)

    def get_results_folder(self, image_path):
        # Get the first image path from the test set and return
        # the corresponding results folder following the convention:
        # /7_1_0001.cbf --> /7_1_dnafiles"
        return "_".join(image_path.split("_")[:-1]) + SUFFIX
        

