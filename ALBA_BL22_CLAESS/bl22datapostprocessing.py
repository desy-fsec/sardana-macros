#!/usr/bin/env python

import os
from collections import OrderedDict


# Number of point to remove
SHIFT = 1

try:
    # Sardana macro declaration.
    from sardana.macroserver.macro import Macro, Type, Optional

    class extractscans(Macro):
        """
        Macro to concatenate and extract the last N scans
        """
        param_def = [
            ['outputFile', Type.String, None, 'Name for the output file'],
            ['nrOfScans', Type.Integer, 1, 'Nr of scans to concatenate'],
            ['lastScanId', Type.Integer, Optional, 'last scan id'],
            ['inputFile', Type.String, Optional, 'Input file'],
            ['sampleDescription', Type.String,  '',
             'Sample description include it as comments'],
            ['shiftXspress', Type.Boolean, True, 'Shift xspress data'],
            ['removeMythen', Type.Boolean, True, 'Remove Mythen 1D data'],

        ]

        def run(self, output_file, nr_scans, last_scanid, input_file,
                sample_desc, shift_xspress, rm_mythen):

            # Check the input file and the last_scanid
            if input_file is None:
                scan_dir = self.getEnv("ScanDir")
                scan_file = self.getEnv("ScanFile")
                if type(scan_file) is list:
                    for f in scan_file:
                        if f.endswith(".dat"):
                            input_file = os.path.join(scan_dir, f)
                            break
            if input_file is None:
                raise RuntimeError('The macro only works with spec file!')

            if last_scanid is None:
                last_scanid = self.getEnv("ScanID")

            extract_scans(self, output_file, nr_scans, last_scanid,
                          input_file, sample_desc, shift_xspress, rm_mythen)

except Exception:
    pass


def get_filename(filename, len_auto_index=3):
    fname, fext = os.path.splitext(filename)
    auto_index = 0
    while len_auto_index > 0:
        filename = '{0}_{1:0{2}d}{3}'.format(fname, auto_index,
                                             len_auto_index, fext)
        if not os.path.exists(filename):
            break
        auto_index += 1

    return filename


def _read_raw_data_spec(f, scan_id):
    found = False
    for line in f:
        line_lower = line.lower()
        start_scan = '#s {0}'.format(scan_id)
        if start_scan in line_lower:
            found = True
            break
    if not found:
        msg = 'The ScanID: {0} is not in the file: {1}'.format(scan_id, f.name)
        raise RuntimeError(msg)

    data = OrderedDict()
    channels_names = []
    channel_1d = ''
    # Skip header and snapshots
    for line in f:
        line_lower = line.lower()
        if '#n' in line_lower:
            break

    for line in f:
        line_lower = line.lower()
        if '#l' in line_lower:
            break
        if '#@' in line_lower:
            if 'det' in line_lower:
                channel_1d = line.split()[1]
                data[channel_1d] = []

    # Read channels name
    channels_names += line.split()[1:]
    for name in channels_names:
        data[name] = []

    # Read channels data
    for line in f:
        if '#' in line:
            break
        if '@a' in line.lower():
            # Read 1d data
            ch1d_data = map(float, line.split()[1:])
            data[channel_1d].append(ch1d_data)
        else:
            channels_data = map(float, line.split())
            for name, value in zip(channels_names, channels_data):
                data[name].append(value)
    return data


def read_raw_data_spec(filename, scans_ids):
    with open(filename, 'r') as f:
        scans_ids.sort()
        scans_datas = OrderedDict()
        for scan_id in scans_ids:
            scans_datas[scan_id] = _read_raw_data_spec(f, scan_id)
    return scans_datas


def read_data(log, nr_scans, last_scanid, input_file):
    if nr_scans < 1:
        raise ValueError('You must read at least one scan')

    first_scan = last_scanid - nr_scans + 1
    # Be compatible with python3
    scans_ids = list(range(first_scan, last_scanid + 1))
    scans_ids.sort()

    log.info('Reading scans {0} from {1}'.format(scans_ids, input_file))

    scans_data = read_raw_data_spec(input_file, scans_ids)

    return scans_data, input_file


