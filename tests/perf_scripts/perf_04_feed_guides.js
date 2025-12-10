import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
  vus: 300,
  duration: '10m',
  thresholds: {
    'http_req_duration': ['p(99)<4000'],
    'http_req_failed': ['rate==0'],
  },
};

const pages = [
  '/feed',
  '/feed/raspberry',
  '/feed/debian',
  '/feed/docker',
];

const BASE = __ENV.BASE_URL || 'https://opensky-network.org';

export default function () {
  let p = pages[Math.floor(Math.random() * pages.length)];
  let res = http.get(`${BASE}${p}`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(Math.random() * 30 + 15);
}
