import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '10s', target: 1000 },
    { duration: '30s', target: 1000 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2800'],
    'http_req_failed': ['rate<0.005'],
  },
};

const BASE = __ENV.MAP_URL || 'https://map.opensky-network.org/';

export default function () {
  let res = http.get(BASE);
  check(res, { 'status 200': (r) => r.status === 200 });
}
