import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  vus: 50,
  duration: __ENV.DURATION || '24h',
  thresholds: {
    'http_req_failed': ['rate<0.01'],
  },
};

const BASE = __ENV.BASE_URL || 'https://opensky-network.org/';
const pages = ['/', '/feed', '/data', '/about', '/account'];

export default function () {
  let p = pages[Math.floor(Math.random() * pages.length)];
  http.get(BASE + p);
  sleep(Math.random() * 60 + 30);
}
