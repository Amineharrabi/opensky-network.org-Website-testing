import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 50,
  duration: '30m',
  thresholds: {
    'http_req_duration': ['p(99)<800'],
  },
};

const RSS = __ENV.RSS_URL || 'https://opensky-network.org/feed';

export default function () {
  let res = http.get(RSS);
  check(res, { 'status 200': (r) => r.status === 200 });
}
