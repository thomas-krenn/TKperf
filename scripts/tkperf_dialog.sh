#!/bin/bash
if [ "$(whoami)" != "root" ]
then
	echo "Insufficient privileges, call with sudo!"
	exit 1
fi

pyStartScript="tkperf"

echo "Test name:"
read testName

echo "Test device (e.g. /dev/sdc):"
read testDevice

#Check if the given device is mounted, this is dangerous
if mount -l |grep $testDevice
then
	echo "Your device is mounted, don't expect to use it"
	exit 1 
fi
#Check if the device is valid
if ! lsblk | grep -q ${testDevice:5}
then
	echo "Could not find your device with lsblk, check the path"
	exit 1
fi

select testMode in ssd hdd
do
	break
done

numJobs=2
ioDepth=16
echo "Change num jobs (enter to skip):"
read nj
if [ "$nj" != '' ]
then
	numJobs = $nj
fi
echo "Change io depth (enter to skip):"
read iod
if [ "$iod" != '' ]
then
	ioDepth = $iod
fi

extraParams="-rfb"
echo "Use refill buffers (default yes) yes/no":
read rfb
if [ "$rfb" == 'no' ]
then
	extraParams=''
fi

echo "Configuration:"
echo "----------------"
echo "Test name: $testName"
echo "Test device: $testDevice"
echo "Test mode $testMode"
echo "Num jobs: $numJobs"
echo "IO depth: $ioDepth"
echo "Add. parameters: $extraParams"
echo "----------------"
echo "Configuration Correct? yes/no"
read configOK
if [ "$configOK" != 'yes' ]
then
	echo "Exiting as config is not OK"
	exit 1
fi
echo "Attention, all data on $testDevice will be lost!!! yes/no"
read dataOK
if [ "$dataOK" != 'yes' ]
then
	echo "Exiting as data loss is not OK"
	exit 1
fi

echo "The following command starts the test:"
echo "----------------"
startCommand="python $pyStartScript $testMode $testName $testDevice -ft -nj=$numJobs -iod=$ioDepth $extraParams"
echo $startCommand
echo "----------------"
echo "Ready to start? yes/no":
read startOK
if [ "$startOK" != 'yes' ]
then
	echo "Exiting as command is not OK"
	exit 1
fi

#start test
$startCommand
if [ "$?" -ne "0" ]
then
	echo "Performance test returned an error code!"
	exit 1
fi

echo "Please check $testName.log if test is running!"


