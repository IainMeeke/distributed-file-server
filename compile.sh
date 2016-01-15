#!/bin/sh


echo "[starting_port] [no_servers] [no_copies]"
read port no_servers no_copies
echo "Create Directory"
echo $port $no_servers #$no_copies
new_port=$((port))
new_port=$((new_port+1))
python DirectoryService.py $port $new_port & #$no_servers $no_copies &

python locking_server.py $port &

for ((i=1;i<=no_servers;i++));
do
	echo "Create replication"
	new_port=$((new_port+1))
	python FileServer.py $new_port & #$no_copies $lock_server_port &
#	for ((j=1;j<=no_copies;j++));
#	do
#		echo "Create file server"
#		new_port=$((new_port+1))
#		python server_file.py $new_port &
#	done
done