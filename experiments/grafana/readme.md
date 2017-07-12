# Grafana experiment

Assuming you are in the root of this project:

        
1. Activate dev environment

        source setup_dev_env.sh
    
2. Move to experiment folder

        cd experiments/grafana
        
3. Launch docker containers

        docker-compose up -d

4. If you want to test Cratedb + Grafana

        python crate_feeder.py
        
    But, if you want to test QuantumLeap + Cratedb + Grafana

        python ql_feeder.py

5. When you've finished, remember to run

        docker-compose down

Manage Cratedb cluster at [http://0.0.0.0:4200](http://0.0.0.0:4200).

Manage Grafana at [http://0.0.0.0:3000](http://0.0.0.0:3000) (user = pass = admin)
