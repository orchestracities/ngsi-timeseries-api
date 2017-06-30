# Grafana experiment

Assuming you are in the root of this project:

        
1. Activate the venv

        source env/bin/activate
    
2. Make sure to have this project in PYTHONPATH

        export PYTHONPATH=$PWD:$PYTHONPATH 

3. Move to experiment folder

        cd experiments/grafana
        
4. Launch docker containers

        docker-compose up -d
        

5. If you want to test Cratedb + Grafana

        python crate_feeder.py
        
6. If you want to test QuantumLeap + Crate + Grafana

        python ql_feeder.py

Manage Cratedb cluster at [http://0.0.0.0:4200](http://0.0.0.0:4200).

Manage Grafana at [http://0.0.0.0:3000](http://0.0.0.0:3000) (user = pass = admin)
