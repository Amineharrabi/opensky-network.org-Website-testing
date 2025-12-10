import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 500 },
    { duration: '10m', target: 500 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    'http_req_duration{static:0}': ['p(95)<2000'],
    'http_req_failed': ['rate<0.001'],
  },
};

const BASE = __ENV.BASE_URL || 'https://opensky-network.org/';

export default function () {
  let res = http.get(BASE);
  check(res, {
    'status 200': (r) => r.status === 200,
  });
  sleep(Math.random() * 3 + 2);
}
