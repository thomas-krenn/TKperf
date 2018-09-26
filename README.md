# TKperf performance test tool for SSDs, HDDs and RAID devices

## Disclaimer
* **ATTENTION: All data on the tested device is lost!**
* The given device becomes overwritten multiple times!
* For SSDs a secure erase is carried out, too.
* For RAID devices each device becomes overwritten or secure erased

## Requirements
* The following python packages are required:
  * logging
  * json
  * lxml
  * subprocess
  * datetime
  * argparse
  * copy
  * collections
  * numpy
  * matplotlib
  * os
  * sys
  * makedirs, path, walk
  * zipfile
  * smtplib
  * email
  * ABCMeta, abstractmethod
  * string.split
  * lstat
  * stat.S_ISBLK
  * string.split
  * time.sleep
  * setuptools
* Under Ubuntu it is normally sufficient to install:
    $ sudo apt-get install python-argparse python-matplotlib \
    python-lxml python-numpy python-simplejson python-setuptools
* The following software is required:
  * FIO version 2.0.3 or higher.
    Please note that older FIO versions are not supported due to an
    incompatibility in the terse output of FIO. The tests will not produce any
    valuable information if FIO is older than 2.0.3.
  * hdparm
  * sg3-utils (for testing SAS devices)
  * nvme-cli (for testing nvme devices)
    * E.g. https://github.com/linux-nvme/nvme-cli.git
  * rst2pdf

## Setup
* TKperf checks if FIO is found with:
    $ which fio
  Please ensure that FIO is in your path and executable.
* To install FIO visit
    http://freecode.com/projects/fio
* To fetch FIO per git use:
    $ git clone git://git.kernel.dk/fio.git
* An installation howto (currently only in German):
    http://www.thomas-krenn.com/de/wiki/Fio_kompilieren

## Installation
* To install TKperf simply call
    $ sudo python setup.py install
* If the source is updated via git ensure to reinstall TKperf.
* An installation howto (in German):
    https://www.thomas-krenn.com/de/wiki/TKperf

