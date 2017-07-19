# Comet experiment

Assuming you are in the root of this project:

        
1. Activate the dev env

        source setup_dev_env.sh


2. Launch docker containers

        docker-compose -f experiments/comet/docker-compose.yml up -d
        
    If comet fails, try ```docker-compose -f experiments/comet/docker-compose.yml restart comet```


3. Open new terminal (T2) and repeat step 1.


4. Run sensor in T2

        python experiments/comet/crazy_sensor.py


5. Run reader (in T1)

        python experiments/comet/paranoid_reader.py

6. When you've finished run

        docker-compose -f experiments/comet/docker-compose.yml down
