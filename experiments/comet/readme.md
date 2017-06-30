# Comet experiment

Assuming you are in the root of this project:

        
1. Activate the venv

        source env/bin/activate
    
2. Make sure to have this project in PYTHONPATH

        export PYTHONPATH=$PWD:$PYTHONPATH 

3. Move to experiment folder

        cd experiments/comet
        
4. Launch docker containers

        docker-compose up -d
        
    If comet fails, try ```docker-compose restart comet```

5. Open new terminal (T2) and repeat steps 1, 2 and 3.


6. Run sensor in T2

        python crazy_sensor.py
        
7. Run reader (in T1)

        python paranoid_reader.py