## Hardware Prerequisites
* To carry out a Secure Erase it is necessary that the SSD is NOT in the
  frozen state.
  (http://www.thomas-krenn.com/en/wiki/SSD_Secure_Erase#Step_1:_NOT_Frozen)
  If the SSD is frozen un- and replug the device while the host is on.

## Running a test
* The main script file is called tkperf:
    $ which tkperf
    /usr/local/bin/tkperf
* Call tkperf with the command line options described below.
  To get the help output use:
    $ tkperf -h

### RAID Tests
* To run a RAID test you have to create a RAID config file (cf. 'examples').
  The config file specifies RAID type, devices and level. For Avago/LSI use
  'hw_lsi' as type, for mdadm 'sw_mdadm'. hw_lsi uses enclosure IDs for the
  devices, you can get them with:
  $ sudo storcli64 /c0 /eall /sall show
  mdadm uses normal device paths like '/dev/sda', '/dev/sdb' etc.
  Example config:
  {
    "devices": [
        "252:0",
        "252:1"
    ],
    "raidlevel": 1,
    "type": "hw_lsi"
  }

## Log File
* The log file is named after the given test name (e.g. 'intel320' in the
  example below). Inspect the log from time to time to ensure that no errors
  occur. In the log all calls to FIO are stated out. Also the results from the
  steady rounds are written to the log file. If you have any doubts that the
  results in the pdf report are correct check the log what performance values
  FIO returned. As the log file contains the FIO output in terse version, read
  the FIO HOWTO to find out how to interpret it.
  If a report is generated from the xml file a seperate log is created. This log
  gets '.xml' appended.

## Examples
* To run a test on a remote machine and ensure it is not stopped if the
  connection closes it is good practice to start the script in a screen session.
  See 'man screen' for more information. Basically it is sufficient to call
  'screen', start the script and then detach with 'Ctrl-a d'.
* As root or with 'sudo':
    $ sudo tkperf ssd intel320 /dev/sde -nj 2 -iod 16 -rfb
* If hdparm does not output any valuable information for your device,
  use a description file to provide the device informations:
    $ sudo tkperf ssd intel320 /dev/sde -nj 2 -iod 16 -rfb -dsc intel320.dsc
* Also nohup could be used to start a test. To disable the warning that the
  device will be erased ('-ft', '--force-test'). Note that with nohup it is
  difficult to use sudo and redirect stdout/stderr to output files.
    $ sudo nohup tkperf ssd intel320 /dev/sde -ft -nj 2 \
      -iod 16 -rfb 1>runTest.out 2>runTest.err &

### RAID Examples
* To deal with Avago RAID devices, you have to install storcli
* To deal with software RAID devices, you have to install mdadm
* First, create the RAID device manually, this has only to be done the first
  time. Afterwards the RAID is re-created automatically:
    $ sudo storcli64 /c0 add vd type=raid1 drives=252:0,252:1
  Then check with e.g. 'lsblk' which device was created and start the test
  with:
    $ sudo tkperf raid LSI-I3500-R5-4 /dev/sdb -c raid5.cfg -nj 2 -iod 16

## SSD Compression
* If the SSD controller uses compression use the '-rfb' switch to ensure that
  data buffers used by FIO are completely random. This option enables the
  'refill_buffers' from FIO.

## Description File
* If 'hdparm -I' does not provide any valuable information about a drive, you
  have to provide a so called 'description file'. This file just contains some
  meta information for the pdf report and so it can be a simple text file
  describing the tested device. When calling the script provide the path to the
  description file with '-dsc PATH_TO_FILE'.

## Generate a PDF report
* To generate a pdf from the rst use rst2pdf:
    $ rst2pdf test.rst test.pdf

## Loading from XML
* To load an already carried out test from the generated xml file, use
  the '-xml' option:
    $ sudo tkperf ssd intel520 none -xml
* In this case as tested device 'none' is used, it is there just as a
  placeholder.
* Loading from an xml file is useful if something has changed in the plotting
  methods and you want to re-plot the results. This is mainly required during a
  development process or if a major update/bugfix has been made to tkperf.

## Creating compare plots
* With the help of the generated xml files multiple devices can be compared (up
  to seven devices). The script 'tkperf-cmp' generates the compare plots for
  write saturation, throughput, IOPS and latency. To generate the plots use:
  $ tkperf-cmp ssd Samsung840PRO-256GB.xml Samsung840EVO-250GB.xml
* Guide (in German)
  https://www.thomas-krenn.com/de/wiki/SSD_Performance_mit_TKperf_vergleichen

## Further information
* To get more information about how the SSD tests are carried out, visit
  http://www.snia.org/tech_activities/standards/curr_standards/pts for the
  standard these tests are based on.

## Help Text

### tkperf
```
usage: tkperf [-h] [-v] [-d] [-q] [-nj NUMJOBS] [-iod IODEPTH] [-rt RUNTIME]
              [-i {sas,nvme,fusion}] [-xml] [-rfb] [-dsc DESC_FILE]
              [-c CONFIG] [-ft] [-fm FEATURE_MATRIX] [-hddt {iops,tp}]
              [-ssdt {iops,lat,tp,writesat}] [-m MAIL] [-s SMTP]
              [-g GEN_REPORT]
              {hdd,ssd,raid} testname device

positional arguments:
  {hdd,ssd,raid}        specify the test mode for the device
  testname              name of the performance tests, corresponds to the
                        result output filenames
  device                device to run fio test on

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         get the version information
  -d, --debug           get detailed debug information
  -q, --quiet           turn off logging of info messages
  -nj NUMJOBS, --numjobs NUMJOBS
                        specify number of jobs for fio
  -iod IODEPTH, --iodepth IODEPTH
                        specify iodepth for libaio used by fio
  -rt RUNTIME, --runtime RUNTIME
                        specify the fio runtime of one test round, if not set
                        this is 60 seconds
  -i {sas,nvme,fusion}, --interface {sas,nvme,fusion}
                        specify optional device interface
  -xml, --fromxml       don't run tests but load test objects from xml file
  -rfb, --refill_buffers
                        use Fio's refill buffers option to circumvent any
                        compression of devices
  -dsc DESC_FILE, --desc_file DESC_FILE
                        use a description file for the tested device if hdparm
                        doesn't work correctly
  -c CONFIG, --config CONFIG
                        specify the config file for a raid device
  -ft, --force_test     skip checks if the used device is mounted, don't print
                        warnings and force starting the test
  -fm FEATURE_MATRIX, --feature_matrix FEATURE_MATRIX
                        add a feature matrix of the given device to the report
  -hddt {iops,tp}, --hdd_type {iops,tp}
                        choose which tests are run
  -ssdt {iops,lat,tp,writesat}, --ssd_type {iops,lat,tp,writesat}
                        choose which tests are run
  -m MAIL, --mail MAIL  Send reports or errors to mail address, needs -s to be
                        set
  -s SMTP, --smtp SMTP  Use the specified smtp server to send mails, uses port
                        25 to connect
  -g GEN_REPORT, --gen_report GEN_REPORT
                        Set and specify command to generate pdf report, e.g.
                        rst2pdf
```

### tkperf-cmp
```
$ tkperf-cmp -h
usage: tkperf-cmp [-h] [-v] [-d] [-q] [-f FOLDER] [-z]
                  {hdd,ssd,raid} xmls [xmls ...]

positional arguments:
  {hdd,ssd,raid}        specify the test mode for the device
  xmls                  XML files to read from

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         get the version information
  -d, --debug           get detailed debug information
  -q, --quiet           turn off logging of info messages
  -f FOLDER, --folder FOLDER
                        store compare plots in a subfolder, specify name of
                        folder
  -z, --zip             store compare plots in a zip archive, requires '-f' as
                        zip is created from subfolder
```

## Copyright (C) 2015-2018 Thomas-Krenn.AG
This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, see <http://www.gnu.org/licenses/>.
