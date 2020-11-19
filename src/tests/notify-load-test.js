import http from 'k6/http';
import { check, sleep } from 'k6';

export default function() {
  var url = 'http://192.0.0.1:8668/v2/notify';
  const before = new Date().getTime();
  const T = 30; // time needed to complete a VU iteration


  for (var i = 0; i < 100; i++){
      var data = {
                "id": "Room:1",
                "type": "Room",
                "temperature": {
                        "value": 23.3,
                        "type": "Number"
                },
                "pressure": {
                        "value": 720,
                        "type": "Integer"
                    }
                }
      var array = [];
      array.push(data);

      var payload = {
        "data" : array
      }
      var payload = JSON.stringify(payload);

      var params = {
        headers: {
          'Content-Type': 'application/json',
        }
      };
      let res = http.post(url, payload, params);
      check(res, { 'status was 200': r => r.status == 200 });
  }
  const after = new Date().getTime();
  const diff = (after - before) / 1000;
  const remainder = T - diff;
  if (remainder > 0) {
    sleep(remainder);
  } else {
    console.warn(
      `Timer exhausted! The execution time of the test took longer than ${T} seconds`
    );
  }
}
