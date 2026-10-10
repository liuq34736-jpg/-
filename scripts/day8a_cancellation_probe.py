"""Real loopback HTTP disconnects + production proxy helper, test-only sleeper.

Uses an isolated instance of the actual ASGI app at ephemeral loopback ports;
does not replace the live services or change any frozen file. No AI/network.
"""

import argparse
import asyncio
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from threading import Thread
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROXY_JS = r'''
import { createServer, request } from 'node:http';
import { EventEmitter } from 'node:events';
import { pathToFileURL } from 'node:url';
const { attachPreviewCancellation } = await import(pathToFileURL(process.argv[1]).href);
const proxy = new EventEmitter();
attachPreviewCancellation(proxy);
const server = createServer((incoming, response) => {
  const outgoing = request({ hostname: '127.0.0.1', port: Number(process.argv[2]),
    path: incoming.url, method: incoming.method, headers: {'content-type':'application/json'} }, upstream => {
      response.writeHead(upstream.statusCode); upstream.pipe(response);
  });
  outgoing.on('error', () => { if (!response.destroyed) { response.writeHead(503); response.end('{}'); } });
  proxy.emit('proxyReq', outgoing, incoming, response);
  incoming.pipe(outgoing);
});
server.listen(0, '127.0.0.1', () => process.stdout.write(String(server.address().port) + '\n'));
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', type=Path, required=True)
    args = parser.parse_args()
    import uvicorn
    from backend.app.main import app, traditional_preview_service
    from backend.traditional_preview_v1.execution import ExecutionControl
    from backend.app.meihua_models import ManualInput
    real_popen, children = subprocess.Popen, []
    checks, observations = [], []
    def check(name, ok): checks.append({'name': name, 'passed': bool(ok)})
    def sleeper(*command, **options):
        child = real_popen([sys.executable, '-I', '-B', '-c', 'import time; time.sleep(30)'], **options)
        children.append(child)
        return child
    def slots_free():
        acquired = sum(traditional_preview_service._slots.acquire(False) for _ in range(2))
        for _ in range(acquired): traditional_preview_service._slots.release()
        return acquired == 2
    def until(predicate, seconds=3):
        until_time=time.monotonic()+seconds
        while not predicate() and time.monotonic()<until_time: time.sleep(.02)
        return predicate()
    request = ManualInput(input_mode='manual_hexagram',hexagram_id=20,moving_line=4,cast_at='2026-09-24T19:45:35+08:00')
    body=json.dumps(request.model_dump()).encode()
    server_socket=socket.socket();server_socket.bind(('127.0.0.1',0));server_socket.listen()
    backend_port=server_socket.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False,lifespan='off'))
    thread=Thread(target=lambda:asyncio.run(server.serve(sockets=[server_socket])),daemon=True)
    thread.start()
    proxy=None
    try:
        if not until(lambda:server.started):raise RuntimeError('isolated_server_unavailable')
        environment={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP'}}
        proxy=real_popen([str(args.node), '--experimental-strip-types', '--input-type=module', '-e', PROXY_JS,
            str(ROOT/'frontend/previewCancellation.ts'), str(backend_port)], stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env=environment,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        line=proxy.stdout.readline().decode().strip()
        if not line.isdecimal():raise RuntimeError('isolated_proxy_unavailable')
        proxy_port=int(line)
        with patch('backend.traditional_preview_v1.execution.subprocess.Popen',side_effect=sleeper):
            for name,port in [('direct_asgi_disconnect',backend_port),('shared_vite_proxy_disconnect',proxy_port)]:
                previous=len(children)
                connection=socket.create_connection(('127.0.0.1',port),timeout=3)
                connection.sendall((f'POST /api/v1/meihua/traditional-preview HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n').encode()+body)
                started=until(lambda:len(children)>previous)
                cancelled_at=time.monotonic();connection.close()
                reaped=until(lambda:started and children[-1].poll() is not None)
                released=until(slots_free)
                latency=round(time.monotonic()-cancelled_at,3)
                check(name,started and reaped and released and len(children)==previous+1 and latency<3)
                observations.append({'case':name,'owned_child_reaped':reaped,'two_slots_released':released,
                                     'child_starts':len(children)-previous,'cancel_to_release_seconds':latency})
            class ShortControl(ExecutionControl):
                def __init__(self):super().__init__(seconds=.2)
            previous=len(children)
            with patch('backend.traditional_preview_v1.execution.ExecutionControl',ShortControl):
                connection=http.client.HTTPConnection('127.0.0.1',proxy_port,timeout=4)
                started_at=time.monotonic()
                connection.request('POST','/api/v1/meihua/traditional-preview',body,{'Content-Type':'application/json'})
                response=connection.getresponse();text=response.read().decode();connection.close()
                check('server_deadline_504_reaped_no_retry',response.status==504 and '已超时并停止' in text
                      and len(children)==previous+1 and children[-1].poll() is not None and slots_free())
                observations.append({'case':'compressed_deadline_test_only','http_status':response.status,
                     'elapsed_seconds':round(time.monotonic()-started_at,3),'child_starts':len(children)-previous})
    finally:
        for child in children:
            if child.poll() is None:child.kill()
            child.wait()
        if proxy is not None:
            proxy.kill();proxy.communicate(timeout=3)
        server.should_exit=True;thread.join(timeout=5);server_socket.close()
    check('isolated_server_stopped',not thread.is_alive())
    result={'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),
        'observations':observations,'transport':'real_loopback_HTTP_ASGI_and_shared_Vite_cancellation_helper',
        'frozen_worker_substitute':'test_sleeper_only; no_calculations_or_corpus_modified',
        'live_ports_changed':False,'real_ai_calls':0}
    (ROOT/'docs/day8a_cancellation_probe_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
    return int(bool(result['failed']))


if __name__=='__main__':raise SystemExit(main())
