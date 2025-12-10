import http from 'k6/http';
import { check } from 'k6';

export let options = {
  scenarios: {
    downloads: {
      executor: 'constant-vus',
      vus: 200,
      duration: '3m',
      exec: 'download',
    },
  },
  thresholds: {
    'http_req_failed': ['rate==0'],
  },
};

const FILE = __ENV.FILE_URL || 'https://opensky-network.org/files/firmware/opensky-feeder_latest_armhf.deb';

export function download() {
  let r = http.get(FILE, { timeout: '120s' });
  check(r, { 'status 200': (r) => r.status === 200 });
  // reading body to ensure download completes; may discard content
  r.body;
}
