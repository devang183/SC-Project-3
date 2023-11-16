if [ -z "$1" ]; then
    echo "Usage: $0 <server_name>"
    exit 1
fi

server_name="$1"

# nohup python3 -u central.py > central_output.log 2>&1 &   

nohup python3 -u server.py --name "$server_name" > server_output.log 2>&1 &

nohup python3 -u sensor_db.py --sensor temp --port 33701 > sensor_temp_33701.log 2>&1 &
nohup python3 -u sensor_db.py --sensor rain --port 33702 > sensor_rain_33702.log 2>&1 &
nohup python3 -u sensor_db.py --sensor dist_front --port 33703 > sensor_temp_33703.log 2>&1 &
nohup python3 -u sensor_db.py --sensor dist_rear --port 33704 > sensor_temp_33704.log 2>&1 &
nohup python3 -u sensor_db.py --sensor dist_left --port 33705 > sensor_temp_33705.log 2>&1 &
nohup python3 -u sensor_db.py --sensor dist_right --port 33706 > sensor_temp_33706.log 2>&1 &
nohup python3 -u sensor_db.py --sensor light --port 33707 > sensor_temp_33707.log 2>&1 &
nohup python3 -u sensor_db.py --sensor wind --port 33708 > sensor_temp_33708.log 2>&1 &
nohup python3 -u sensor_db.py --sensor speed --port 33709 > sensor_temp_33709.log 2>&1 &
nohup python3 -u sensor_db.py --sensor fuel --port 33710 > sensor_temp_33710.log 2>&1 &
nohup python3 -u sensor_db.py --sensor RPM --port 33711 > sensor_temp_33711.log 2>&1 &
nohup python3 -u sensor_db.py --sensor inttemp --port 33712 > sensor_temp_33712.log 2>&1 &


nohup python3 -u device.py --interest Light_Sensor --name dev1 --data Wind_Sensor Rainfall Ultrasonic_Distance_Sensor_Left --duration 0.1 > dev1.log 2>&1 &
nohup python3 -u device.py --interest Light_Sensor --name dev2 --data Internal_temp Temperature --duration 0.1 > dev2.log 2>&1 &
nohup python3 -u device.py --interest Light_Sensor --name dev3 --data Fuel Wind_Sensor --duration 0.1 > dev3.log 2>&1 &
nohup python3 -u device.py --interest Light_Sensor --name dev4 --data Rainfall Light_Sensor Wind_Sensor --duration 0.1 > dev4.log 2>&1 &
nohup python3 -u device.py --interest Light_Sensor --name dev5 --data Revs_per_min Internal_temp --duration 0.1 > dev5.log 2>&1 &
