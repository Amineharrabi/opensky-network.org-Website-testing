import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 100,
  duration: '2m',
  thresholds: {
    'http_req_duration': ['p(95)<1200'],
  },
};

const BASE = __ENV.BASE_URL || 'https://opensky-network.org/';

export default function () {
  let res = http.get(BASE);
  check(res, { 'status 200': (r) => r.status === 200 });
}
