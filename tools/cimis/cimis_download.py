#--------------------------------
# Name:         cimis_download.py
# Purpose:      Download CIMIS data
#--------------------------------

import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

import _utils


def main(start_dt, end_dt, output_ws, variables=['all'],
         overwrite_flag=False):
    """Download CIMIS data

    Parameters
    ----------
    start_dt : datetime
        Start date.
    end_dt : datetime
        End date.
    output_ws : str
        Folder path of the output ascii files.
    variables : list
        Choices: 'ETo', 'Rs', 'Tdew', 'Tn', 'Tx', 'U2', 'all'
        'K', 'Rnl', 'Rso' can be downloaded but are not needed.
        Set as ['all'] to download all variables.
    overwrite_flag : bool, optional
        If True, overwrite existing files (the default is False).

    Returns
    -------
    None

    Notes
    -----
    The file on the CIMIS server do not appeared to be compressed even though
      they have a .asc.gz file extension.
    The files will be saved directly to ASCII type.

    """
    logging.info('\nDownloading CIMIS data\n')
    logging.debug('  Start date: {}'.format(start_dt))
    logging.debug('  End date:   {}'.format(end_dt))

    # Site URL
    site_url = 'http://cimis.casil.ucdavis.edu/cimis/'

     # CIMIS rasters to extract
    data_full_list = ['ETo', 'Rso', 'Rs', 'Tdew', 'Tn', 'Tx', 'U2']
    if not variables:
        logging.error('\nERROR: variables parameter is empty\n')
        sys.exit()
    elif type(variables) is not list:
        logging.error('\nERROR: variables parameter must be a list\n')
        sys.exit()
    elif 'all' in variables:
        logging.error('Downloading all variables\n  {}'.format(
            ','.join(data_full_list)))
        data_list = ['ETo', 'Rso', 'Rs', 'Tdew', 'Tn', 'Tx', 'U2']
    elif not set(variables).issubset(set(data_full_list)):
        logging.error('\nERROR: variables parameter is invalid\n  {}'.format(
            variables))
        sys.exit()
    else:
        data_list = variables

    # Build output workspace if it doesn't exist
    if not os.path.isdir(output_ws):
        os.makedirs(output_ws)

    # Set data types to upper case for comparison
    data_list = list(map(lambda x: x.lower(), data_list))

    # Each sub folder in the main folder has all imagery for 1 day
    # The path for each subfolder is the /YYYY/MM/DD
    logging.info('')
    for input_date in _utils.date_range(start_dt, end_dt + dt.timedelta(1)):
        logging.info('{}'.format(input_date.date()))
        date_url = site_url + '/' + input_date.strftime("%Y/%m/%d")
        logging.debug('  {}'.format(date_url))

        # Download a list of all files in the date sub folder
        try:
            date_html = requests.get(date_url + '/').text
        except:
            logging.error("  ERROR: {}".format(date_url))
            continue
        file_list = sorted(list(set(
            re.findall(r'href=[\'"]?([^\'" >]+)', date_html))))
        if not file_list:
            logging.debug('  Empty file list, skipping date')
            continue

        # Create a separate folder for each day
        year_ws = os.path.join(output_ws, input_date.strftime("%Y"))
        if not os.path.isdir(year_ws):
            os.mkdir(year_ws)
        date_ws = os.path.join(year_ws, input_date.strftime("%Y_%m_%d"))
        if not os.path.isdir(date_ws):
            os.mkdir(date_ws)

        # Process each file in sub folder
        for file_name in file_list:
            if not file_name.endswith('.asc.gz'):
                continue
            elif file_name.replace('.asc.gz', '').lower() not in data_list:
                continue

            file_url = '{}/{}'.format(date_url, file_name)

            # DEADBEEF - The file on the CIMIS server do not appeared to be
            #   compressed even though they have a .asc.gz file extension.
            # Saving the files directly to ASCII type.
            save_path = os.path.join(
                date_ws, file_name.replace('.asc.gz', '.asc'))
            # save_path = os.path.join(date_ws, file_name)

            logging.info('  {}'.format(os.path.basename(save_path)))
            logging.debug('    {}'.format(file_url))
            logging.debug('    {}'.format(save_path))
            if os.path.isfile(save_path):
                if not overwrite_flag:
                    logging.debug('    File already exists, skipping')
                    continue
                else:
                    logging.debug('    File already exists, removing existing')
                    os.remove(save_path)

            _utils.url_download(file_url, save_path)

    logging.debug('\nScript Complete')


def arg_parse():
    """Base all default folders from script location
        scripts: ./pymetric/tools/cimis
        tools:   ./pymetric/tools
        output:  ./pymetric/cimis
    """
    script_folder = sys.path[0]
    code_folder = os.path.dirname(script_folder)
    project_folder = os.path.dirname(code_folder)
    cimis_folder = os.path.join(project_folder, 'cimis')
    ascii_folder = os.path.join(cimis_folder, 'input_asc')

    parser = argparse.ArgumentParser(
        description='Download daily CIMIS data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--start', required=True, type=_utils.valid_date, metavar='YYYY-MM-DD',
        help='Start date')
    parser.add_argument(
        '--end', required=True, type=_utils.valid_date, metavar='YYYY-MM-DD',
        help='End date')
    parser.add_argument(
        '--ascii', default=ascii_folder, metavar='PATH',
        help='Output ascii root folder path')
    parser.add_argument(
        '-v', '--vars', default=['all'], nargs='+', metavar='ETo',
        choices=['ETo', 'Rso', 'Rs', 'Tdew', 'Tn', 'Tx', 'U2', 'All'],
        help='CIMIS variables to download')
    parser.add_argument(
        '-o', '--overwrite', default=False, action="store_true",
        help='Force overwrite of existing files')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.ascii and os.path.isdir(os.path.abspath(args.ascii)):
        args.ascii = os.path.abspath(args.ascii)

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    logging.info('{:<20s} {}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{:<20s} {}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(start_dt=args.start, end_dt=args.end, output_ws=args.ascii,
         variables=args.vars, overwrite_flag=args.overwrite)
