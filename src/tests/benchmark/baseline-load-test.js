import http from 'k6/http';
import { check, sleep } from 'k6';

export default function() {
  var url = 'http://192.0.0.1:8668/version';
  const before = new Date().getTime();
  const T = 30; // time needed to complete a VU iteration


  for (var i = 0; i < 100; i++){
      let res = http.get(url);
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