def write_data(log, output_file, data, sample_desc, input_file, scans_ids):
    if sample_desc == '':
        _, fname = os.path.split(output_file)
        sample_desc, _ = os.path.splitext(fname)

    output_file = get_filename(output_file)
    log.info('Writing data.....')
    with open(output_file, 'w') as f:
        f.write('#S 0 Fake Scan\n')
        f.write('#S 1 Extracted scans: {0}\n'.format(scans_ids))
        f.write('#C InputFile: {0}\n'.format(input_file))
        f.write('#C Sample Description: {0}\n'.format(sample_desc))
        labels = '  '.join(data.keys())
        f.write('#L {0}\n'.format(labels))
        for idx in data['Pt_No']:
            data_line = ''
            for channel_data in data.values():
                data_line += '{0} '.format(channel_data[idx])
            data_line.strip()
            data_line += '\n'
            f.write(data_line)
    log.output('Extracted scans on: {0}'.format(output_file))


def extract_scans(log, output_file, nr_scans, last_scanid, input_file,
                  sample_desc, shift_xspress, rm_mythen):

    # Read date from spec file
    scans_data, input_file = read_data(log, nr_scans,
                                       last_scanid=last_scanid,
                                       input_file=input_file)
    # Be compatible with python3
    scans_ids = list(scans_data.keys())
    total_len = 0

    for scan in scans_data.values():
        total_len += len(scan['Pt_No'])

    used_xspress = False
    for channel in scans_data[scans_ids[0]]:
        if shift_xspress and channel.startswith('x_ch'):
            used_xspress = True
            total_len -= SHIFT * len(scans_ids)
            break

    nr_points = range(total_len)
    data = OrderedDict()
    data['Pt_No'] = nr_points

    for scan_id in scans_ids:
        for channel, channel_data in scans_data[scan_id].items():
            if channel in ['Pt_No', 'dt']:
                continue
            if rm_mythen and channel == 'm_raw':
                continue
            if channel not in data:
                # TODO: Implement solution to check if the previous scan do
                # not have the data
                data[channel] = []
            if used_xspress:
                # Shift the Xspress3 channels data to the begging and the
                # other channel remove the last part. This is a
                # temporally solution upto find the problem on Lima.
                if channel.startswith('x_ch'):
                    channel_data = channel_data[SHIFT:]
                else:
                    channel_data = channel_data[:-SHIFT]

            data[channel] += channel_data
    write_data(log, output_file, data, sample_desc, input_file, scans_ids)


if __name__ == '__main__':
    import argparse
    import logging
    log = logging.getLogger('Application')
    logging.basicConfig(level=logging.INFO)
    # To be compatible with Sardana
    log.output = log.info

    desc = 'Claess Data Post-Processing to extract scan data.'
    parse = argparse.ArgumentParser(description=desc)
    parse.add_argument('input', help='Input raw data filename.')
    parse.add_argument('scanID', help='Last scan ID to extract.')
    parse.add_argument('nrScans', help='Number of scan to extract.')
    parse.add_argument('output', help='Output filename.')
    parse.add_argument('-x', '--xspress3', action='store_false',
                       help='Deactivate Xspress3 shift')
    parse.add_argument('-m', '--mythen', action='store_false',
                       help='Deactivate mythen remove data')

    args = parse.parse_args()
    output_file = args.output
    nr_scans = int(args.nrScans)
    last_scanid = int(args.scanID)
    input_file = args.input
    sample_desc = ''
    shift_xspress = args.xspress3
    rm_mythen = args.mythen

    extract_scans(log, output_file, nr_scans, last_scanid, input_file,
                  sample_desc, shift_xspress, rm_mythen)


